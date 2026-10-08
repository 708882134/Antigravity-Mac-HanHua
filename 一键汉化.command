#!/bin/bash
cd "$(dirname "$0")"
python3 localize.py 1
echo ""
read -p "按回车键退出..."
