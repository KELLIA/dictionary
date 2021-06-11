import io, sys, os, re
from glob import glob
from collections import defaultdict
from zipfile import ZipFile
from copy import deepcopy

pub_corpora = ""  # Path to clone of CopticScriptorium/Corpora
if not pub_corpora.endswith(os.sep):
    pub_corpora += os.sep


def extract_collocs(lines,unit="norm",window=5):

    collocs = defaultdict(int)
    items = []
    for line in lines:
        if ' ' + unit + '=' in line:
            item = re.search(r' '+unit+'="([^"]*)"',line).group(1)
            if len(item) == 0:
                continue
            items.append(item)

    # Get right neighbors
    for i, item in enumerate(items[window:-window]):
        sequence = items[i:i+window]
        for neighbor in sequence[1:]:
            collocs[(sequence[0],neighbor)] +=1

    return collocs


def compile_colloc_table():
    pub = pub_corpora

    all_collocs = defaultdict(int)

    all_files = glob(pub + "**"+os.sep +"*.tt",recursive=True)
    all_files += glob(pub + "**"+os.sep +"*.zip",recursive=True)

    for file_ in all_files:
        if file_.endswith(".zip"):
            zip = ZipFile(file_)
            zipped_files = [f for f in zip.namelist() if f.endswith(".tt")]
            for zipped_file in zipped_files:
                lines = io.TextIOWrapper(zip.open(zipped_file), encoding="utf8").readlines()
                collocs = extract_collocs(lines,unit="norm",window=5)
                for tup, f in collocs.items():
                    all_collocs[tup] += f
        else:
            lines = io.open(file_, encoding="utf8").readlines()
            collocs = extract_collocs(lines, unit="norm", window=5)
            for tup, f in collocs.items():
                all_collocs[tup] += f

    # Get left neighbors:
    temp_collocs = deepcopy(all_collocs)
    for w1, w2 in temp_collocs:
        all_collocs[(w2,w1)] += all_collocs[(w1,w2)]

    output = []
    for tup, freq in all_collocs.items():
        output.append("\t".join([tup[0],tup[1],str(freq)]))

    return "\n".join(output) + "\n"


if __name__ == "__main__":
    table = compile_colloc_table()
    with io.open("tt_collocs.tab",'w',encoding="utf8",newline="\n") as f:
        f.write(table)

