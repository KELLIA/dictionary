import os, io, glob, re, json
from collections import defaultdict

def get_entity_types(pub_corpora_dir=None):
    def get(attr, line):
        return re.search(' ' + attr + r'="([^"]*)"', line).group(1)

    all_pos = defaultdict(int)

    if pub_corpora_dir is None:
        pub_corpora_dir = "corpora"
    if not pub_corpora_dir.endswith(os.sep):
        pub_corpora_dir += os.sep
    tt_files = glob.glob(pub_corpora_dir + "**" + os.sep + "*.tt", recursive=True)
    entity_types = defaultdict(set)
    for file_ in tt_files:
        sgml = io.open(file_, encoding="utf8").read()
        if ' entities="gold"' not in sgml or "treebank" not in file_:
            continue  # Only use gold entities
        lines = sgml.split("\n")
        # Pass 1 - get head lemmas
        id2lemma = {}
        id2pos = {}
        for line in lines:
            if 'norm' in line and 'xml:id' in line:
                xml_id = get('xml:id', line)
                lemma = get('lemma', line)
                pos = get('pos', line)
                id2lemma[xml_id] = lemma
                id2pos[xml_id] = pos
        # Pass 2 - get entity types for each lemma
        for line in lines:
            if ' entity="' in line:
                ent_type = get('entity', line)
                head_id = get('head_tok', line).replace("#", "")
                lemma = id2lemma[head_id]
                pos = id2pos[head_id]
                entity_types[lemma].add(ent_type)
                all_pos[pos] +=1
    for pos in sorted(all_pos, key=all_pos.get, reverse=True):
        print(pos, all_pos[pos])
    return entity_types

def main():

    script_dir = os.path.dirname(__file__)

    entity_types = get_entity_types()

    # Turn all sets to lists for json
    entity_types = {lemma: sorted(list(entity_types[lemma])) for lemma in entity_types}

    # Dump to entities.json
    with io.open(script_dir + os.sep + "entities.json", "w", encoding="utf8") as f:
        json.dump(entity_types, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()