import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


SMTP_HOST= "10.10.10.100"
SMTP_PORT= 1025
SUBJECT = "RESOLVED: DNS Service Issue and Device Compromise--All Issues Remediated"
SENDER = "network.monitoring@lantzops.com"
RECIPIENT = "stakeholders@lantzops.com"
RESOLVED_DEVICE_NAMES = ["SVR1", "SVR2"]


now = datetime.now()
timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

resolved_devices = []

with open("device_status_results.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        resolved_device_status = row.get("Device Name", "")

        if resolved_device_status in RESOLVED_DEVICE_NAMES:
            resolved_devices.append({
                "name":    row.get("Device Name"),
                "service": row.get("Device Name"),
                "ip": row.get("Device Address"),
                "last_checked": row.get("Checked At"),
                "dns_status": row.get("DNS Status")
                })


print("\n" + "-" * 80)
print("RESOLUTION NOTIFICATION EMAIL")
print(f"SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
print("-" * 80)
print(f"From:   {SENDER}")
print(f"To:     {RECIPIENT}")
print(f"Subject: {SUBJECT}")
print(f"Sent at: {timestamp_str}")
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

