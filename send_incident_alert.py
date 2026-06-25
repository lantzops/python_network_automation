import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


SMTP_HOST= "10.10.10.100"
SMTP_PORT= 1025
SUBJECT = "URGENT: Device Compromise Detected - Immediate Attention Required"
SENDER = "network.monitoring@lantzops.com"
RECIPIENT = "stakeholders@lantzops.com"


now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

affected_devices = []

with open("device_status_results.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        dns_status = row.get("DNS Status", "")

        if "Unauthorized DNS detected" in dns_status:
            affected_devices.append({
                "name":    row.get("Device Name"),
                "service": row.get("Device Name"),
                "ip": row.get("Device Address"),
                "last_checked": row.get("Checked At"),
                "dns_status": row.get("DNS Status")
                })


print("\n" + "-" * 80)
print("INCIDENT ALERT EMAIL")
print(f"SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
print("-" * 80)
print(f"From:   {SENDER}")
print(f"To:     {RECIPIENT}")
print(f"Subject: {SUBJECT}")
print(f"Sent at: {timestamp_str}")
print("-" * 80)

if not affected_devices:
    print("\n No affected devices found.")
    print("   No alert email is needed.")
else:
    body = """Dear Stakeholders,

This is an automated alert to inform you that the following device(s) have been
identified as compromised during a recent network scan:

"""

    for device in affected_devices:
        body += f"""Device Name: {device['name']}
IP Address: {device['ip']}
Service: {device['service']}
DNS Finding: {device['dns_status']}
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

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.sendmail(SENDER, [RECIPIENT], msg.as_string())

        email_sent = True
        send_status = "Email alert sent successfully"

    except Exception as error:
        email_sent = False
        send_status = f"Email alert failed: {error}" 

    
    print(f"Send Status: {send_status}")
    print("\nEMAIL BODY:")
    print("-" * 80)
    print(body)
    print("-" * 80)

if affected_devices:
    print("\nAffected devices:")
    for device in affected_devices:
        print(f"- {device['name']} | {device['ip']} | Service: {device['service']} | {device['dns_status']}")

