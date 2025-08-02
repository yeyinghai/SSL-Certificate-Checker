# 网站SSL证书有效期检测

自动检测多个域名的 SSL 证书有效期，并在证书即将过期时通过 Bark 推送通知。支持 GitHub Actions 定时运行。

## 功能
- 批量检测多个域名的 SSL 证书过期时间
- 通过自建 Bark 服务器推送通知
- GitHub Actions 每日自动运行
- 支持手动触发检查

## 安装与本地使用

1. 克隆仓库：
   git clone https://github.com/yeyinghai/ssl-cert-checker.git
   cd ssl-cert-checker

2. 安装依赖：
   bashDownloadCopy code Wrappip install -r requirements.txt

3. 配置 config.ini：

   * 复制 config.example.ini 为 config.ini
   * 修改 config.ini 中的 Bark 服务器地址、设备 Key 和目标网站列表（参照 config.example.ini 中的注释）

4. 运行检测：
   chmod +x run_checks.sh
   ./run_checks.sh	

# GitHub Actions 定时运行
推荐使用 GitHub Actions 实现自动化检测，无需自己的服务器即可运行。

1. 设置 GitHub Secrets:
在你的 GitHub 仓库中，进入 Settings -> Secrets and variables -> Actions。
添加以下仓库 Secrets：
BARK_BASE_URL: 你的 Bark 服务器地址（例如 https://bark.yourdomain.com）
BARK_DEVICE_KEY: 你的 Bark 设备 Key
DOMAINS: 需要检查的域名列表。使用竖线 | 分隔每个域名，并且可以指定端口。
例如：example.com|google.com=443|another.site.com=8443


2. 工作流程触发:

工作流程将每天 UTC 时间 0:00（北京时间 8:00）自动运行。
你也可以手动触发工作流程：
进入仓库的 Actions 标签页
选择 "SSL Certificate Checker" 工作流程
点击 "Run workflow" 按钮   

# 仓库结构
ssl-cert-checker/
│
├── .github/
│   └── workflows/
│       └── ssl_check.yml
├── README.md
├── requirements.txt
├── config.example.ini
├── ssl_checker.py
└── run_checks.sh