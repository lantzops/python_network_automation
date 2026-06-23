import csv

with open("network_devices.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        print(row["Device Name"])



