# -*- coding: utf-8 -*-
"""
Antigravity Mac 一键汉化工具 v1.0
=================================
支持环境：
  - macOS (Apple Silicon M系列 / Intel)
  - Antigravity 主程序 (v2.x Electron 架构)
  - Antigravity IDE 编辑器 (VS Code 定制版)

功能特性：
  - 双端全量深度汉化 (18845+ 词条动态拦截与原生菜单翻译)
  - macOS Hardened Runtime 本地 Ad-Hoc 签名与隔离属性清洗 (彻底根治闪退/报错)
  - 官方原版字节级自动备份 (永不降级)
  - 零联网、零上报、一键秒级还原官方英文
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import hashlib
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(SCRIPT_DIR, "engine.js")
DATA_PATH = os.path.join(SCRIPT_DIR, "zh_data.json")

# 默认安装路径识别
APP_CANDIDATES = [
    "/Applications/Antigravity.app",
    os.path.expanduser("~/Applications/Antigravity.app")
]
IDE_CANDIDATES = [
    "/Applications/Antigravity IDE.app",
    os.path.expanduser("~/Applications/Antigravity IDE.app")
]

ENGINE_START = "// ===== [AGY_ZH_ENGINE_START] Antigravity 一键汉化引擎 ====="
ENGINE_END = "// ===== [AGY_ZH_ENGINE_END] ====="
MENU_START = "// ===== [AGY_ZH_MENU_START] 原生菜单翻译 ====="
MENU_END = "// ===== [AGY_ZH_MENU_END] ====="
TRAY_START = "// ===== [AGY_ZH_TRAY_START] 托盘菜单翻译 ====="
TRAY_END = "// ===== [AGY_ZH_TRAY_END] ====="

def log(msg, ok=False, warn=False):
    tag = "\033[32m[✓]\033[0m" if ok else ("\033[33m[!]\033[0m" if warn else "\033[36m[·]\033[0m")
    print(f"{tag} {msg}", flush=True)

def die(msg):
    print(f"\033[31m[✗] {msg}\033[0m", flush=True)
    sys.exit(1)

def find_app_path():
    for p in APP_CANDIDATES:
        if os.path.exists(os.path.join(p, "Contents", "Resources", "app.asar")):
            return p
    return None

def find_ide_path():
    for p in IDE_CANDIDATES:
        if os.path.exists(os.path.join(p, "Contents", "Resources", "app")):
            return p
    return None

def check_env():
    node = shutil.which("node")
    npx = shutil.which("npx")
    if not node or not npx:
        die("未检测到 Node.js 环境（需要 node 和 npx 命令）。\n"
            "  请先安装 Node.js (推荐通过 Homebrew: brew install node 或官网 https://nodejs.org)")
    return npx

def strip_block(content, start_marker, end_marker):
    if start_marker not in content:
        return content
    s = content.index(start_marker)
    e = content.find(end_marker, s)
    if e == -1:
        return content[:s]
    e += len(end_marker)
    while e < len(content) and content[e] in "\r\n":
        e += 1
    return content[:s] + content[e:]

def build_menu_block(data):
    menu_map = data.get("menuMap", {})
    return (f"\n{MENU_START}\n"
            f"const __AGY_ZH_MENU_MAP__ = {json.dumps(menu_map, ensure_ascii=False)};\n"
            f"function __AGY_ZH_MENU_TRANSLATE__(mi) {{\n"
            f"    if (mi && mi.label && __AGY_ZH_MENU_MAP__[mi.label]) mi.label = __AGY_ZH_MENU_MAP__[mi.label];\n"
            f"    if (mi && mi.submenu) {{\n"
            f"        if (mi.submenu.items) mi.submenu.items.forEach(__AGY_ZH_MENU_TRANSLATE__);\n"
            f"        else if (Array.isArray(mi.submenu)) mi.submenu.forEach(__AGY_ZH_MENU_TRANSLATE__);\n"
            f"    }}\n"
            f"}}\n"
            f"{MENU_END}\n")

def build_tray_block():
    return (f"\n{TRAY_START}\n"
            f"function __AGY_ZH_TRAY_ACTIONS__(actions) {{\n"
            f"    const M = {{ 'No agents running': '没有智能体在运行', 'Quit': '退出', 'Open Antigravity': '打开 Antigravity' }};\n"
            f"    return actions.map(a => {{\n"
            f"        if (a && a.label) {{\n"
            f"            if (M[a.label]) a.label = M[a.label];\n"
            f"            else if (/^Open /.test(a.label)) a.label = '打开 Antigravity';\n"
            f"        }}\n"
            f"        return a;\n"
            f"    }});\n"
            f"}}\n"
            f"{TRAY_END}\n")

def menu_hook_pairs():
    set_hooked = ("{ if (typeof __AGY_ZH_MENU_TRANSLATE__ === 'function') "
                  "{ try { menu.items.forEach(__AGY_ZH_MENU_TRANSLATE__); } catch (e) {} } "
                  "electron_1.Menu.setApplicationMenu(menu); }")
    set_orig = "electron_1.Menu.setApplicationMenu(menu);"
    find_hooked = ("const submenuItem = appMenu.items.find((item) => item.label === submenuLabel || "
                   "(typeof __AGY_ZH_MENU_MAP__ !== 'undefined' && item.label === __AGY_ZH_MENU_MAP__[submenuLabel]));")
    find_orig = "const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);"
    tray_hooked = "electron_1.Menu.buildFromTemplate(__AGY_ZH_TRAY_ACTIONS__(actions));"
    tray_orig = "electron_1.Menu.buildFromTemplate(actions);"
    return [(set_hooked, set_orig), (find_hooked, find_orig), (tray_hooked, tray_orig)]

def inject_engine(content, engine_code):
    c = strip_block(content, ENGINE_START, ENGINE_END)
    block = f"\n{ENGINE_START}\n{engine_code}\n{ENGINE_END}\n"
    return c.rstrip("\n") + "\n" + block

def codesign_bundle(bundle_path):
    log(f"为 {os.path.basename(bundle_path)} 重新生成本地安全签名 (Ad-Hoc)...")
    try:
        subprocess.run(["xattr", "-cr", bundle_path], check=False)
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", bundle_path], check=True, capture_output=True)
        log("签名完成，运行保护检查已通过", ok=True)
    except Exception as e:
        log(f"签名警告 (可能需要管理员权限): {e}", warn=True)

def get_sha256_base64(path):
    with open(path, 'rb') as f:
        data = f.read()
    return base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8').rstrip('=')

def localize_app(npx, app_path, engine_final, data):
    log(f"--- 开始汉化 Antigravity 主程序: {app_path} ---")
    resources_dir = os.path.join(app_path, "Contents", "Resources")
    asar_path = os.path.join(resources_dir, "app.asar")
    bak_path = os.path.join(resources_dir, "app.asar.bak")

    # 1. 备份原版
    if not os.path.exists(bak_path):
        log(f"备份官方原版 app.asar -> {bak_path}")
        shutil.copy2(asar_path, bak_path)
        log("原版备份已安全保存", ok=True)
    else:
        log("官方原版备份已存在，保留当前备份", ok=True)

    # 2. 解包
    work_dir = tempfile.mkdtemp(prefix="agy_mac_")
    extract_dir = os.path.join(work_dir, "x")
    work_asar = os.path.join(work_dir, "app.asar")
    shutil.copy2(bak_path, work_asar)
    unpacked_orig = os.path.join(resources_dir, "app.asar.unpacked")
    if os.path.exists(unpacked_orig):
        try:
            os.symlink(unpacked_orig, os.path.join(work_dir, "app.asar.unpacked"))
        except Exception:
            pass
    log("正在解包官方原版 app.asar ...")
    subprocess.run([npx, "--yes", "@electron/asar", "extract", work_asar, extract_dir], check=True, capture_output=True)

    # 3. 注入
    # dist/preload.js
    p = os.path.join(extract_dir, "dist", "preload.js")
    if os.path.exists(p):
        orig_content = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(inject_engine(orig_content, engine_final))
        log("已注入 dist/preload.js 核心翻译引擎", ok=True)

    # dist/ideInstall/wizardPreload.js
    p = os.path.join(extract_dir, "dist", "ideInstall", "wizardPreload.js")
    if os.path.exists(p):
        orig_content = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(inject_engine(orig_content, engine_final))
        log("已注入安装向导翻译", ok=True)

    # dist/menu.js
    p = os.path.join(extract_dir, "dist", "menu.js")
    if os.path.exists(p):
        c = open(p, encoding='utf-8').read()
        c = strip_block(c, MENU_START, MENU_END)
        for h, orig in menu_hook_pairs():
            if h in c: c = c.replace(h, orig)
        set_h, set_o = menu_hook_pairs()[0]
        if set_o in c: c = c.replace(set_o, set_h)
        find_h, find_o = menu_hook_pairs()[1]
        if find_o in c: c = c.replace(find_o, find_h)
        c = c.rstrip("\n") + "\n" + build_menu_block(data)
        open(p, 'w', encoding='utf-8').write(c)
        log("已注入原生菜单栏翻译", ok=True)

    # dist/tray.js
    p = os.path.join(extract_dir, "dist", "tray.js")
    if os.path.exists(p):
        c = open(p, encoding='utf-8').read()
        c = strip_block(c, TRAY_START, TRAY_END)
        tray_h, tray_o = menu_hook_pairs()[2]
        if tray_h in c: c = c.replace(tray_h, tray_o)
        if tray_o in c: c = c.replace(tray_o, tray_h)
        c = c.rstrip("\n") + "\n" + build_tray_block()
        open(p, 'w', encoding='utf-8').write(c)
        log("已注入系统托盘菜单翻译", ok=True)

    # staticPatches
    for rel, patches in data.get("staticPatches", {}).items():
        rel_norm = rel.replace("/", os.sep)
        if not rel_norm.startswith("dist" + os.sep):
            rel_norm = os.path.join("dist", rel_norm)
        p = os.path.join(extract_dir, rel_norm)
        if os.path.isfile(p):
            c = open(p, encoding='utf-8').read()
            changed = False
            for patch in patches:
                if patch["find"] in c:
                    c = c.replace(patch["find"], patch["replace"])
                    changed = True
            if changed:
                open(p, 'w', encoding='utf-8').write(c)

    # 4. 重新打包
    temp_asar = os.path.join(work_dir, "app.asar.new")
    log("正在重新封装打包 app.asar ...")
    subprocess.run([npx, "--yes", "@electron/asar", "pack", extract_dir, temp_asar,
                    "--unpack-dir", "node_modules/chrome-devtools-mcp"], check=True, capture_output=True)

    # 5. 原子替换
    shutil.copy2(temp_asar, asar_path)
    log("成功部署汉化版 app.asar", ok=True)

    # 6. 代码签名与清理
    codesign_bundle(app_path)
    shutil.rmtree(work_dir, ignore_errors=True)
    log("Antigravity 主程序汉化成功！", ok=True)

def localize_ide(ide_path, engine_final):
    log(f"--- 开始汉化 Antigravity IDE 编辑器: {ide_path} ---")
    workbench_dir = os.path.join(ide_path, "Contents", "Resources", "app", "out", "vs", "code", "electron-browser", "workbench")
    wb_js = os.path.join(workbench_dir, "workbench.js")
    wb_bak = os.path.join(workbench_dir, "workbench.js.bak")
    jetski_js = os.path.join(workbench_dir, "jetskiAgent.js")
    jetski_bak = os.path.join(workbench_dir, "jetskiAgent.js.bak")

    if not os.path.exists(wb_js):
        log("未找到 IDE workbench.js，跳过", warn=True)
        return

    # 1. 备份原版
    if not os.path.exists(wb_bak):
        shutil.copy2(wb_js, wb_bak)
        log("已备份官方原版 workbench.js", ok=True)
    if os.path.exists(jetski_js) and not os.path.exists(jetski_bak):
        shutil.copy2(jetski_js, jetski_bak)
        log("已备份官方原版 jetskiAgent.js", ok=True)

    # 2. 注入
    open(wb_js, 'w', encoding='utf-8').write(inject_engine(open(wb_bak, encoding='utf-8').read(), engine_final))
    log("已注入 IDE workbench.js 界面翻译", ok=True)

    if os.path.exists(jetski_js):
        open(jetski_js, 'w', encoding='utf-8').write(inject_engine(open(jetski_bak, encoding='utf-8').read(), engine_final))
        log("已注入 IDE jetskiAgent.js (Agent智能体面板)", ok=True)

    # 3. 重新签名
    codesign_bundle(ide_path)
    log("Antigravity IDE 汉化成功！", ok=True)

def restore_all(app_path, ide_path):
    print("\n正在恢复官方原版...")
    if app_path:
        res = os.path.join(app_path, "Contents", "Resources")
        asar = os.path.join(res, "app.asar")
        bak = os.path.join(res, "app.asar.bak")
        if os.path.exists(bak):
            shutil.copy2(bak, asar)
            codesign_bundle(app_path)
            log("Antigravity 主程序已恢复官方英文原版", ok=True)
        else:
            log("未找到主程序备份文件 app.asar.bak", warn=True)

    if ide_path:
        wb_dir = os.path.join(ide_path, "Contents", "Resources", "app", "out", "vs", "code", "electron-browser", "workbench")
        wb = os.path.join(wb_dir, "workbench.js")
        wb_bak = os.path.join(wb_dir, "workbench.js.bak")
        jk = os.path.join(wb_dir, "jetskiAgent.js")
        jk_bak = os.path.join(wb_dir, "jetskiAgent.js.bak")
        restored = False
        if os.path.exists(wb_bak):
            shutil.copy2(wb_bak, wb)
            restored = True
        if os.path.exists(jk_bak):
            shutil.copy2(jk_bak, jk)
            restored = True
        if restored:
            codesign_bundle(ide_path)
            log("Antigravity IDE 已恢复官方英文原版", ok=True)
        else:
            log("未找到 IDE 备份文件", warn=True)

def main():
    print("=" * 64)
    print("      Antigravity Mac 一键汉化工具 v1.0")
    print("  支持 Antigravity 主程序 + Antigravity IDE 编辑器")
    print("=" * 64)

    app_path = find_app_path()
    ide_path = find_ide_path()

    print(f"检测到主程序: {app_path or '未找到'}")
    print(f"检测到IDE程序: {ide_path or '未找到'}")
    print("-" * 64)

    if not app_path and not ide_path:
        die("未在 /Applications 或 ~/Applications 下检测到任何 Antigravity 软件！")

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
    else:
        print("  [1] 一键双端汉化 (推荐：主程序与IDE同时汉化)")
        print("  [2] 仅汉化 Antigravity 主程序")
        print("  [3] 仅汉化 Antigravity IDE 编辑器")
        print("  [4] 恢复官方英文原版")
        print("  [0] 退出")
        print("-" * 64)
        cmd = input("请选择操作 [0-4]: ").strip()

    if cmd in ("0", "q", "quit"):
        return

    if cmd in ("4", "restore", "-r"):
        restore_all(app_path, ide_path)
        print("\n恢复完成！请按 Cmd+Q 重启软件。")
        return

    npx = check_env()

    if not os.path.exists(ENGINE_PATH) or not os.path.exists(DATA_PATH):
        die("缺少 engine.js 或 zh_data.json 词典文件！")

    engine_code = open(ENGINE_PATH, encoding='utf-8').read()
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    data_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    engine_final = engine_code.replace("/*__AGY_ZH_DATA__*/ {}", "__AGY_ZH_DATA__JSON__").replace("__AGY_ZH_DATA__JSON__", data_json)

    log(f"已加载词典：{len(data.get('exact', {}))} 条精确匹配，{len(data.get('menuMap', {}))} 条菜单映射", ok=True)

    if cmd in ("1", "all"):
        if app_path: localize_app(npx, app_path, engine_final, data)
        if ide_path: localize_ide(ide_path, engine_final)
    elif cmd in ("2", "app"):
        if app_path: localize_app(npx, app_path, engine_final, data)
    elif cmd in ("3", "ide"):
        if ide_path: localize_ide(ide_path, engine_final)
    else:
        print("无效选项，退出。")
        return

    print("=" * 64)
    log("汉化完成！请选中运行中的软件，按 Cmd+Q 彻底退出后再重新打开即可享受全中文！", ok=True)
    print("=" * 64)

if __name__ == "__main__":
    main()
