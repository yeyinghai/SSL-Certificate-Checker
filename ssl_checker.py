import ssl
import socket
import datetime
import configparser
from OpenSSL import crypto
import requests
import sys

def read_config(config_file):
    """读取配置文件"""
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        return config
    except Exception as e:
        print(f"Error reading config file {config_file}: {e}")
        sys.exit(1)

def get_cert_expiry(hostname, port=443):
    """获取证书过期时间"""
    context = ssl.create_default_context()
    try:
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as conn:
            conn.settimeout(10) # Increased timeout for potentially slower connections
            conn.connect((hostname, port))
            cert_bin = conn.getpeercert(binary_form=True)
            cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bin)
            expiry = datetime.datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
            return expiry
    except ssl.SSLError as e:
        print(f"SSL Error for {hostname}:{port} - {e}. Skipping.")
        return None
    except socket.timeout:
        print(f"Connection to {hostname}:{port} timed out. Skipping.")
        return None
    except ConnectionRefusedError:
        print(f"Connection to {hostname}:{port} refused. Skipping.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for {hostname}:{port} - {e}. Skipping.")
        return None

def send_bark_notification(config, title, body):
    """发送 Bark 通知"""
    try:
        bark_url = config['bark']['base_url'].strip('/')
        device_key = config['bark']['device_key']
    except KeyError as e:
        print(f"Bark configuration missing: {e}. Cannot send notification.")
        return

    url = f"{bark_url}/{device_key}/{title}/{body}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Bark notification sent successfully for: {title}")
    except requests.exceptions.RequestException as e:
        print(f"Bark push failed: {e}")

def main():
    config = read_config('config.ini')

    try:
        warning_days = int(config['ssl_checks']['warning_days'])
    except KeyError:
        print("Warning days not specified in config.ini. Using default 30 days.")
        warning_days = 30
    except ValueError:
        print("Invalid value for warning_days in config.ini. Using default 30 days.")
        warning_days = 30

    domains = {}
    try:
        # Parse domains from the multiline 'domains' key
        for line in config['ssl_checks']['domains'].splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('=')
            domain = parts[0].strip()
            port = 443
            if len(parts) == 2:
                try:
                    port = int(parts[1].strip())
                except ValueError:
                    print(f"Invalid port for {domain}. Defaulting to 443.")
            domains[domain] = port
    except KeyError:
        print("No domains specified in config.ini. Please add domains under [ssl_checks].")
        sys.exit(1)

    if not domains:
        print("No domains found to check. Exiting.")
        sys.exit(0)

    print(f"Checking SSL certificates for {len(domains)} domains...")
    for domain, port in domains.items():
        print(f"  Checking {domain}:{port}...")
        expiry = get_cert_expiry(domain, port)
        if not expiry:
            continue # Error already printed by get_cert_expiry

        now = datetime.datetime.utcnow()
        delta = (expiry - now).days

        status_message = f"{domain}:{port} - 证书剩余 {delta} 天"
        print(f"    {status_message}")

        if delta < 0:
            send_bark_notification(config,
                                   f"⚠️ {domain} 证书已过期",
                                   f"过期时间: {expiry.strftime('%Y-%m-%d %H:%M')} UTC")
        elif delta < warning_days:
            send_bark_notification(config,
                                   f"⚠️ {domain} 证书即将过期",
                                   f"剩余 {delta} 天 (过期时间: {expiry.strftime('%Y-%m-%d %H:%M')} UTC)")
        # else:
        #     print(f"    {domain} 证书有效，距离过期还有较长时间。")


if __name__ == "__main__":
    main()
    