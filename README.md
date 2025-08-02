# 网站SSL证书有效期检测

自动检测多个域名的 SSL 证书有效期，并在证书即将过期时通过 Bark 推送通知。支持 GitHub Actions 定时运行。

### **项目结构 **

`domains.txt` 文件已被移除。

```
.
├── .github
│   └── workflows
│       └── check.yml        # GitHub Actions 配置文件
├── check_ssl.py             # 核心检测和通知脚本 
├── requirements.txt         # Python 依赖库
└── README.md                # 项目说明文件 
```

---

### **文件内容**

#### **1. `check_ssl.py`**

此脚本现在从环境变量读取 Bark 地址和域名列表。

```python
import ssl
import socket
import datetime
import os
import requests

# --- 配置 ---
# 从环境变量获取所有配置
BARK_KEY = os.environ.get('BARK_KEY')
# 自建 Bark 服务器地址，如果未设置，则默认为官方服务器
BARK_URL = os.environ.get('BARK_URL', 'https://api.day.app').rstrip('/')
# 从环境变量获取以逗号分隔的域名字符串
DOMAINS_STR = os.environ.get('DOMAINS')
# 证书过期提醒阈值（天）
DAYS_THRESHOLD = int(os.environ.get('DAYS_THRESHOLD', 30))


def get_cert_expiry_date(hostname: str) -> datetime.datetime | None:
    """获取指定域名的 SSL 证书过期日期"""
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date_str = cert['notAfter']
                return datetime.datetime.strptime(expiry_date_str, '%b %d %H:%M:%S %Y %Z')
    except (socket.gaierror, socket.timeout, ssl.SSLError, ConnectionRefusedError) as e:
        print(f"❌ 无法连接到 {hostname}: {e}")
        return None
    except Exception as e:
        print(f"❌ 检查 {hostname} 时发生未知错误: {e}")
        return None

def send_bark_notification(title: str, body: str, bark_key: str):
    """通过 Bark 发送推送通知"""
    if not bark_key:
        print("❗ 未配置 Bark Key，跳过通知。")
        return

    # 组合成最终的 Bark API URL
    url = f"{BARK_URL}/{bark_key}/{title}/{body}?icon=https://raw.githubusercontent.com/google/material-design-icons/master/png/action/https/materialicons/48dp/1x/baseline_https_black_48dp.png"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Bark 通知已成功发送: {title}")
        else:
            print(f"❗ Bark 通知发送失败 (URL: {BARK_URL})，状态码: {response.status_code}, 内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❗ Bark 通知发送时网络错误 (URL: {BARK_URL}): {e}")

def main():
    """主函数"""
    print("🚀 开始检测 SSL 证书有效期...")
    
    if not BARK_KEY:
        print("🔴 错误: 环境变量 BARK_KEY 未设置，将无法发送 Bark 通知。")
        # 如果没有key，脚本运行没有意义，可以直接退出
        return

    if not DOMAINS_STR:
        print("🔴 错误: 环境变量 DOMAINS 未设置或为空，没有可检测的域名。")
        return
        
    # 解析以逗号分隔的域名列表
    domains = [domain.strip() for domain in DOMAINS_STR.split(',') if domain.strip()]
    if not domains:
        print("🔴 错误: 从环境变量 DOMAINS 中未解析出有效域名。")
        return

    print(f"🔍 将检测以下 {len(domains)} 个域名 (从环境变量获取)，阈值为 {DAYS_THRESHOLD} 天:")
    for domain in domains:
        print(f"  - {domain}")
    
    print("-" * 20)

    expiring_soon_count = 0
    for domain in domains:
        expiry_date = get_cert_expiry_date(domain)
        if expiry_date:
            now = datetime.datetime.now()
            time_remaining = expiry_date - now
            days_left = time_remaining.days

            if days_left < 0:
                print(f"🔴 {domain} - 证书已过期 {abs(days_left)} 天！")
                title = f"SSL证书已过期⚠️"
                body = f"{domain} 的证书已于 {expiry_date.strftime('%Y-%m-%d')} 过期！"
                send_bark_notification(title, body, BARK_KEY)
                expiring_soon_count += 1
            elif days_left <= DAYS_THRESHOLD:
                print(f"🟠 {domain} - 证书将在 {days_left} 天后过期 (日期: {expiry_date.strftime('%Y-%m-%d')})")
                title = f"SSL证书即将过期提醒"
                body = f"{domain} 的证书将在 {days_left} 天后过期，请及时续签！"
                send_bark_notification(title, body, BARK_KEY)
                expiring_soon_count += 1
            else:
                print(f"🟢 {domain} - 正常，剩余 {days_left} 天。")
    
    print("-" * 20)
    if expiring_soon_count == 0:
        print("🎉 所有证书状态良好！")
        # 可以选择在一切正常时也发一条通知
        # send_bark_notification("SSL证书检测报告", f"所有 {len(domains)} 个证书均状态良好。", BARK_KEY)
    else:
        print(f"🚨 共发现 {expiring_soon_count} 个证书需要关注。")


if __name__ == "__main__":
    main()
```

---

#### **2. `.github/workflows/check.yml` **

`env` 部分现在包含了所有配置项。

