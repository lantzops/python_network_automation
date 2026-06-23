import csv

count = 0
print("Network Device List \n----------------------")

with open("network_devices.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row["Device Name"])
        count += 1

print(f"Total Number of Devices = {count}")


