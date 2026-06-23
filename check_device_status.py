import csv
import subprocess
import platform 
from datetime import datetime




with open("network_devices.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        subprocess.run( ping -c 1 (row["Device Address"]))





