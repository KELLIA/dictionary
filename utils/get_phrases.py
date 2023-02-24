from collections import defaultdict
from glob import glob
from depedit import DepEdit
import io

white_list = ["N","V","VSTAT","VIMP","PREP"]

deped_conf = """text=/.*/;text=/.*/;func=/cop|case|mark/\t#1>#2>#3\t#1>#3;#3>#2
func=/root/;func=/cop|case|mark|det/\t#1>#2\t#2:head=0
func=/case/;text=/.*/;func=/det/\t#1>#2>#3\t#1>#3;#3>#2"""

class Token:

    def __init__(self, tid, word, pos, func):
        self.id = tid
        self.word = word
        self.pos = pos
        self.func = func
        self.span = []
        self.parent = ""

def conll2phrases(conllu):
    def get_descendents(tid,children,descendents,rank=1):
        if rank > 10:
            return descendents
        for child in children[tid]:
            descendents.add((int(child),rank))
            descendents.update(get_descendents(child,children,descendents,rank=rank+1))
        return descendents

    sents = conllu.strip().split("\n\n")
    phrases = defaultdict(lambda : defaultdict( lambda : defaultdict(int)))

    for sent in sents:
        children = defaultdict(list)
        lines = sent.split("\n")
        sent_toks = {}
        for line in lines:
            if "\t" in line:
                fields = line.split("\t")
                if "-" in fields[0]:
                    continue
                word = fields[1]
                xpos = fields[4]
                head = fields[6]
                tid = fields[0]
                func = fields[7]
                children[head].append(tid)
                sent_toks[tid] = Token(tid,word,xpos,func)

        for tid in children:
            if int(tid) != 0:
                for child in children[tid]:
                    if tid in sent_toks:
                        sent_toks[child].parent = sent_toks[tid].word
                    else:
                        a=3  # This should never happen

        for tid, tok in sent_toks.items():
            if tok.pos in white_list:
                tok.span = sorted(list(get_descendents(tok.id,children,set([])))+[(int(tid),0)])
                phrase = []
                seen = set([])
                for d_id, rank in tok.span:
                    descendent = sent_toks[str(d_id)]
                    if descendent.pos == "PUNCT":
                        continue

                    affix = "node" if rank == 0 else "pre"
                    if d_id > int(tok.id):
                        affix="post"
                    unique_word = descendent.word + "_" + str(rank) + "_"+affix
                    if rank!=0:
                        unique_word += "_" + descendent.parent
                    if unique_word in seen:
                        unique_word += "_b"
                    seen.add(unique_word)
                    phrase.append(unique_word)
                phrases[tok.pos][tok.word][" ".join(phrase)] += 1

    return phrases

def write_phrase_table():

    pub_corpora = "pub_corpora" + os.sep
    files = glob(pub_corpora + "**" +os.sep + "*.conllu",recursive=True)

    d = DepEdit(config_file=deped_conf.strip().split("\n"))

    all_phrases = defaultdict(lambda : defaultdict( lambda : defaultdict(int)))
    for file_ in files:
        conllu = io.open(file_,encoding="utf8").read()
        conllu = d.run_depedit(conllu)
        updates = conll2phrases(conllu)
        for pos in updates:
            for word in updates[pos]:
                for phrase in updates[pos][word]:
                    all_phrases[pos][word][phrase] += updates[pos][word][phrase]

    output = []
    for pos in all_phrases:
        for word in all_phrases[pos]:
            for phrase in all_phrases[pos][word]:
                freq = all_phrases[pos][word][phrase]
                output.append("\t".join([pos, word, phrase, str(freq)]))

    with io.open("phrase_freqs.tab",'w',encoding="utf8",newline="\n") as f:
        f.write("\n".join(output)+ "\n")

if __name__ == "__main__":
    write_phrase_table()