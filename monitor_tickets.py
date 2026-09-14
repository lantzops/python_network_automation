import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from http.client import HTTPException

API_URL = "http://helpdesk.d522.wgu.internal:5000/api/tickets"
TOKEN_ENV_VAR = "HELPDESK_API_TOKEN"


def create_ticket(device, issue_type):
    api_token = os.environ.get(TOKEN_ENV_VAR)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not api_token:
        print(f"Missing API token. Set it with: export {TOKEN_ENV_VAR}=<token>")
        return None

    print("Ticket Creation Results")
    print(f"API endpoint: {API_URL}")
    print(f"Created at: {created_at}")
    print("-" * 80)

    description = (
        f"Issue type: {issue_type}\n"
        f"Device: {device['Device Name']}\n"
        f"IP address: {device['Device Address']}\n"
        f"Device status: {device['Ping Status']}\n"
        f"DNS finding: {device['DNS Status']}\n"
        f"Checked at: {device['Checked At']}"
    )
    payload = {
        "title": f"{issue_type}: {device['Device Name']}",
        "status": "open",
        "description": description,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
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
        if not isinstance(response_data, dict) or not response_data.get("id"):
            raise ValueError("Response did not contain a ticket ID")

        ticket_id = response_data["id"]
        print(f"Created ticket for {device['Device Name']}")
        print(f"Response status: {response_status}")
        print(f"Ticket ID: {ticket_id}")
        print(f"Ticket status: {response_data.get('status')}")
        print(f"Ticket title: {response_data.get('title')}")
        print(f"Ticket description: {response_data.get('description')}")
        print("-" * 80)
        return ticket_id

    except urllib.error.HTTPError as error:
        try:
            error_body = error.read().decode("utf-8", errors="replace")
        finally:
            error.close()
        print(f"Ticket creation failed for {device['Device Name']}")
        print(f"Response status: {error.code}")
        print(f"Response body: {error_body}")
    except (urllib.error.URLError, OSError, HTTPException) as error:
        print(f"Connection failed for {device['Device Name']}: {error}")
        print("Check the helpdesk before retrying; a ticket may already exist.")
    except ValueError as error:
        print(f"Could not confirm ticket creation for {device['Device Name']}: {error}")
        print("Check the helpdesk before retrying; a ticket may already exist.")

    return None


