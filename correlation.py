import pandas as pd
import os
from zodiac import ZODIAC_SIGNS

df = pd.read_csv(os.path.join("output", "professions.csv"))
print("Original shape:", df.shape)

for sign in ZODIAC_SIGNS:
    df = df[df[sign] >= 5]

print("Filtered shape:", df.shape)
df.to_csv(os.path.join("output", "filtered.csv"), index=False)