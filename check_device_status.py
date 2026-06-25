import csv
import subprocess
import platform 
from datetime import datetime
from ipaddress import ip_address
import paramiko 
import re
import socket

def is_valid_ipv4(address: str) -> bool:
    try:
        return ip_address(address).version == 4
    except ValueError:
        return False

now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20", "127.0.0.1"}

print("Device Status and DNS Verification")
print("Checked at:", timestamp_str)
print(f"{'Device':<10} {'Address' :<16} {'Ping Status':<14} DNS Status")
print("-" * 80)

ping_count_flag = "-n" if platform.system().lower() == "windows" else "-c"

with open("network_devices.csv") as infile, \
     open("device_status_results.csv", "w", newline='') as outfile:   
    
    reader = csv.DictReader(infile)

    fieldnames = ["Device Name", "Device Address", "Ping Status", 
                 "DNS Status", "Checked At"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        address = row["Device Address"].strip()
        name = row["Device Name"].strip()
        os = row["OS"].strip()
        port_name = row["Access Port"].strip()
        username = row["Username"].strip()
        password = row["Password"].strip()


        if address == "DHCP":
            ping_status = "Skipped"
            dns_status = "Skipped - DHCP address"
        elif address == "None":
            ping_status = "Skipped"
            dns_status = "Skipped - No IP Address"
        elif name == "SMTP":
            try:
                with socket.create_connection((address, 1025), timeout=5):
                    ping_status = "Reachable"
                    dns_status = "SMTP service reachable on port 1025; DNS shell check unavailable"
            except OSError as error:
                ping_status = f"Unreachable: {error}"

        elif is_valid_ipv4(address):
            try:
                process_result = subprocess.run(
                        ["ping", ping_count_flag, "1", address],
                        capture_output=True,
                        text=True,
                        timeout=9
                        )

                if process_result.returncode == 0:
                    ping_status = "Reachable"
                    try:
                        if os.lower() == "ubuntu":
                            client.connect(
                                    hostname=address,
                                    port=22,
                                    username=username,
                                    password=password,
                                    timeout=10,
                                    look_for_keys=False,
                                    allow_agent=False,)
                            stdin, stdout, stderr = client.exec_command("resolvectl dns")
                            command_output = stdout.read().decode().strip()
                            command_error = stderr.read().decode().strip()

                            if command_output:
                                clean_dns_output = " | ".join(command_output.splitlines())
                                dns_status = clean_dns_output
                                dns_servers_found = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", dns_status)
                                unauthorized_dns = [
                                        server for server in dns_servers_found
                                        if server not in APPROVED_DNS_SERVERS
                                        ]
                                if unauthorized_dns:
                                    dns_status = f"{dns_status} | Unauthorized DNS detected: {', '.join(unauthorized_dns)}"

                            elif command_error: 
                                clean_dns_error = " | ".join(command_error.splitlines())
                                dns_status = clean_dns_error

                            else:
                                dns_status = "DNS settings not found"

                            client.close()
                        
                        elif os == "VyOS":
                            dns_status = "Skipped - DNS command not supported for VyOS"

                        else:
                            dns_status = f"Skipped - no supported DNS Verification Method"

                    except Exception as error:
                        dns_status = f"DNS check failed: {error}"

                else:
                    ping_status = "Unreachable"
                    dns_status = "Not verified - device unreachable"

            except subprocess.TimeoutExpired:
                ping_status = "Timeout"
                dns_status = "Not Verified - ping timeout"
            
        else:
            ping_status = "Skipped"
            dns_status = "Skipped - invalid ipv4 address"

        print(f"{name:<10} {address:<16} {ping_status:<14} {dns_status}")

        writer.writerow({
            "Device Name": name,
            "Device Address": address,
            "Ping Status": ping_status,
            "DNS Status": dns_status,
            "Checked At": timestamp_str
        })

print("Results have been saved to 'device_status_results.csv'")


            
                


    
        




                


