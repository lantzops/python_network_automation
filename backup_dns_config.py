import csv
from datetime import datetime
from ipaddress import ip_address
from pathlib import Path
import paramiko

NETWORK_DEVICE_FILE = "network_devices.csv"
RESULTS_FILE = "record-config.txt"
SSH_PORT = 22
BACKUP_ROOT = "DNS-Backup" 
DNS_SERVER_NAMES = ["DNS1", "DNS2"]
BIND_CONFIG_FILES = [
    "/etc/bind/named.conf",
    "/etc/bind/named.conf.options",
    "/etc/bind/named.conf.local",
    "/etc/bind/named.conf.default-zones",
]
DNS1_ZONE_FILES = [
    "/etc/bind/zones/db.d522.wgu.internal",
    "/etc/bind/zones/db.10.10.10",
    "/etc/bind/zones/db.20.168.192",
    "/etc/bind/zones/db.30.168.192",
]
DNS2_ZONE_FILE = "/var/cache/bind/db.d522.wgu.internal"
DNS2_ZONE_EXPORT_COMMAND = (
    "sudo -n named-compilezone -q -f raw -F text -o - "
    f"d522.wgu.internal {DNS2_ZONE_FILE}"
)
BACKUP_SUBDIRECTORIES = {"DNS1": "Server-1", "DNS2": "Server-2",}



def is_valid_ipv4(address: str) -> bool:
    try:
        return ip_address(address).version == 4
    except ValueError:
        return False

def run_remote_command(client, command):
    stdin, stdout, stderr = client.exec_command(command, timeout=10)
    try:
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(
                f"Remote command failed (exit {exit_status}): {error or command}"
            )
        return output, error
    finally:
        stdin.close()
        stdout.close()
        stderr.close()

now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")


print("DNS Configuration Backup")
print("Started at:", timestamp_str)
print("-" * 80)

dns_servers = []

with open(NETWORK_DEVICE_FILE) as file:    
    reader = csv.DictReader(file)

    for row in reader:
        if row["Device Name"].strip() in DNS_SERVER_NAMES:
            dns_servers.append(row)

for expected_name in DNS_SERVER_NAMES:
    matches = [
        server for server in dns_servers
        if server["Device Name"].strip() == expected_name
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one {expected_name} row; found {len(matches)}"
        )
    if not is_valid_ipv4(matches[0]["Device Address"].strip()):
        raise SystemExit(f"Invalid IPv4 address for {expected_name}")

for server in dns_servers:
    name = server["Device Name"].strip()
    address = server["Device Address"].strip()
    username = server["Username"].strip()
    password = server["Password"].strip()
    subdirectory = BACKUP_SUBDIRECTORIES[name]

    client = None
    sftp = None


    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=address,
            port=SSH_PORT,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        backup_directory = Path(BACKUP_ROOT) / subdirectory
        backup_directory.mkdir(parents=True, exist_ok=True)

        summary_sections = []
        files_to_copy = BIND_CONFIG_FILES.copy()

        for remote_path in BIND_CONFIG_FILES:
            output, error = run_remote_command(
                client, f"sudo -n cat {remote_path}"
            )

            if error:
                raise RuntimeError(f"Could not read {remote_path}: {error}")

            if not output.strip():
                raise RuntimeError(f"No content returned from {remote_path}")

            summary_sections.append(
                f"====== {remote_path} ======\n{output}\n"
            )

        if name == "DNS1":
            files_to_copy.extend(DNS1_ZONE_FILES)

            for path in DNS1_ZONE_FILES:
                output, error = run_remote_command(client, f"sudo -n cat {path}" )
                
                if error:
                    raise RuntimeError(f"Could not read {path}: {error}")

                if not output.strip():
                    raise RuntimeError(f"No content returned from {path}")

                summary_sections.append(
                    f"====== {path} ======\n{output}\n"
                )

        elif name == "DNS2":
            files_to_copy.append(DNS2_ZONE_FILE)

            output, error = run_remote_command(
                    client, DNS2_ZONE_EXPORT_COMMAND
            )

            if error:
                raise RuntimeError(
                    f"Could not read {DNS2_ZONE_FILE}: {error}"
                )

            if not output.strip():
                raise RuntimeError(
                    f"No content returned from {DNS2_ZONE_FILE}"
                )

            summary_sections.append(
                f"====== {DNS2_ZONE_FILE} (converted from raw to text) ======\n"
                f"{output}\n"
            )

        sftp = client.open_sftp()

        for remote_path in files_to_copy:
            relative_path = remote_path.lstrip("/")
            local_path = backup_directory / "files" / relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            if local_path.exists():
                raise FileExistsError(
                        f"Backup already exists: {local_path}"
                )

            sftp.get(remote_path, str(local_path))

            remote_size = sftp.stat(remote_path).st_size
            local_size = local_path.stat().st_size

            if local_size != remote_size:
                raise RuntimeError(
                        f"Backup size mismatch: {local_path}")

        backup_file = backup_directory / RESULTS_FILE

        header = (
                f"Server: {name}\n"
                f"Address: {address}\n"
                f"Backup timestamp: {timestamp_str}\n\n"
        )

        summary_text = header + "\n".join(summary_sections)

        with backup_file.open("x", encoding="utf-8") as file:
            file.write(summary_text)


        if backup_file.read_text(encoding="utf-8") != summary_text:
            raise RuntimeError(f"Backup verification failed: {backup_file}")

        print(f"Server: {name} ({address})")
        print(f"Backup saved: {backup_file.resolve()}")
        print("Result: SUCCESS")
        print("-" * 80)

    except Exception as error:
        print(f"Backup failed for {name}: {error}")

    finally:
        try:
            if sftp is not None:
                sftp.close()
        finally:
            if client is not None:
                client.close()


    
                

            
                


    
        




                
