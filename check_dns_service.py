import paramiko
from datetime import datetime

DNS_SERVER_NAME_1 = "DNS1"
DNS_SERVER_NAME_2 = "DNS2"
DNS_SERVER_IP_1 = "10.10.10.10"
DNS_SERVER_IP_2 = "10.10.10.20"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SERVICE_NAME = "named"

checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("DNS Service Verification")
print(f"Checked at: {checked_at}")
print(f"Server: {DNS_SERVER_NAME_1} ({DNS_SERVER_IP_1})")
print(f"Service: {SERVICE_NAME}")
print("-" * 80)

client = None

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=DNS_SERVER_IP_1,
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
    stdin.close()
    stdout.close()
    stderr.close()


    if service_status == "active":
        print("DNS service status: active")
        print("DNS service is running")
    else:
        print(f"DNS service status: {service_status}")
        print("DNS service is down")

    if service_error:
        print(f"Service check error: {service_error}")
except Exception as error:
    print(f"DNS service check failed: {error}")

finally:
    if client:
        client.close()



print(f"Server: {DNS_SERVER_NAME_2} ({DNS_SERVER_IP_2})")
print(f"Service: {SERVICE_NAME}")
print("-" * 80)

client = None

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=DNS_SERVER_IP_2,
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
    stdin.close()
    stdout.close()
    stderr.close()


    if service_status == "active":
        print("DNS service status: active")
        print("DNS service is running")
    else:
        print(f"DNS service status: {service_status}")
        print("DNS service is down")

    if service_error:
        print(f"Service check error: {service_error}")
except Exception as error:
    print(f"DNS service check failed: {error}")

finally:
    if client:
        client.close()
