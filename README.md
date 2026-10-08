# 🍏 Antigravity Mac 一键汉化工具

<p align="center">
  <img src="https://img.shields.io/badge/Platform-macOS%20(Apple%20Silicon%20%7C%20Intel)-black?style=flat-square&logo=apple" alt="Platform" />
  <img src="https://img.shields.io/badge/Antigravity-v2.x-blue?style=flat-square" alt="Antigravity" />
  <img src="https://img.shields.io/badge/Antigravity%20IDE-v2.x-green?style=flat-square" alt="IDE" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License" />
</p>

> **专为 macOS 设计的 Google Antigravity & Antigravity IDE 双端一键全量汉化套件。**  
> 18,800+ 翻译单元 · 自动处理 macOS Ad-Hoc 签名防闪退 · 零联网 · 一键还原 · Finder 双击即用！

---

## ✨ 核心特性

- 🎯 **双端全量覆盖**：全网首发同时深度适配 **Antigravity 主程序**（调度器/管理中心）与 **Antigravity IDE**（专属代码编辑器/Agent侧边栏）；
- 🍎 **macOS 深度排雷**：打包后全自动进行 **本地 Ad-Hoc 签名与隔离属性清洗**，彻底根治 macOS Hardened Runtime 导致的“应用已损坏，无法打开”或闪退崩溃；
- ⚡ **无感实时渲染**：基于底层微任务调度的 DOM 动态观察管道，**输入框、代码区、思考链物理隔离保护**，绝不破坏用户输入与推理生成；
- 🛡️ **无损备份与防降级**：汉化前自动备份官方原版，官方版本更新后重新汉化会自动升级备份，还原永不降级；
- 🖱️ **小白友好**：提供 Mac 专属 `.command` 脚本，在访达（Finder）中**双击即可运行**，无需手动敲命令行。

---

## 🚀 快速上手

### 环境准备
- macOS 12+ (支持 M1/M2/M3/M4 系列及 Intel 机型)
- 已安装 [Node.js](https://nodejs.org/)（需包含 `node` 与 `npx` 命令，解包/打包 asar 依赖）
- 已安装 [Python 3.8+](https://www.python.org/)

### 使用步骤

#### 方法一：双击运行（推荐）
1. [下载本仓库 Zip 压缩包](https://github.com/) 并解压到本地任意目录；
2. 在访达（Finder）中直接双击 **`一键汉化.command`**；
3. 按照提示输入数字 `1`，等待约 10~30 秒提示完成；
4. **完全退出软件**（在运行中的应用窗口按键盘 **`Cmd + Q`**），重新启动即可！

#### 方法二：终端命令行运行
```bash
git clone https://github.com/your-username/Antigravity-Mac-HanHua.git
cd Antigravity-Mac-HanHua

# 运行交互菜单
python3 localize.py

# 或直接一键双端汉化
python3 localize.py 1
```

---

## ❓ 常见问题 (FAQ)

### 1. 汉化后重新打开，为什么界面依然是英文？
> **原因**：在 macOS 上，点击窗口左上角的红叉“×”**并不是退出程序**，进程仍挂在后台内存中读取旧资源。  
> **解决办法**：请在软件窗口内按键盘快捷键 **`Cmd + Q`**（或菜单栏点击 `Quit` 彻底退出），再重新打开即可！

### 2. IDE 为什么提示“Antigravity IDE 安装似乎损坏。请重新安装”？
> **原因**：这是微软 VS Code 底座的内置文件哈希自检机制。由于我们注入了中文渲染引擎，VS Code 启动时检测到核心文件变更就会弹窗提醒。  
> **解决办法**：软件本身没有任何损坏，直接点击弹窗下方的 **【不再显示】** 按钮即可，以后再也不会打扰你！

### 3. 为什么 IDE 重启后账号显示掉登录了？
> **原因**：macOS 钥匙串（Keychain）的安全机制非常严苛。由于汉化后重新生成了本地 Ad-Hoc 签名，钥匙串为防止木马冒用旧证书凭证，会主动锁死旧凭证。  
> **解决办法**：直接点击右上角 **【登录 ->】** 重新在浏览器授权一次即可，之后就会永久绑定到新签名，稳定不掉。

### 4. 官方大版本更新后怎么办？
> Antigravity 官方更新后会覆盖资源变回英文。只需再次双击 **`一键汉化.command`** 重新汉化一次即可，备份会自动刷新为新版官方原版。

### 5. 如何恢复官方英文原版？
> 在访达中双击 **`一键还原.command`**，或运行 `python3 localize.py 4`，即可字节级无损恢复到官方原版。

---

## 📄 开源许可

本项目采用 [MIT 许可证](LICENSE)。仅供个人学习与研究使用。
