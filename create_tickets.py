import csv
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

## API_URL =
TOKEN_ENV_VAR = "HELPDESK_API_TOKEN"

api_token = os.environ.get(TOKEN_ENV_VAR)
created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if not api_token:
    print(f"Missing API token, Set it with: export {TOKEN_ENV_VAR}=<token>")
    raise SystemExit(1)

print("Ticket Creation Results")
print(f"API endpoint: {API_URL}")
print(f"Created at: {created_at}")
print("-" * 80)


devices = []

with open("device_status_results.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        dns_status = row.get("DNS Status", "")

        devices.append({
            "name": row.get("Device Name", ""),
            "ip": row.get("Device Address", ""),
            "service": row.get("Device Name", ""),
            "device_status": row.get("Ping Status", ""),
            "dns_finding": dns_status,
            "checked_at": row.get("Checked At", ""),
        })

if not devices:
    print("No device results found. No tickets created.")
    raise SystemExit(0)

for device in devices:
    if "Unauthorized DNS detected" in device["dns_finding"]:
        issue_type = "Unauthorized DNS configuration"
    else:
        issue_type = "Device verification review"

    description = (
        f"Issue type: {issue_type}\n"
        f"Device: {device['name']}\n"
        f"IP address: {device['ip']}\n"
        f"Service: {device['service']}\n"
        f"Device status: {device['device_status']}\n"
        f"DNS finding: {device['dns_finding']}\n"
        f"Checked at: {device['checked_at']}"
    )

    payload = {
        "title": f"{issue_type}: {device['name']}",
        "status": "open",
        "description": description,
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
            API_URL,
            data=payload_bytes,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_status = response.status
            response_body = response.read().decode("utf-8")
            response_data = json.loads(response_body)

        print(f"Created ticket for {device['name']}")
        print(f"Response status: {response_status}")
        print(f"Ticket ID: {response_data.get('id')}")
        print(f"Ticket status: {response_data.get('status')}")
        print(f"Ticket title: {response_data.get('title')}")
        print(f"Ticket description: {response_data.get('description')}")
        print("-" * 80)

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        print(f"Ticket creation failed for {device['name']}")
        print(f"Response status: {error.code}")
        print("-" * 80)
        print(f"Response body: {error_body}")
       
    except urllib.error.URLError as error:
        print(f"Connection failed for {device['name']}: {error}")



