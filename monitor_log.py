




HEALTHY_DNS_LOG = "healthy_dns.txt"


def log_healthy_dns(device):
    if (
        device.get("Ping Status") != "Reachable"
        or device.get("DNS Check Status") != "approved"
        or device.get("DNS Resolution Verified") is not True
    ):
        return False

    try:
        entry = (
            f"{device['Checked At']} | {device['Device Name']} | "
            f"{device['Device Address']} | DNS resolution successful; "
            "configuration approved\n"
        )
        with open(HEALTHY_DNS_LOG, "a", encoding="utf-8") as logfile:
            logfile.write(entry)
    except (OSError, KeyError) as error:
        print(f"Could not write healthy-DNS log entry: {error}")
        return False

    print(f"Healthy DNS logged for {device['Device Name']}: {HEALTHY_DNS_LOG}")
    return True
