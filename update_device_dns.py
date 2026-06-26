import csv
import re
import paramiko
from datetime import datetime

RESULTS_FILE = "device_status_results.csv"
APPROVED_DNS_SERVERS = ["10.10.10.10", "10.10.10.20"]
USERNAME = "ubuntu"
PASSWORD = "ubuntu"

def extract_ipv4_addresses(text):
    return re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)

def find_unauthorized_dns(dns_status):
    found_servers = extract_ipv4_addresses(dns_status)

    unauthorized_servers = []
    for server in found_servers:
        if server not in APPROVED_DNS_SERVERS and server not in unauthorized_servers:
            unauthorized_servers.append(server)

    return unauthorized_servers

def run_remote_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    stdin.close()
    stdout.close()
    stderr.close()

    return output, error

affected_devices = []


with open(RESULTS_FILE) as file:
    reader = csv.DictReader(file)

    for row in reader:
        dns_status = row.get("DNS Status", "")
        unauthorized_dns = find_unauthorized_dns(dns_status)

        if unauthorized_dns:
            affected_devices.append({
                "name": row.get("Device Name", ""),
                "ip": row.get("Device Address", ""),
                "dns_status": dns_status,
                "unauthorized_dns": unauthorized_dns,
            })

if not affected_devices:
    print("No affected devices found. No DNS updates needed.")
    raise SystemExit(0)

for device in affected_devices:
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("Affected Device DNS Remediation")
    print(f"Started at: {started_at}")
    print(f"Approved DNS servers: {', '.join(APPROVED_DNS_SERVERS)}")
    print("-" * 80)

    replacement_commands = []

    for index, unauthorized_server in enumerate(device["unauthorized_dns"]):
        approved_server = APPROVED_DNS_SERVERS[index % len(APPROVED_DNS_SERVERS)]
        replacement_commands.append(
            f"sudo sed -i 's/{unauthorized_server}/{approved_server}/g' /etc/netplan/*.yaml"
        )
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname=device["ip"],
            port=22,
            username=USERNAME,
            password=PASSWORD,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        before_output, before_error = run_remote_command(client, "resolvectl dns")

        print(f"Updating DNS settings for {device['name']} ({device['ip']})")
        print(f"Unauthorized DNS detected: {', '.join(device['unauthorized_dns'])}")
        print("Before DNS settings:")
        print(before_output)

        if before_error:
            print(f"Before check error: {before_error}")

        for command in replacement_commands:
            output, error = run_remote_command(client, command)

            if error:
                print(f"Replacement error: {error}")

        apply_output, apply_error = run_remote_command(client, "sudo netplan apply")

        if apply_output:
            print(apply_output)

        if apply_error:
            print(f"Netplan apply message: {apply_error}")

        after_output, after_error = run_remote_command(client, "resolvectl dns")

        print("After DNS settings:")
        print(after_output)

        if after_error:
            print(f"After check error: {after_error}")

        remaining_unauthorized = []

        for server in device["unauthorized_dns"]:
            if server in after_output:
                remaining_unauthorized.append(server)

        if remaining_unauthorized:
            print(f"DNS update incomplete. Still found: {', '.join(remaining_unauthorized)}")
        else:
            print(f"DNS settings update completed for {device['name']}")

        print("-" * 80)
        
    except Exception as error:
        print(f"DNS update failed for {device['name']}: {error}")

    finally:
        if client:
            client.close()



