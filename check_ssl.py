import ssl
import socket
import datetime
import os
import requests

# --- 配置 ---
# 从环境变量获取所有配置
BARK_KEY = os.environ.get('BARK_KEY')
BARK_URL = os.environ.get('BARK_URL', 'https://api.day.app').rstrip('/')
DOMAINS_STR = os.environ.get('DOMAINS')
DAYS_THRESHOLD = int(os.environ.get('DAYS_THRESHOLD', 30))
DEFAULT_PORT = 443 # <--- 新增：定义默认端口

def get_cert_expiry_date(hostname: str, port: int) -> datetime.datetime | None: # <--- 修改：增加 port 参数
    """获取指定主机和端口的 SSL 证书过期日期"""
    context = ssl.create_default_context()
    try:
        # <--- 修改：使用传入的 hostname 和 port
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date_str = cert['notAfter']
                return datetime.datetime.strptime(expiry_date_str, '%b %d %H:%M:%S %Y %Z')
    except (socket.gaierror, socket.timeout, ssl.SSLError, ConnectionRefusedError) as e:
        print(f"❌ 无法连接到 {hostname}:{port}: {e}") # <--- 修改：打印端口
        return None
    except Exception as e:
        print(f"❌ 检查 {hostname}:{port} 时发生未知错误: {e}") # <--- 修改：打印端口
        return None

def send_bark_notification(title: str, body: str, bark_key: str):
    """通过 Bark 发送推送通知"""
    if not bark_key:
        print("❗ 未配置 Bark Key，跳过通知。")
        return

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
    
    if not BARK_KEY or not DOMAINS_STR:
        print("🔴 错误: 环境变量 BARK_KEY 和 DOMAINS 必须设置。")
        return
        
    # <--- 修改：domain_entries 保存原始的 "域名:端口" 字符串
    domain_entries = [d.strip() for d in DOMAINS_STR.split(',') if d.strip()]
    if not domain_entries:
        print("🔴 错误: 从环境变量 DOMAINS 中未解析出有效域名。")
        return

    print(f"🔍 将检测以下 {len(domain_entries)} 个条目，阈值为 {DAYS_THRESHOLD} 天:")
    for entry in domain_entries:
        print(f"  - {entry}")
    
    print("-" * 20)

    expiring_soon_count = 0
    # <--- 修改：循环处理每个条目
    for entry in domain_entries:
        # 解析域名和端口
        if ':' in entry:
            parts = entry.rsplit(':', 1) # 使用 rsplit 从右边分割，避免 IPv6 地址问题
            hostname = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                print(f"🟡 警告: '{entry}' 中的端口无效，跳过此条目。")
                continue
        else:
            hostname = entry
            port = DEFAULT_PORT
            
        # 开始检测
        expiry_date = get_cert_expiry_date(hostname, port)
        if expiry_date:
            now = datetime.datetime.now()
            days_left = (expiry_date - now).days

            if days_left < 0:
                print(f"🔴 {entry} - 证书已过期 {abs(days_left)} 天！")
                title = f"SSL证书已过期⚠️"
                body = f"域名 {entry} 的证书已于 {expiry_date.strftime('%Y-%m-%d')} 过期！"
                send_bark_notification(title, body, BARK_KEY)
                expiring_soon_count += 1
            elif days_left <= DAYS_THRESHOLD:
                print(f"🟠 {entry} - 证书将在 {days_left} 天后过期 (日期: {expiry_date.strftime('%Y-%m-%d')})")
                title = f"SSL证书即将过期提醒"
                body = f"域名 {entry} 的证书将在 {days_left} 天后过期，请及时续签！"
                send_bark_notification(title, body, BARK_KEY)
                expiring_soon_count += 1
            else:
                print(f"🟢 {entry} - 正常，剩余 {days_left} 天。")
    
    print("-" * 20)
    if expiring_soon_count == 0:
        print("🎉 所有证书状态良好！")
    else:
        print(f"🚨 共发现 {expiring_soon_count} 个证书需要关注。")

if __name__ == "__main__":
    main()
