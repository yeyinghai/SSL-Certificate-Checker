# 网站SSL证书有效期检测

自动检测多个域名的 SSL 证书有效期，并在证书即将过期时通过 Bark 推送通知。支持 GitHub Actions 定时运行。

### **项目结构 **

```
├── github
│   └── workflows
│       └── check.yml        # GitHub Actions 配置文件
├── check_ssl.py             # 核心检测和通知脚本 
├── requirements.txt         # Python 依赖库
└── README.md                # 项目说明文件 
```


# SSL 证书有效期自动检测 & Bark 通知 

这是一个使用 Python 和 GitHub Actions 实现的简单项目，用于自动监控多个域名的 SSL 证书有效期，并在证书即将过期时通过 [Bark](https://github.com/Finb/Bark) 发送推送通知到你的 iOS 设备。

**支持自建 Bark 服务器，并且所有配置均通过 GitHub Secrets 完成，无需修改任何代码文件。**

##  ✨ 功能特性

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

1.  克隆仓库: `git clone https://github.com/yeyinghai/SSL-Certificate-Checker.git`
2.  进入目录: `cd SSL-Certificate-Checker`
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
