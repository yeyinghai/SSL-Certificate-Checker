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
