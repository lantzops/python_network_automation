from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


SMTP_HOST = "10.10.10.100"
SMTP_PORT = 1025
SENDER = "network.monitoring@lantzops.com"
RECIPIENT = "stakeholders@lantzops.com"
APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20", "127.0.0.1"}



def send_dns_altered_email(device):
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    name = device["Device Name"]
    address = device["Device Address"]
    checked_at = device["Checked At"]
    subject = f"DNS Configuration Alert: {name} ({address})"

    print("\n" + "-" * 80)
    print("DNS ALTERED NOTIFICATION")
    print(f"SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
    print("-" * 80)
    print(f"From:   {SENDER}")
    print(f"To:     {RECIPIENT}")
    print(f"Subject: {subject}")
    print(f"Attempted at: {timestamp_str}")
    print("-" * 80)

    body = f"""Dear Network Administrator,

This is an automated alert that the DNS configuration for the following device has been altered from the expected settings:

Device Name: {name}
IP Address: {address}
Detected DNS Setting: {device["DNS Status"]}
Expected DNS Setting: {', '.join(sorted(APPROVED_DNS_SERVERS))}
Time Detected: {checked_at}

The system will attempt to automatically correct this configuration.

Best regards,
Network Monitoring System
"""

    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # None means delivery is uncertain; the monitor must not retry automatically.
    email_sent = False
    send_started = False
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            send_started = True
            smtp.sendmail(SENDER, [RECIPIENT], msg.as_string())
            email_sent = True

        send_status = "SMTP server accepted the email alert"

    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused,
            smtplib.SMTPDataError, smtplib.SMTPNotSupportedError) as error:
        email_sent = False
        send_status = f"SMTP rejected the email attempt: {error}"
    except (smtplib.SMTPException, OSError) as error:
        if email_sent:
            send_status = f"SMTP accepted the email; connection cleanup failed: {error}"
        elif send_started:
            email_sent = None
            send_status = f"Delivery uncertain; check MailHog before retrying: {error}"
        else:
            send_status = f"Email connection failed before sending: {error}"

    print(f"Send Status: {send_status}")
    print("\nEMAIL BODY:")
    print("-" * 80)
    print(body)
    print("-" * 80)
    return email_sent

   
