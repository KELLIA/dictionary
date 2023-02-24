# Updates dictionary DB with all information from a fresh scriptorium release
import os, sys
from argparse import ArgumentParser

p = ArgumentParser()
p.add_argument("--tasks",choices=["read","phrases","lemmas","colloc","examples"],nargs="+",default=["read","phrases","lemmas","colloc","examples"])

opts = p.parse_args()

script_dir = os.path.realpath(os.path.dirname(__file__)) + os.sep
xml_dir = script_dir + ".." + os.sep + "xml" + os.sep

# Step 1 - build phrase table for transitions info
if "phrases" in opts.tasks:
    sys.stderr.write("o Building phrase table (it will only be imported on XML read; this will take a little while)\n")
    from get_phrases import write_phrase_table
    write_phrase_table()

# Step 2 - read lexicon data from XML files (also imports phrase table)
if "read" in opts.tasks or "phrases" in opts.tasks:
    sys.stderr.write("o Getting lexicon XML entries and reading phrases\n")
    from dictionary_reader import dictionary_xml_to_database
    dictionary_xml_to_database(xml_dir)

# Step 3 - make lemma table with collocations
if "lemmas" in opts.tasks or "colloc" in opts.tasks:
    sys.stderr.write("o Getting inflected lemma lookup and collocation info\n")
    from make_lemma_table import main as make_lemmas
    make_lemmas()

# Step 4 - get example usages
if "examples" in opts.tasks:
    sys.stderr.write("o Getting example usages\n")
    from get_examples import main as write_examples
    write_examples()