import paramiko
from datetime import datetime

DNS_SERVER_NAME = "DNS1"
DNS_SERVER_IP = "10.10.10.10"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SERVICE_NAME = "named"

checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("DNS Service Restart")
print(f"Restarted at: {checked_at}")
print(f"Server: {DNS_SERVER_NAME} ({DNS_SERVER_IP})")
print(f"Service: {SERVICE_NAME}")
print("-" * 80)
print("Restart command executed")

client = None

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=DNS_SERVER_IP,
        port=22,
        username=USERNAME,
        password=PASSWORD,
        timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )

    stdin, stdout, stderr = client.exec_command(f"sudo systemctl restart {SERVICE_NAME}")

    service_status = stdout.read().decode().strip()
    service_error = stderr.read().decode().strip()
    stdin.close()
    stdout.close()
    stderr.close()

    stdin, stdout, stderr = client.exec_command(f"systemctl is-active {SERVICE_NAME}")
    
    service_status = stdout.read().decode().strip()
    service_error = stderr.read().decode().strip()

    stdin.close()
    stdout.close()
    stderr.close()

    if service_status == "active":
        print("DNS service status: active")
        print("DNS service is running")
    else:
        print(f"DNS service status: {service_status}")
        print("DNS service did not restart successfully")

    if service_error:
        print(f"Service check error: {service_error}")
except Exception as error:
    print(f"DNS service restart failed: {error}")

finally:
    if client:
        client.close()
