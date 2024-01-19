"""Merge together the `citation-contexts.csv` with the `all-data.one-hot.tsv` file to create the `citation-contexts-extended.csv`.

This uses the `chiir2024.all-scholar-IDs.tsv` to map the ids.

This script must be run in the directory containing all three files.
"""
from csv import DictReader, DictWriter

# Determine the result_id to DOI mappings needed to merge the `all-data.one-hot.tsv`
# into the `citation-contexts.cvs`.
id_mappings = {}
with open("chiir2024.all-scholar-IDs.tsv") as in_f:
    reader = DictReader(in_f, delimiter="\t")
    for line in reader:
        id_mappings[line["result_id"]] = line["doi"]

# Load the `all-data.one-hot.tsv` file into a DOI indexed dict.
all_data = {}
all_data_fieldnames = []
with open("all-data.one-hot.tsv") as in_f:
    reader = DictReader(in_f, delimiter="\t")
    all_data_fieldnames = reader.fieldnames
    for line in reader:
        all_data[line["DOI"]] = line

DROP_FIELDNAMES=["zotero_ID", "DOI", "authors", "title", "pages", "codes", "keywords", "abstract"]
dropped = 0
with open("citation-contexts.csv") as in_f:
    with open("citation-contexts-merged.csv", "w") as out_f:
        reader = DictReader(in_f)
        writer = DictWriter(out_f, fieldnames=reader.fieldnames + [fn for fn in all_data_fieldnames if fn not in DROP_FIELDNAMES])
        writer.writeheader()
        for line in reader:
            annotated = False
            for category in ["background", "uses_data", "uses_design", "uses_infrastructure", "similarities", "differences", "disagreement", "motivation", "extension", "future_work"]:
                if line[category] == "1":
                     annotated = True
                     break
            if annotated:
                if id_mappings[line["cited_id"]] in all_data:
                    for key, value in all_data[id_mappings[line["cited_id"]]].items():
                        if key not in DROP_FIELDNAMES:
                            line[key] = value
                    writer.writerow(line)
                else:
                    print(line["cited_id"], id_mappings[line["cited_id"]])
                    dropped = dropped + 1

print(f"Dropped {dropped} contexts")


with open("citation-contexts.csv") as in_f:
    with open("citation-contexts-extended.csv", "w") as out_f:
        reader = DictReader(in_f)
        writer = DictWriter(out_f, fieldnames=reader.fieldnames + ["type", "year", "design__type__resource_paper", "design__type__experimental", "design__type__theoretical"])
        writer.writeheader()
        for line in reader:
            line["type"] = all_data[id_mappings[line["cited_id"]]]["type"]
            line["year"] = all_data[id_mappings[line["cited_id"]]]["year"]
            line["design__type__resource_paper"] = all_data[id_mappings[line["cited_id"]]]["design__type__resource_paper"]
            line["design__type__experimental"] = all_data[id_mappings[line["cited_id"]]]["design__type__experimental"]
            line["design__type__theoretical"] = all_data[id_mappings[line["cited_id"]]]["design__type__theoretical"]
            writer.writerow(line)