```yaml
name: Check SSL Certificate Expiration

on:
  # 每天北京时间上午10点运行 (UTC 时间 2:00)
  schedule:
    - cron: '0 2 * * *'
  
  # 允许在 Actions 页面手动触发
  workflow_dispatch:

jobs:
  check-certs:
    runs-on: ubuntu-latest

    steps:
      # 步骤1: 检出你的代码
      - name: Checkout repository
        uses: actions/checkout@v4

      # 步骤2: 设置 Python 环境
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      # 步骤3: 安装依赖库
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # 步骤4: 运行检测脚本
      - name: Run SSL check script
        env:
          # --- 从 GitHub Secrets and Variables 读取配置 ---
          # 必填: 你的 Bark Key
          BARK_KEY: ${{ secrets.BARK_KEY }}
          # 必填: 逗号分隔的域名列表
          DOMAINS: ${{ secrets.DOMAINS }}
          # 选填: 你的自建 Bark 服务器地址
          BARK_URL: ${{ secrets.BARK_URL }}
          # 选填: 过期提醒阈值，默认为 30 天
          DAYS_THRESHOLD: ${{ vars.DAYS_THRESHOLD || 30 }}
        run: python check_ssl.py
```

---

#### **3. `requirements.txt` **

```
requests
```

---

#### **4. `README.md` **

说明文档已完全重写，以匹配新的、更简洁的配置流程。

````markdown
# SSL 证书有效期自动检测 & Bark 通知 

这是一个使用 Python 和 GitHub Actions 实现的简单项目，用于自动监控多个域名的 SSL 证书有效期，并在证书即将过期时通过 [Bark](https://github.com/Finb/Bark) 发送推送通知到你的 iOS 设备。

**此版本已升级，支持自建 Bark 服务器，并且所有配置均通过 GitHub Secrets 完成，无需修改任何代码文件。**

## ✨ 功能特性

- **环境变量配置**: 无需修改代码或配置文件，所有参数通过 GitHub Secrets 设置。
- **自建服务器支持**: 可轻松指定你自己的 Bark 服务器地址。
- **多域名支持**: 在环境变量中通过逗号分隔符提供域名列表。
- **自动化检测**: 利用 GitHub Actions 每日定时运行，无需人工干预。
- **即时通知**: 通过 Bark 推送证书过期预警，防止业务中断。
- **灵活配置**: 可自由设定证书过期的提醒阈值（默认为30天）。

## 🚀 部署与使用指南

### 步骤 1: Fork 本仓库

点击本页面右上角的 **Fork** 按钮，将此仓库复制到你自己的 GitHub 账户下。

### 步骤 2: 配置 GitHub Secrets

这是唯一的配置步骤，用于安全地存储你的所有敏感信息。

1.  在你的仓库页面，点击 **Settings** -> **Secrets and variables** -> **Actions**。
2.  在 **Repository secrets** 部分，点击 **New repository secret**，然后逐一添加以下 Secrets：

    *   **`BARK_KEY` (必填)**
        *   **Name**: `BARK_KEY`
        *   **Secret**: 填入你自己的 Bark 推送 Key (例如 `YourKey`)。

    *   **`DOMAINS` (必填)**
        *   **Name**: `DOMAINS`
        *   **Secret**: 填入**以逗号分隔**的域名列表。例如：`github.com,google.com,your-domain.com`

    *   **`BARK_URL` (选填)**
        *   **Name**: `BARK_URL`
        *   **Secret**: 填入你的自建 Bark 服务器地址。例如：`https://bark.your-server.com`。**如果留空或不创建此 Secret，脚本将自动使用官方服务器 `https://api.day.app`**。

### 步骤 3: (可选) 自定义过期提醒阈值

默认情况下，证书在剩余30天或更少时会发送通知。如果你想修改这个值：

1.  在 **Settings** -> **Secrets and variables** -> **Actions** 页面。
2.  切换到 **Variables** 标签页，点击 **New repository variable**。
3.  **Name**: `DAYS_THRESHOLD`
4.  **Value**: 填入你希望的天数，例如 `15`。
5.  点击 **Add variable** 保存。

### 步骤 4: 启用并测试 GitHub Actions

1.  在你的仓库页面，点击 **Actions** 标签页。
2.  如果看到一个黄色提示条，请点击按钮启用工作流。
3.  在左侧列表中，点击 **Check SSL Certificate Expiration**。
4.  点击右侧的 **Run workflow** 下拉菜单，然后点击绿色的 **Run workflow** 按钮，即可立即手动运行一次进行测试。
5.  点击正在运行的任务，可以查看实时日志输出。

配置完成！现在它会按照计划自动为你监控证书。

## 📝 本地运行

1.  克隆你的仓库: `git clone https://github.com/YourUsername/your-repo-name.git`
2.  进入目录: `cd your-repo-name`
3.  安装依赖: `pip install -r requirements.txt`
4.  设置环境变量并运行:
    ```bash
    # Linux / macOS
    export BARK_KEY="你的BarkKey"
    export DOMAINS="domain1.com,domain2.com"
    export BARK_URL="https://your-bark-server.com" # 如果使用自建服务器
    export DAYS_THRESHOLD="15" # 可选
    python check_ssl.py

    # Windows (CMD)
    set BARK_KEY="你的BarkKey"
    set DOMAINS="domain1.com,domain2.com"
    python check_ssl.py
    ```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 授权。
````
