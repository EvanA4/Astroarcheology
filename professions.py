import os

merged = open(os.path.join("extracted", "merged.csv"), "r", encoding="latin-1")

professions = set()

line = merged.readline()
ctr = 0
while True:
    line = merged.readline().strip()
    if len(line) == 0: break
    temps = line.split(";")[3].split(",")
    for temp in temps:
        professions.add(temp.lower())
    ctr += 1
merged.close()

output = open("professions.txt", "w", encoding="latin-1")
for profession in professions:
    output.write(profession + "\n")
output.close()