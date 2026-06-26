import paramiko
from datetime import datetime

DNS_SERVER_NAME = "DNS1"
DNS_SERVER_IP = "10.10.10.10"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SERVICE_NAME = "named"

checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("DNS Service Verification")
print(f"Checked at: {checked_at}")
print(f"Server: {DNS_SERVER_NAME} ({DNS_SERVER_IP})")
print(f"Service: {SERVICE_NAME}")
print("-" * 80)

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

stdin, stdout, stderr = client.exec_command(f"systemctl is-active {SERVICE_NAME}")

service_status = stdout.read().decode().strip()
service_error = stderr.read().decode().strip()

if service_status == "active":
    print("DNS service status: active")
    print("DNS service is running")
else:
    print(f"DNS service status: {service_status}")
    print("DNS service is down")

if service_error:
    print(f"Service check error: {service_error}")

client.close()
