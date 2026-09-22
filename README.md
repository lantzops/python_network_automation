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

Establishing and managing SSH connections programmatically

Using Netmiko to interact with Cisco IOS

Executing commands and processing returned CLI output

Turning unstructured command output into structured data

Working with CSV files in Python

Handling connection failures without terminating the entire collection process

Recognizing the limitations of parsing CLI output based on assumptions about its format

Thinking about network administration tasks as repeatable automation workflows rather than individual commands

The debugging process was particularly useful. Problems with command syntax, output parsing, CSV formatting, and connection handling demonstrated how quickly assumptions that work for one device or output format can become problems when automation is applied across multiple systems.

Current Status

This project is a work in progress.

The core workflow currently works:

Connect -> Execute -> Parse -> Export

The next stage is to make the project less like a single-purpose script and more like a reusable network automation tool.

Planned Improvements

Future development will include:

Interface and IP address collection

Improved exception handling

Structured logging

More robust IOS output parsing

Moving device inventory/configuration outside the Python source

A reusable CLI or menu-driven interface

Additional network health and inventory information

Ansible integration

Better credential management

Documentation and testing across a larger virtual network

As I progress through CCNA and Cisco-focused network engineering coursework, I plan to continue integrating concepts from those studies into the project.

Longer-Term Goal

The goal is to integrate this project into my own network and infrastructure lab rather than leave it as a completed coursework assignment.

That environment gives me a place to experiment with combining:

Cisco networking + Linux + Python + Ansible + infrastructure automation

The project will continue evolving as I learn more about network engineering and identify repetitive infrastructure tasks that can be automated.

Security

Credentials should not be committed to the repository.

The current implementation prompts for the device password at runtime using Python's getpass module. Future versions will explore more scalable approaches to credential and secrets management.

Any device addresses, usernames, credentials, or configuration examples published in this repository should be treated as lab/example data rather than production credentials.

Project Status

🚧 Active Development

This repository represents an ongoing learning and development project. Features, structure, and implementation will change as the project expands.
