prof_file = open("professions.txt", "r", encoding="latin-1")
profs = [x.strip() for x in prof_file.readlines()]
prof_file.close()

print(f"Original length: {len(profs)}")

def is_only_letters_and_spaces(prof: str) -> bool:
    if not prof.isascii(): return False
    for char in prof:
        if not char.isalpha() and not char == " ":
            return False
    return True

profs = [x for x in profs if is_only_letters_and_spaces(x)]
print(f"Only letters and spaces length: {len(profs)}")

profs = [x for x in profs if not x.startswith("http")]
print(f"No site length: {len(profs)}")

profs = [x for x in profs if len(x.split(" ")) <= 3]
print(f"No 4+ word length: {len(profs)}")

output = open("filtered-profs.txt", "w")
for profession in profs:
    output.write(profession + "\n")
output.close()