from collections import defaultdict

nlp_dir = "Coptic-NLP/"  # Path to Coptic-NLP repo

files = ["data/segmentation_table.tab","data/morph_table.tab","data.b/segmentation_table.tab","data.b/morph_table.tab"]

covered = set(open("../data/covered_base_forms.tab").read().split("\n"))

freqs = defaultdict(lambda: defaultdict(int))

for file in files:
    with open(nlp_dir + file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                key, value = parts
                freqs[key][value] += 1

output = set()

for key, value_counts in freqs.items():
    # Find the most common value for this key
    most_common_value = max(value_counts, key=value_counts.get)
    # Only include it if it contains "|"
    if "|" in most_common_value and key not in covered:
        output.add((key, most_common_value))

forbidden_chars = ".,;:ⲻ()[]{}<>·˽/\\`~!@#$%^&*+=?\"'"

with open("../public/seg_data.tab", "w", encoding="utf-8") as f:
    for key, value in sorted(output):
        if not any(char in value for char in forbidden_chars):
            f.write(f"{value}\n")