import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from http.client import HTTPException

## API_URL = 
TOKEN_ENV_VAR = "HELPDESK_API_TOKEN"

def resolve_ticket(ticket_id):
    if type(ticket_id) is not int or ticket_id <= 0:
        print("Cannot resolve ticket: expected a positive integer ticket ID.")
        return False

    api_token = os.environ.get(TOKEN_ENV_VAR)

    if not api_token:
        print(f"Missing API token. Set it with: export {TOKEN_ENV_VAR}=<token>")
        return False

    print("\n" + "-" * 80)
    print("DNS INCIDENT TICKET UPDATE")
    print(f"Ticket ID: {ticket_id}")
    print("Requested status: resolved")
    print(f"Attempted at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("-" * 80)

    payload = {
        "status": "resolved",
    }
    request = urllib.request.Request(
        f"{API_URL}/{ticket_id}",
        data=json.dumps(payload).encode("utf-8"),
        method="PATCH",
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
        if not isinstance(response_data, dict):
            raise ValueError("Response was not a ticket object")

        if (
            response_status == 200
            and response_data.get("id") == ticket_id
            and response_data.get("status") == "resolved"
        ):
            print(f"Response status: {response_status}")
            print(f"Ticket ID: {response_data.get('id')}")
            print(f"Ticket status: {response_data.get('status')}")
            print(f"Ticket title: {response_data.get('title')}")
            print(f"Updated at: {response_data.get('updated_at')}")
            print(f"Ticket {ticket_id} confirmed resolved.")
            print("-" * 80)
            return True

        print(f"Could not confirm resolution of ticket {ticket_id}.")
        print(f"Response status: {response_status}")
        print(f"Returned ticket ID: {response_data.get('id')}")
        print(f"Returned ticket status: {response_data.get('status')}")
        return False

    except urllib.error.HTTPError as error:
        try:
            error_body = error.read().decode("utf-8", errors="replace")
        finally:
            error.close()
        print(f"Ticket update failed for {ticket_id}")
        print(f"Response status: {error.code}")
        print(f"Response body: {error_body}")
    except (urllib.error.URLError, OSError, HTTPException) as error:
        print(f"Could not confirm resolution of ticket {ticket_id}: {error}")
        print("Check the ticket status before retrying.")
    except ValueError as error:
        print(f"Could not confirm resolution of ticket {ticket_id}: {error}")
        print("Check ticket status before retrying")

    return False



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

