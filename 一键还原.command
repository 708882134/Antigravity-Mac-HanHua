#!/bin/bash
cd "$(dirname "$0")"
python3 localize.py 4
echo ""
read -p "按回车键退出..."
