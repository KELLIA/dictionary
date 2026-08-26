from collections import defaultdict

nlp_dir = "Coptic-NLP/"  # Path to Coptic-NLP repo

covered = set(open("../data/covered_base_forms.tab").read().split("\n"))

orig_chars = ["̈", "", "̄", "̀", "̣", "`", "̅", "̈", "̂", "︤", "︥", "︦", "⳿", "~", "\n", "[", "]", "̇", "᷍", "⸍", "›", "‹"]
forbidden_chars = ".,;:ⲻ()[]{}<>·˽/\\`~!@#$%^&*+=?\"'Ⲻⲻ·⳾- "

norm_files = ["data.b/norm_table.tab","data/norm_table.tab"]
lex_files = ["data.b/copt_lemma_lex.tab","data/copt_lemma_lex.tab"]

mapping = {}

# Sahidic will overwrite Bohairic normalization since Bohairic file is first
for norm_file in norm_files:
    for line in open(nlp_dir + norm_file, "r", encoding="utf-8").read().strip().split("\n"):
        if "\t" in line:
            orig, norm = line.split("\t")
            if "_" in norm:
                continue
            if any(char in orig for char in forbidden_chars):
                continue
            orig = "".join([c for c in orig if c not in orig_chars]).lower()
            if orig != norm and len(orig) > 0:
                mapping[orig] = norm

# word to lemma mapping will overwrite normalization mapping (more valuable)
for lex_file in lex_files:
    for line in open(nlp_dir + lex_file, "r", encoding="utf-8").read().strip().split("\n"):
        if "\t" in line:
            word, pos, lemma = line.split("\t")
            if "_" in lemma:
                continue
            if any(char in word for char in forbidden_chars):
                continue
            word = "".join([c for c in word if c not in orig_chars]).lower()
            if len(word) > 0 and word != lemma:
                mapping[word] = lemma

output = set()
for entry in mapping:
    if entry not in covered:
        output.add(entry + "\t" + mapping[entry])

output = sorted(list(output))

with open("../public/vide.tab", 'w', encoding="utf-8", newline="\n") as f:
    f.write("\n".join(output))