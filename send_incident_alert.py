import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SUBJECT = "URGENT: Device Compromise Detected-Immediate Attention Required"
SENDER = "network.monitoring@lantzops.com"
RECIPIENT = "stakeholders@lantzops.com"


now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

affected_devices = []

with open("device_status_results.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        ping_status = row.get("Ping Status", "")

        if ping_status in ["Timeout", "Unreachable"]:
            affected_devices.append({
                "name":    row.get("Device Name"),
                "service": row.get("Device Name"),
                "ip": row.get("Device Address"),
                "last_checked": row.get("Checked At")
                })

body = """Dear Stakeholders,

This is an automated alert to inform you that the following device(s) have been
identified as compromised during a recent network scan:

"""

for device in affected_devices:
    body += f"""Name: {device['name']}
IP Address: {device['ip']}
Service: {device['service']}
Last Checked: {device['last_checked']}

"""

body +="""Immediate investigation and remediation are recommended to prevent further impact.
If you have any questions or require additional information, please contact the IT support team.

Best regards,
Network Monitoring System"""

msg = MIMEMultipart()
msg['From'] = SENDER
msg['To'] = RECIPIENT
msg['Subject'] = SUBJECT
msg.attach(MIMEText(body, 'plain'))

print("\n" + "-" * 80)
print("INCIDENT ALERT EMAIL")
print("-" * 80)
print(f"From:   {SENDER}")
print(f"To:     {RECIPIENT}")
print(f"Subject:{SUBJECT}")
print(f"Sent at (Simulated):{timestamp_str}")
print("-" * 80)
print(body)
print("-" * 80)
