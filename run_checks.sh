#!/bin/bash

# 获取脚本所在目录并切换到该目录，确保所有路径正确
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo "--- Starting SSL Certificate Check ---"
echo "Current directory: $(pwd)"

# 确保 config.example.ini 存在
if [ ! -f config.example.ini ]; then
    echo "错误: 找不到 config.example.ini 文件！"
    exit 1
fi

# 复制模板文件到 config.ini
cp config.example.ini config.ini

# 通过环境变量（GitHub Actions Secrets）注入 Bark 配置
# sed -i 跨平台兼容性更好，使用 gnu-sed 或 -i '' for BSD/macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS (BSD sed)
  sed -i '' "s|base_url = .*|base_url = ${BARK_BASE_URL:-http://bark.yourdomain.com}|" config.ini
  sed -i '' "s|device_key = .*|device_key = ${BARK_DEVICE_KEY:-your_device_key}|" config.ini
else
  # Linux (GNU sed)
  sed -i "s|base_url = .*|base_url = ${BARK_BASE_URL:-http://bark.yourdomain.com}|" config.ini
  sed -i "s|device_key = .*|device_key = ${BARK_DEVICE_KEY:-your_device_key}|" config.ini
fi

echo "Bark URL set to: ${BARK_BASE_URL:-http://bark.yourdomain.com}"
echo "Bark Device Key set (masked for security)"

# 处理 DOMAINS 环境变量，将其转换为 config.ini 可识别的多行格式
# DOMAINS 变量应为 example.com|google.com=443 格式
if [ -n "$DOMAINS" ]; then
    echo "Processing DOMAINS secret..."
    # 将竖线 | 替换为换行符，并为每一行添加前导空格以符合INI文件格式
    # 结果会是：
    #     example.com
    #     google.com = 443
    printf "%s\n" "$DOMAINS" | sed 's/|/\n    /g' | sed 's/^/    /' > domains_list_for_config.txt

    # 将生成的域名列表插入到 config.ini 中 'domains =' 这一行的后面
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "/domains =/r domains_list_for_config.txt" config.ini
    else
        sed -i "/domains =/r domains_list_for_config.txt" config.ini
    fi
    rm domains_list_for_config.txt # 清理临时文件
    echo "Domains loaded from secret."
else
    echo "No DOMAINS secret provided or it is empty. Using domains specified in config.ini (if any)."
fi

# 打印最终生成的 config.ini 内容 (仅用于调试，生产环境可注释)
# echo "--- Generated config.ini content ---"
# cat config.ini
# echo "------------------------------------"

# 运行 Python 脚本
python3 ssl_checker.py

echo "--- SSL Certificate Check Finished ---"
