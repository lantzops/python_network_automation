import csv
import re
from ipaddress import ip_address
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


SMTP_HOST= "10.10.10.100"
SMTP_PORT= 1025
SUBJECT = "RESOLVED: DNS Service Issue and Device Compromise--All Issues Remediated"
SENDER = "network.monitoring@lantzops.com"
RECIPIENT = "stakeholders@lantzops.com"
BEFORE_RESULTS_FILE = "before_remediation_device_status_results.csv"
CURRENT_RESULTS_FILE = "device_status_results.csv"
APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20"}


now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

resolved_devices = []
affected_devices = {}
verification_errors = []

with open(BEFORE_RESULTS_FILE) as file:
    for row in csv.DictReader(file):
        if "Unauthorized DNS detected" in row.get("DNS Status", ""):
            name = row.get("Device Name", "").strip().upper()
            if not name or name in affected_devices:
                raise SystemExit("Invalid or duplicate device name in before-remediation results")
            affected_devices[name] = row

current_devices = {}
with open(CURRENT_RESULTS_FILE) as file:
    for row in csv.DictReader(file):
        name = row.get("Device Name", "").strip().upper()
        if name in current_devices:
            raise SystemExit(f"Duplicate device in current results: {name}")
        current_devices[name] = row

for name, before_row in affected_devices.items():
    row = current_devices.get(name)
    if row is None:
        verification_errors.append(f"{name}: missing current result")
        continue
    try:
        before_time = datetime.strptime(before_row.get("Checked At", ""), "%Y-%m-%d %H:%M:%S")
        checked_time = datetime.strptime(row.get("Checked At", ""), "%Y-%m-%d %H:%M:%S")
        if checked_time <= before_time:
            raise ValueError("current check must be newer than the incident check")
        ip_address(row.get("Device Address", ""))
        if row.get("Ping Status", "") != "Reachable":
            raise ValueError("device is not confirmed reachable")

        dns_status = row.get("DNS Status", "").strip()
        if "Unauthorized DNS detected" in dns_status:
            raise ValueError("unauthorized DNS is still reported")

        if dns_status.startswith("/etc/resolv.conf:"):
            addresses = dns_status.split(":", 1)[1].replace(",", " ").split()
        elif dns_status.startswith(("Global:", "Link ")):
            addresses = []
            for section in dns_status.split(" | "):
                match = re.fullmatch(r"(?:Global|Link \d+ \([^)]+\)):\s*(.*)", section)
                if not match:
                    raise ValueError("unrecognized DNS verification output")
                addresses.extend(match.group(1).split())
        else:
            raise ValueError("DNS verification unavailable or failed")

        servers = {str(ip_address(address)) for address in addresses}
        allowed_servers = APPROVED_DNS_SERVERS.copy()
        if name in {"DNS1", "DNS2"}:
            allowed_servers.add("127.0.0.1")
        if not servers or not servers.issubset(allowed_servers):
            raise ValueError("DNS addresses are missing or not approved")
    except ValueError as error:
        verification_errors.append(f"{name}: {error}")
        continue

    resolved_devices.append({
        "name": name,
        "service": name,
        "ip": row["Device Address"],
        "last_checked": row["Checked At"],
        "dns_status": dns_status,
    })

if verification_errors:
    print("Resolution email not sent: verification incomplete.")
    for error in verification_errors:
        print(f"- {error}")
    raise SystemExit(1)


print("\n" + "-" * 80)
print("RESOLUTION NOTIFICATION EMAIL")
print(f"SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
print("-" * 80)
print(f"From:   {SENDER}")
print(f"To:     {RECIPIENT}")
print(f"Subject: {SUBJECT}")
print(f"Prepared at: {timestamp_str}")
print("-" * 80)

if not resolved_devices:
    print("\n No devices resolved.")
    print("   No resolution email is needed.")
else:
    body = """Dear Stakeholders,

This is an automated notification to inform you that the DNS service issue and all related device compromises have been successfully resolved. The following devices were affected and have now been remediated:

"""

    for device in resolved_devices:
        body += f"""Device Name: {device['name']}
IP Address: {device['ip']}
Service: {device['service']}
DNS Finding: {device['dns_status']}
Last Checked: {device['last_checked']}

"""

    body +="""No further action is required at this time. If you have any questions or concerns, please contact the IT support team.

    Thank you for your attention.

Best regards,  
Network Monitoring System """

    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = RECIPIENT
    msg['Subject'] = SUBJECT
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.sendmail(SENDER, [RECIPIENT], msg.as_string())

        email_sent = True
        send_status = "Resolution Email sent successfully"

    except Exception as error:
        email_sent = False
        send_status = f"Resolution Email failed: {error}" 

    
    print(f"Send Status: {send_status}")
    print("\nEMAIL BODY:")
    print("-" * 80)
    print(body)
    print("-" * 80)

if resolved_devices:
    print("\nResolved devices:")
    for device in resolved_devices:
        print(f"- {device['name']} | {device['ip']} | Service: {device['service']} | {device['dns_status']}")
