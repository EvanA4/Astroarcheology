import pandas as pd
import os
from zodiac import ZODIAC_SIGNS
from scipy.stats import chi2_contingency


# filter professions CSV for rows with at least five people of each zodiac sign
if not os.path.exists(os.path.join("output", "filtered.csv")):
    df = pd.read_csv(os.path.join("output", "professions.csv"))
    print("Original shape:", df.shape)

    for sign in ZODIAC_SIGNS:
        df = df[df[sign] >= 5]

    print("Filtered shape:", df.shape)
    df.to_csv(os.path.join("output", "filtered.csv"), index=False)


df = pd.read_csv(os.path.join("output", "filtered.csv"))
table = df.set_index("profession").select_dtypes(include="number")
chi_square, p_value, degrees_of_freedom, expected = chi2_contingency(
    table,
    correction=False,
)

print(f"Chi-square: {chi_square:.3f}")
print(f"Degrees of freedom: {degrees_of_freedom}")
print(f"p-value: {p_value:.6g}")