import csv
import subprocess
import platform 
from datetime import datetime
from enum import Enum
from ipaddress import ip_address
import paramiko 
import re
import socket
import shlex
from monitor_tickets import create_ticket, resolve_ticket
from monitor_email import send_unavailable_email
from dns_altered_alert import send_dns_altered_email
from remediate_device_dns import remediate_device_dns
from monitor_log import log_healthy_dns
import time

CHECK_INTERVAL_SECONDS = 60
MAX_EMAIL_ATTEMPTS = 3
NETWORK_DEVICE_FILE = "network_devices.csv"
RESULTS_FILE = "device_status_results.csv"
DNS_TEST_HOSTNAME = "helpdesk.d522.wgu.internal"
DNS_TEST_EXPECTED_IP = "10.10.10.200"

ROUTER_IP = "10.10.10.1"
ROUTER_USERNAME = "vyos"
ROUTER_PASSWORD = "vyos"
DHCP_LEASE_COMMAND = "/opt/vyatta/bin/vyatta-op-cmd-wrapper show dhcp server leases"

SMTP_SERVICE_PORT = 1025
SSH_PORT = 22
APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20", "127.0.0.1"}

class IncidentState(Enum):
    ACTIVE = "active"
    RECOVERED = "recovered"

class DNSStatus(Enum):
    APPROVED = "approved"
    UNAUTHORIZED = "unauthorized"
    UNVERIFIED = "unverified" 

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
            error = error or f"Remote command failed with exit status {exit_status}"
        return output, error
    finally:
        stdin.close()
        stdout.close()
        stderr.close()

def get_dhcp_leases_from_vyos():
    client = None
    dhcp_leases = {}

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
                hostname=ROUTER_IP,
                port=SSH_PORT,
                username=ROUTER_USERNAME,
                password=ROUTER_PASSWORD,
                timeout=10,
                look_for_keys=False,
                allow_agent=False,
        )
        output, error = run_remote_command(client, DHCP_LEASE_COMMAND)

        if error:
            raise RuntimeError(error)

        for line in output.splitlines():
            tokens = line.split()
            if len(tokens) < 11:
                continue
            ip = tokens[0]
            status = tokens[2]
            hostname = tokens[-2]

            if not is_valid_ipv4(ip):
                continue
            if status.lower() != "active":
                continue

            dhcp_leases[hostname.upper()] = ip

            
    except Exception as error:
        print(f"DHCP Lease Check Failed: {error}")

    finally:
        if client:
            client.close()

    return dhcp_leases

