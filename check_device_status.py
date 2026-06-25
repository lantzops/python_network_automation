import csv
import subprocess
import platform 
from datetime import datetime
from ipaddress import ip_address
import paramiko 

def is_valid_ipv4(address: str) -> bool:
    try:
        return ip_address(address).version == 4
    except ValueError:
        return False

now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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
        access_port = row["Access Port"].strip()
        os = row["OS"].strip()
        username = row["Username"].strip()
        password = row["Password"].strip()


        if address == "DHCP":
            ping_status = "Skipped"
            dns_status = "Skipped - DHCP address"
        elif address == "None":
            ping_status = "Skipped"
            dns_status = "Skipped - No IP Address"
        elif is_valid_ipv4(address):
            try:
                process_result = subprocess.run(
                        ["ping", ping_count_flag, "1", address],
                        capture_output=True,
                        text=True,
                        timeout=3
                        )

                if process_result.returncode == 0:
                    ping_status = "Reachable"
                    try:
                        client.connect(
                                hostname="localhost",
                                port=int(access_port),
                                username=username,
                                password=password,
                                timeout=10,
                                look_for_keys=False,
                                allow_agent=False,)
                        stdin, stdout, stderr = client.exec_command("resolvectl dns")
                        command_output = stdout.read().decode().strip()
                        command_error = stderr.read().decode().strip()

                        if command_output:
                            dns_status = command_output

                        elif command_error: 
                            dns_status = command_error

                        else:
                            dns_status = "DNS settings not found"

                        client.close()
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


            
                


    
        




                


