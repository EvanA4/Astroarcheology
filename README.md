# Astroarcheology

A collection of Python scripts to measure a correlation between tropical zodiac sign and occupation.

## How to Use

### Data Collection

First, data must be extracted. The study describing the database used in this project can be found [here](https://palaashbhargava.github.io/Bhargava_Notable_People.pdf). The actual CSV, however, can be downloaded [here](https://data.sciencespo.fr/api/access/datafile/4432?gbrecs=true). Place this CSV in the `scaper` directory.

Before scraping, one should understand `extractor.py`. It fetches the people found in the downloaded CSV from Wikidata, looking for anyone with a valid birthday and list of occupations. Because the downloaded CSV is so large, the extraction process has been divided into 10 windows. The Python script can be called directly like so:

```
"Usage: python extractor.py <input.csv> <output.csv> <window_number (1-10)>
```

However, the Wikidata servers can occasionally cause the script to error. To account for this, the Python script uses a checkpoint system for each batch it fetches. Simply re-calling the script will let the script start where it left off, should an error arise. `extractScript.bat` and `extractScript.sh` are example scripts which call this script repeatedly so the user does not need to monitor the device running it; the user should modify these scripts to extract the windows they need.

Once all of the windows have been collected, place all of their corresponding CSVs in a temporary directory. Then, call `merge.py` like so:

```
`Usage: python merge.py <csv dir>
```

This should result in a CSV containing all of the people extracted from the several CSVs. For this guide, this CSV shall be refered to as `masterList.csv`.

### Data Processing

Place `masterList.csv` in the `analyzer` directory. To preprocess the new, merged dataset, call `filter.py` in the following manner:

```
python filter.py <input csv> <output csv>
```

The output CSV file will have any occupations with fewer than sixty people removed. It will also sort the people in the database by birthdate, not by name (alphabetically).

Afterwards, compute the number of zodiac signs per occupation with `counts.py`. This follows the same usage as `filter.py`. Pass in the CSV file you had just computed with `filter.py`.

Finally, determine the Chi-squared p-value with `correlation.py`. Simply provide it the CSV file generated with `counts.py` like so:

```
python correlation.py <input csv>
```