def check_devices_run():

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")


    print("Device Status and DNS Verification")
    print("Checked at:", timestamp_str)
    print(f"{'Device':<10} {'Address' :<16} {'Ping Status':<14} DNS Status")
    print("-" * 80)

    ping_count_flag = "-n" if platform.system().lower() == "windows" else "-c"

    dhcp_leases = get_dhcp_leases_from_vyos()
    results = []



    with open(NETWORK_DEVICE_FILE) as infile, \
         open(RESULTS_FILE, "w", newline='') as outfile:
        
        reader = csv.DictReader(infile)

        fieldnames = ["Device Name", "Device Address", "Ping Status", 
                     "DNS Status", "DNS Check Status", "DNS Resolution Verified",
                     "DNS Resolution Detail", "Checked At"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            address = row["Device Address"].strip()
            name = row["Device Name"].strip()
            os = row["OS"].strip()
            port_name = row["Access Port"].strip()
            username = row["Username"].strip()
            password = row["Password"].strip()
            dns_check_status = DNSStatus.UNVERIFIED
            dns_resolution_verified = False
            dns_resolution_detail = "Not tested; approved DNS configuration required"

            if address == "DHCP":
                address = dhcp_leases.get(name.upper(), "DHCP")


            if address == "DHCP":
                ping_status = "Skipped"
                dns_status = "DHCP lease unavailable; DNS not verified"
            elif address == "None":
                ping_status = "Skipped"
                dns_status = "Skipped - No IP Address"
            elif name == "SMTP":
                try:
                    with socket.create_connection((address, 1025), timeout=5):
                        ping_status = "Reachable"
                        dns_status = "SMTP service reachable on port 1025; DNS shell check unavailable"
                except OSError as error:
                    ping_status = "Unreachable"
                    dns_status = f"DNS not verified; SMTP connection failed: {error}"

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
                        client = None

                        try:
                            if os.lower() == "ubuntu":
                                client = paramiko.SSHClient()
                                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                client.connect(
                                        hostname=address,
                                        port=22,
                                        username=username,
                                        password=password,
                                        timeout=10,
                                        look_for_keys=False,
                                        allow_agent=False,)
                                command_output, command_error = run_remote_command(
                                    client, "resolvectl dns"
                                )

                                if command_output and not command_error:
                                    clean_dns_output = " | ".join(command_output.splitlines())
                                    dns_status = clean_dns_output
                                    dns_servers_found = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", dns_status)
                                    unauthorized_dns = [
                                            server for server in dns_servers_found
                                            if server not in APPROVED_DNS_SERVERS
                                            ]
                                    if unauthorized_dns:
                                        dns_check_status = DNSStatus.UNAUTHORIZED
                                        dns_status = (
                                            f"{dns_status} | Unauthorized DNS detected: "
                                            f"{', '.join(unauthorized_dns)}"
                                        )
                                    elif dns_servers_found:
                                        dns_check_status = DNSStatus.APPROVED

                                elif command_error:
                                    fallback_output, fallback_error = run_remote_command(
                                        client, "cat /etc/resolv.conf"
                                    )

                                    if fallback_error:
                                        dns_status = f"DNS verification failed: {fallback_error}"
                                    else:
                                        dns_servers_found = []

                                        for line in fallback_output.splitlines():
                                            fields = line.split()
                                            if len(fields) >= 2 and fields[0] == "nameserver":
                                                dns_servers_found.append(fields[1])

                                        if dns_servers_found:
                                            dns_status = f"/etc/resolv.conf: {', '.join(dns_servers_found)}"

                                            unauthorized_dns = [
                                                server for server in dns_servers_found
                                                if server not in APPROVED_DNS_SERVERS
                                            ]

                                            if unauthorized_dns:
                                                dns_check_status = DNSStatus.UNAUTHORIZED
                                                dns_status += (
                                                    f" | Unauthorized DNS detected: {', '.join(unauthorized_dns)}"
                                                )
                                            elif dns_servers_found:
                                                dns_check_status = DNSStatus.APPROVED
                                        else:
                                            dns_status = "DNS not verified; no nameserver entries found"

                                else:
                                    dns_status = "DNS settings not found"

                                if dns_check_status == DNSStatus.APPROVED:
                                    try:
                                        # dig uses DNS rather than a possible /etc/hosts entry.
                                        lookup_output, lookup_error = run_remote_command(
                                            client,
                                            "dig +short +time=2 +tries=1 "
                                            f"{shlex.quote(DNS_TEST_HOSTNAME)} A",
                                        )
                                        answers = {
                                            line.strip() for line in lookup_output.splitlines()
                                            if is_valid_ipv4(line.strip())
                                        }
                                        dns_resolution_verified = (
                                            not lookup_error
                                            and answers == {DNS_TEST_EXPECTED_IP}
                                        )
                                        if dns_resolution_verified:
                                            dns_resolution_detail = (
                                                f"{DNS_TEST_HOSTNAME} resolved to {DNS_TEST_EXPECTED_IP}"
                                            )
                                        else:
                                            dns_resolution_detail = (
                                                "DNS lookup not verified: "
                                                f"{lookup_error or lookup_output or 'no A records returned'}"
                                            )
                                    except Exception as error:
                                        dns_resolution_detail = f"DNS lookup failed: {error}"
                            
                            elif os == "VyOS":
                                dns_status = "Skipped - DNS command not supported for VyOS"

                            else:
                                dns_status = f"Skipped - no supported DNS Verification Method"

                        except Exception as error:
                            dns_check_status = DNSStatus.UNVERIFIED
                            dns_status = f"DNS check failed: {error}"

                        finally:
                            if client:
                                client.close()


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
            if dns_check_status == DNSStatus.APPROVED:
                print(f"  DNS resolution: {dns_resolution_detail}")

            result = {
                "Device Name": name,
                "Device Address": address,
                "Ping Status": ping_status,
                "DNS Status": dns_status,
                "DNS Check Status": dns_check_status.value,
                "DNS Resolution Verified": dns_resolution_verified,
                "DNS Resolution Detail": dns_resolution_detail,
                "Checked At": timestamp_str
            }
            writer.writerow(result)
            results.append(result)

    print("Results have been saved to 'device_status_results.csv'")
    return results

def resolve_dns_incident_ticket(incident):
    if incident["ticket_resolution_attempted"]:
        return

    incident["ticket_resolution_attempted"] = True
    ticket_id = incident["ticket_id"]

    if ticket_id is None:
        incident["ticket_resolution_needs_review"] = True
        print("DNS recovered, but no ticket ID is available; review needed.")
        return

    incident["ticket_resolved"] = resolve_ticket(ticket_id)
    incident["ticket_resolution_needs_review"] = (
        not incident["ticket_resolved"]
    )

    if incident["ticket_resolution_needs_review"]:
        print(f"DNS recovered, but ticket {ticket_id} needs resolution review.")

def process_dns_result(device, dns_incidents, incident_history):
    name = device["Device Name"]
    status = device.get("DNS Check Status", DNSStatus.UNVERIFIED.value)
    incident = dns_incidents.get(name)

    if status == DNSStatus.UNVERIFIED.value:
        print(f"DNS unverified for {name}; no remediation or recovery assumed.")
        return

    if status == DNSStatus.APPROVED.value:
        log_healthy_dns(device)

        if incident and incident["state"] == IncidentState.ACTIVE:
            incident["state"] = IncidentState.RECOVERED
            incident["recovered_at"] = device["Checked At"]
            resolve_dns_incident_ticket(incident)
            print(f"DNS configuration verified approved for {name}.")
        return

    if status != DNSStatus.UNAUTHORIZED.value:
        return
    if incident and incident["state"] == IncidentState.ACTIVE:
        return
    if incident is not None:
        incident_history.append(incident.copy())

    incident = {
        "device_name": name,
        "device_address": device["Device Address"],
        "issue_type": "Unauthorized DNS configuration",
        "started_at": device["Checked At"],
        "state": IncidentState.ACTIVE,
        "email_sent": False,
        "email_needs_review": False,
        "ticket_id": None,
        "ticket_needs_review": False,
        "remediation_attempted": False,
        "remediation_verified": False,
        "remediation_needs_review": False,
        "ticket_resolved": False,
        "ticket_resolution_attempted": False,
        "ticket_resolution_needs_review": False,
    }
    dns_incidents[name] = incident

    # One attempt per DNS incident; failures require review before another write.
    email_result = send_dns_altered_email(device)
    incident["email_sent"] = email_result is True
    incident["email_needs_review"] = email_result is not True
    if incident["email_needs_review"]:
        print(f"DNS alert for {name} needs review; automatic email retries paused.")

    incident["ticket_id"] = create_ticket(device, incident["issue_type"])
    incident["ticket_needs_review"] = incident["ticket_id"] is None

    try:
        # Keep credentials out of the scan CSV and incident history.
        with open(NETWORK_DEVICE_FILE) as infile:
            matches = [
                row for row in csv.DictReader(infile)
                if row["Device Name"].strip() == name
            ]
        if len(matches) != 1:
            raise ValueError(f"Expected one inventory row for {name}; found {len(matches)}")
        credentials = matches[0]
        username = credentials["Username"].strip()
        password = credentials["Password"]
        if not username or not password:
            raise ValueError(f"Missing SSH credentials for {name}")
        incident["remediation_attempted"] = True
        verified = remediate_device_dns(device, username, password)
    except (OSError, KeyError, ValueError) as error:
        print(f"Cannot prepare DNS remediation for {name}: {error}")
        verified = False

    incident["remediation_verified"] = verified is True
    if verified is True:
        incident["state"] = IncidentState.RECOVERED
        incident["recovered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resolve_dns_incident_ticket(incident)
        print(f"DNS file settings verified for {name}.")
    else:
        incident["remediation_needs_review"] = True
        print(f"DNS remediation for {name} needs review; automatic retries paused.")


def process_scan_results(results, incidents, incident_history, dns_incidents):
    for device in results:
        name = device["Device Name"]
        ping_status = device["Ping Status"]
        incident = incidents.get(name)

        if ping_status == "Reachable":
            if incident and incident["state"] == IncidentState.ACTIVE:
                incident["state"] = IncidentState.RECOVERED
                incident["recovered_at"] = device["Checked At"]
                print(f"{name} is reachable again; incident marked as recovered.")
            process_dns_result(device, dns_incidents, incident_history)
            continue

        if ping_status not in ("Unreachable", "Timeout"):
            continue

        if incident is None or incident["state"] == IncidentState.RECOVERED:
            if incident is not None:
                incident_history.append(incident.copy())

            incidents[name] = {
                "device_name": name,
                "device_address": device["Device Address"],
                "started_at": device["Checked At"],
                "ticket_id": None,
                "issue_type": "Device unavailable",
                "ticket_attempted": False,
                "needs_review": False,
                "email_sent": False,
                "email_attempts": 0,
                "email_needs_review": False,
                "state": IncidentState.ACTIVE,
            }

        incident = incidents[name]
        if not incident["ticket_attempted"]:
            incident["ticket_attempted"] = True
            incident["ticket_id"] = create_ticket(device, "Device unavailable")
            if incident["ticket_id"] is None:
                incident["needs_review"] = True
                print(f"Ticket creation needs review for {name}; retries are paused.")

        if incident["email_sent"] or incident["email_needs_review"]:
            continue
        if incident["email_attempts"] >= MAX_EMAIL_ATTEMPTS:
            continue

        incident["email_attempts"] += 1
        email_result = send_unavailable_email(device)
        if email_result is True:
            incident["email_sent"] = True
        elif email_result is None:
            incident["email_needs_review"] = True
            print(f"Email delivery uncertain for {name}; check MailHog. Retries paused.")
        elif incident["email_attempts"] >= MAX_EMAIL_ATTEMPTS:
            incident["email_needs_review"] = True
            print(f"Email failed after {MAX_EMAIL_ATTEMPTS} attempts for {name}; review needed.")
        else:
            print(f"Email for {name} will be retried on the next scan if still unavailable.")


def main():
    incidents = {}
    incident_history = []
    dns_incidents = {}

    try:
        while True:
            results = check_devices_run()
            process_scan_results(results, incidents, incident_history, dns_incidents)

            print(
                    f"Next scan in {CHECK_INTERVAL_SECONDS} seconds."
            )
            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(f"\nMonitoring stopped.")


if __name__ == "__main__":
    main()



            
                


    
        




                
