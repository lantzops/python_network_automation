# Python Network Automation

A Python-based network automation project for connecting to Cisco IOS devices, collecting device information, and exporting the results into a structured CSV report.

This project began as part of my network engineering coursework and is being developed further as a practical way to apply Python automation to my Cisco and infrastructure lab environments.

## Current Features

The current version of the project:

- Connects to multiple Cisco IOS devices over SSH using Netmiko
- Executes Cisco IOS `show` commands
- Collects device information including:
  - Hostname
  - Hardware model
  - IOS version
  - Serial number
- Parses command-line output into usable values
- Exports collected information to `device_info.csv`
- Reports successful and failed device connections
- Disconnects SSH sessions after data collection
- Uses `getpass` to avoid storing the device password directly in the script

## Technologies

- Python 3
- Netmiko
- Cisco IOS
- SSH
- CSV
- Linux / virtual lab infrastructure

## Example Workflow

```text
Cisco Device
     |
     | SSH
     v
  Netmiko
     |
     | IOS show commands
     v
Python Script
     |
     | Parse device information
     v
device_info.csv
```

Example console output:

```text
Enter device password:

[+] Collected info from R1
[+] Collected info from R2
[+] Collected info from SW1
[+] Collected info from SW2

Data saved to device_info.csv
```

The resulting CSV can then be used as a simple device inventory:

```text
hostname,model,ios_version,serial_number
R1,ISR4331,16.12.04,FTX2449ABC1
R2,ISR4321,17.03.04,FOC3001XYZ8
SW1,C3560X,15.2(7)E3,FOC1234QWE5
SW2,C2960X,15.2(7)E1,FOC5678RTY9
```

## What I Learned

One of the most useful parts of this project has been moving beyond Python exercises and using Python to interact with actual network infrastructure.

Some of the key lessons have included:

- Establishing and managing SSH connections programmatically
- Using Netmiko to
