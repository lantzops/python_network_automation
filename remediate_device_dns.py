import re
import shlex
import paramiko
from datetime import datetime
from ipaddress import ip_address

ALLOWED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20", "127.0.0.1"}
REPLACEMENT_DNS_SERVERS = ["10.10.10.10", "10.10.10.20"]

def run_remote_command(client, command):
    stdin, stdout, stderr = client.exec_command(command, timeout=10)

    try:
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(f"Remote command failed (exit {exit_status}): {error or command}")
        return output, error
    finally:
        stdin.close()
        stdout.close()
        stderr.close()

def remediate_device_dns(device, username, password):
    name = device["Device Name"]
    address = device["Device Address"]
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("Affected Device DNS Remediation")
    print(f"Started at: {started_at}")
    print(f"Allowed DNS servers: {', '.join(sorted(ALLOWED_DNS_SERVERS))}")
    print("-" * 80)

    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname=address,
            port=22,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

     
        run_remote_command(client, "test -f /etc/resolv.conf && test ! -L /etc/resolv.conf")
        before_output, before_error = run_remote_command(client, "cat /etc/resolv.conf")

        print(f"Updating DNS settings for {name} ({address})")
        print("Before DNS settings:")
        print(before_output)

        if before_error:
            raise RuntimeError(f"Before check error: {before_error}")
        
        nameservers = []

        for line in before_output.splitlines():
            fields = line.split()

            if not fields or fields[0] != "nameserver":
                continue

            if len(fields) < 2:
                raise RuntimeError("Nameserver address is missing")

            server = fields[1]

            try:
                ip_address(server)
            except ValueError:
                raise RuntimeError(f"Invalid DNS address: {server}")

            nameservers.append(server)

        if not nameservers:
            raise RuntimeError("No nameserver entries found")

        unauthorized_dns = []

        for server in nameservers:
            if (
                server not in ALLOWED_DNS_SERVERS
                and server not in unauthorized_dns
            ):
                unauthorized_dns.append(server)

        if not unauthorized_dns:
            print(f"DNS settings already approved for {name}; no change needed.")
            return True

        print(
            f"Unauthorized DNS detected: {', '.join(unauthorized_dns)}"
        )

        backup_path = "/etc/resolv.conf.bak." + datetime.now().strftime("%Y%m%dT%H%M%S%f")
        backup_output, backup_error = run_remote_command(
            client, f"sudo -n cp -p /etc/resolv.conf {backup_path}"
        )
        if backup_error:
            raise RuntimeError(f"DNS backup failed: {backup_error}")
        print(f"Backup saved on device: {backup_path}")

        replacement_commands = []
        for index, unauthorized_server in enumerate(unauthorized_dns):
            approved_server = REPLACEMENT_DNS_SERVERS[index % len(REPLACEMENT_DNS_SERVERS)]
            # Match only a complete address on a nameserver line, preserving comments.
            pattern = (
                rf"^([[:space:]]*nameserver[[:space:]]+)"
                rf"{re.escape(unauthorized_server)}([[:space:]].*)?$"
            )
            expression = rf"s|{pattern}|\1{approved_server}\2|"
            replacement_commands.append(
                f"sudo -n sed -E -i {shlex.quote(expression)} /etc/resolv.conf"
            )

        for command in replacement_commands:
            output, error = run_remote_command(client, command)

            if error:
                raise RuntimeError(f"Replacement error: {error}")
 
        after_output, after_error = run_remote_command(client, "cat /etc/resolv.conf")

        print("After DNS settings:")
        print(after_output)

        if after_error:
            raise RuntimeError(f"After check error: {after_error}")

        nameservers = []
        for line in after_output.splitlines():
            fields = line.split()
            if fields and fields[0] == "nameserver":
                if len(fields) < 2:
                    raise RuntimeError("DNS verification failed: nameserver address missing")
                try:
                    ip_address(fields[1])
                except ValueError:
                    raise RuntimeError(f"DNS verification failed: invalid address {fields[1]}")
                nameservers.append(fields[1])
        if not nameservers:
            raise RuntimeError("DNS verification failed: no nameserver entries found")
        remaining_unauthorized = []

        for server in nameservers:
            if server not in ALLOWED_DNS_SERVERS:
                remaining_unauthorized.append(server)

        if remaining_unauthorized:
            print(f"DNS update incomplete. Still found: {', '.join(remaining_unauthorized)}")

            return False
        else:
            print(f"DNS settings update completed for {name}")

        print("-" * 80)
        return True
        
    except Exception as error:
        print(f"DNS update failed for {name}: {error}")
        return False

    finally:
        if client:
            client.close()
