import csv
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "http://10.10.10.200:5000/api/tickets"
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


affected_devices = []

with open("device_status_results.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        dns_status = row.get("DNS Status", "")

        if "Unauthorized DNS detected" in dns_status:
            affected_devices.append({
                "name": row.get("Device Name", ""),
                "ip": row.get("Device Address", ""),
                "service": row.get("Device Name", ""),
                "device_status": row.get("Ping Status", ""),
                "dns_finding": dns_status,
                "checked_at": row.get("Checked At", ""),
            })

if not affected_devices:
    print("No affected devices found. No tickets created.")
    raise SystemExit(0)

for device in affected_devices:
    payload = {
        "title": f"Unauthorized DNS configuration detected on {device['name']}",
        "status": "open",
        "issue_type": "Unauthorized DNS configuration",
        "device_name": device["name"],
        "device_address": device["ip"],
        "service": device["service"],
        "device_status": device["device_status"],
        "dns_finding": device["dns_finding"],
        "checked_at": device["checked_at"],
        "created_at": created_at,
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
        print("-" * 80)

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        print(f"Ticket creation failed for {device['name']}")
        print(f"Response status: {error.code}")
        print("-" * 80)
        print(f"Response body: {error_body}")
       
    except urllib.error.URLError as error:
        print(f"Connection failed for {device['name']}: {error}")




