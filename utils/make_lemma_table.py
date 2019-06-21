#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script takes a tagged lemma table and an ANNIS url with a corpus list
to collect:
 1. A list of lemmas to look up inflected word forms
 2. Frequencies from ANNIS corpora for each lemma and word form
"""

from argparse import ArgumentParser
import re, sys, os, requests, io
from collections import defaultdict
from itertools import groupby
from math import log
from six import iteritems

corpora = ["shenoute.eagerness", "shenoute.fox", "shenoute.a22", "shenoute.abraham", "shenoute.dirt",
		   "apophthegmata.patrum", "sahidica.nt", "sahidic.ot", "pseudo.theophilus", "martyrdom.victor",
		   "johannes.canons",
		   "besa.letters", "sahidica.mark", "sahidica.1corinthians", "doc.papyri"]


stop_list = ["ⲛ","ⲛⲁ","ⲡⲉ","ⲁ","ⲛⲧ","ⲓ","ϣⲁ","ⲉⲛⲧ"]

def read_lemmas(filename):
	"""

	:param filename: a tab delimited text file name, with three columns: word, pos, lemma
	:return: list of triples (word, pos, lemma)
	"""
	lines = io.open(filename,encoding="utf8").read().replace("\r","").split("\n")
	lemmas = []
	for line in lines:
		fields = line.split("\t")
		if len(fields) > 2:
			lemmas.append(fields[:3])
	return lemmas


def escape(query):
	query = query.replace("&", "%26").replace(" ", "%20").replace("#", "%23")
	return query


def tabulate(xml):
	lines = xml.replace("\r", "").replace("><", ">\n<").split("\n")
	item = ""
	count = 0
	counts = defaultdict(int)
	for line in lines:
		#line = line
		if "<entry>" in line:
			pass
		if "<tupel>" in line:  # the word form or lemma
			m = re.search(r'>([^<]*)<', line)
			item = m.group(1)
		elif "<count>" in line:
			m = re.search(r'>([^<]*)<', line)
			count = int(m.group(1))
		elif "</entry>" in line:
			if len(item) > 0:
				counts[item] += count
	return counts


def tabulate_multiple(xml):
	lines = xml.replace("\r", "").replace("><", ">\n<").split("\n")
	items = []
	count = 0
	counts = defaultdict(int)
	for line in lines:
		#line = line
		if "<entry>" in line:
			pass
		if "<tupel>" in line:  # the word form or lemma
			m = re.search(r'>([^<]*)<', line)
			items.append(m.group(1))
		elif "<count>" in line:
			m = re.search(r'>([^<]*)<', line)
			count = int(m.group(1))
			item = "||".join(items)
			items = []
		elif "</entry>" in line:
			if len(item) > 0:
				counts[item] += count
	return counts


def get_freqs(url, corpora, use_cache=False):

	# TODO: remove duplicate data from sahidica.nt also in Mark and 1Cor
	#corpora = ["shenoute.fox"]

	sys.stderr.write("o Retrieving data from corpora:\n - " + "\n - ".join(sorted(corpora)) + "\n")

	corpora = "corpora=" + ",".join(corpora)

	queries = []
	# TODO: consider doing POS specific counts
	queries.append("q=norm")
	queries.append("q=lemma")

	fields = []
	fields.append("fields=1:norm")
	fields.append("fields=1:lemma")

	lemma_counts = []
	norm_counts = []
	counts = defaultdict(lambda: defaultdict(int))
	output = ""
	for index, query in enumerate(queries):
		sys.stderr.write("o Getting part " + str(index + 1) + " of query list...\n")

		if use_cache:
			sys.stderr.write("! Retrieving data from CACHE!\n")
			if index == 0:
				text_content = io.open("cache_freqs_norm.xml",encoding="utf8").read()
			else:
				text_content = io.open("cache_freqs_lemma.xml",encoding="utf8").read()

		else:
			field = fields[index]
			query = escape(query)
			params = "&".join([corpora, query, field])

			api_call = url + "annis-service/annis/query/search/frequency?"
			api_call += params
			resp = requests.get(api_call)
			text_content = resp.text
			#with io.open("cache_freqs.xml",'w',encoding="utf8") as f:
			#	f.write(text_content)
		if index == 0:
			counts = tabulate(text_content)
			norm_counts = counts
		else:
			counts = tabulate(text_content)
			lemma_counts = counts

	return norm_counts, lemma_counts


def add_rank(data):
	"""
	Adds the rank to a frequency list, with ties (i.e. 1st=100, 2nd=99, 2nd=99, 3rd=98...)

	:param data: Nested list in format: [[freq,word], [freq,word], ...]
	:return: Nested list in format: [[freq,word,rank], [freq,word,rank], ...]
	"""

	sorted_data = sorted(data, reverse=True)
	for rank, (_, grp) in enumerate(groupby(sorted_data, key=lambda xs: xs[0]), 1):
		for x in grp:
			x.append(rank)
	return data


def get_collocations(url, corpora):

	# TODO: remove duplicate data from sahidica.nt also in Mark and 1Cor
	#corpora = ["shenoute.fox"]

	sys.stderr.write("o Retrieving collocations from corpora:\n - " + "\n - ".join(sorted(corpora)) + "\n")

	corpora = "corpora=" + ",".join(corpora)

	# TODO: consider doing POS specific counts
	query = "q=lemma ^1,5 lemma"
	fields = "fields=1:lemma,2:lemma"

	node_freqs = defaultdict(int)
	collocate_freqs = defaultdict(lambda: defaultdict(int))

	sys.stderr.write("o Getting collocations...\n")
	query = escape(query)
	params = "&".join([corpora, query, fields])

	api_call = url + "annis-service/annis/query/search/frequency?"
	api_call += params
	resp = requests.get(api_call)
	text_content = resp.text
	counts = tabulate_multiple(text_content)

	return counts


def get_assoc(f_a, f_b, f_ab, N):
	# Currently using MI3

	E = (f_a * f_b)/float(N)
	return log(f_ab**3/E)


def update_db(row_list,table="lemmas"):
	import sqlite3 as lite
	con = lite.connect('alpha_kyima_rc1.db')

	with con:
		cur = con.cursor()

		if table == "lemmas":
			cur.execute("DROP TABLE IF EXISTS lemmas")
			cur.execute(
				"CREATE TABLE lemmas(word TEXT, pos TEXT, lemma TEXT, word_count TEXT, word_freq REAL, word_rank INT, " +
				"lemma_count TEXT, lemma_freq REAL, lemma_rank INT)")

			cur.executemany("INSERT INTO lemmas (word, pos, lemma, word_count, word_freq, word_rank, lemma_count, lemma_freq, lemma_rank) VALUES " +
							"(?, ?, ?, ?, ?, ?, ?, ?, ?);", row_list)
			con.commit()
		elif table == "collocates":
			cur.execute("DROP TABLE IF EXISTS collocates")
			cur.execute(
				"CREATE TABLE collocates(lemma TEXT, collocate TEXT, freq INT, assoc REAL)")

			cur.executemany(
				"INSERT INTO collocates (lemma, collocate, freq, assoc) VALUES " +
				"(?, ?, ?, ?);", row_list)
			con.commit()


parser = ArgumentParser()
parser.add_argument("-l","--lemma_list",action="store",dest="lemma_list",default="C:\\TreeTagger\\bin\\coptic\\copt_lemma_lex.tab")
parser.add_argument("-u","--url",action="store",dest="url",default="https://corpling.uis.georgetown.edu/")
parser.add_argument("-o","--outmode",action="store",dest="outmode",default="db")
parser.add_argument("-c","--use_cache",action="store_true",help="activate cache - read data from tt_collocs.tab and cache_freqs.xml")


options = parser.parse_args()

# Get collocation information
cooc_pool = 0
collocate_freqs = defaultdict(lambda: defaultdict(int))

# Check if cached file is available and create it if not
if not os.path.isfile("tt_collocs.tab") or not options.use_cache:
	sys.stderr.write('o Cache data unavailable - retrieving collocations from ANNIS\n')
	colloc_data = get_collocations(options.url,corpora)
	out_cache = []
	for key, val in iteritems(colloc_data):
		if "||" in key:
			w1, w2 = key.split("||")
			out_cache.append("\t".join([w1,w2,str(val)]))
	with io.open("tt_collocs.tab",'w',encoding="utf8",newline="\n") as f:
		f.write("\n".join(out_cache) +"\n")
else:
	sys.stderr.write('o Using cached tt_collocs.tab\n')

colloc_lines = io.open("tt_collocs.tab",encoding="utf8").readlines()
for i, line in enumerate(colloc_lines):
	if i > 0:
		line = line.strip()
		if line.count("\t") == 2:
			node, collocate, freq = line.strip().split("\t")
			freq = int(freq)
			cooc_pool += freq #* 2
			if freq > 5:
				collocate_freqs[node][collocate] += freq
				#collocate_freqs[collocate][node] += freq


# Get lemmas from TT dict
# TODO: Also get norm-pos-lemma mappings from ANNIS items not in the TT dict
lemma_list = read_lemmas(options.lemma_list)


norm_counts, lemma_counts = get_freqs(options.url,corpora, use_cache=options.use_cache)

total = float(sum(norm_counts.values()))
norm_freqs = {}
lemma_freqs = {}

for norm in norm_counts:
	freq = (norm_counts[norm]/total) * 10000
	norm_freqs[norm] = freq
for lemma in lemma_counts:
	freq = (lemma_counts[lemma]/total) * 10000
	lemma_freqs[lemma] = freq

norm_freqs_as_list = [[val,key] for key,val in iteritems(norm_freqs)]
norm_freqs_as_list = add_rank(norm_freqs_as_list)
lemma_freqs_as_list = [[val,key] for key,val in iteritems(lemma_freqs)]
lemma_freqs_as_list = add_rank(lemma_freqs_as_list)

norm_data = {}
lemma_data = {}

for freq, norm, rank in norm_freqs_as_list:
	norm_data[norm] = (freq,rank)
for freq, lemma, rank in lemma_freqs_as_list:
	lemma_data[lemma] = (freq,rank)


rows = []
lemmas = set([])
norms = set([])
lemma2pos = defaultdict(set)
norm2pos = defaultdict(set)
for row in lemma_list:
	norm, pos, lemma = row
	lemma2pos[lemma].add(pos)
	norm2pos[norm].add(pos)
	lemmas.add(lemma)
	norms.add(norm)
	if norm in norm_counts:
		norm_count = norm_counts[norm]
	else:
		norm_count = 0
	if norm in norm_data:
		norm_freq, norm_rank = norm_data[norm]
	else:
		norm_freq, norm_rank = [0,0]
	if lemma in lemma_counts:
		lemma_count = lemma_counts[lemma]
	else:
		lemma_count = 0
	if lemma in lemma_data:
		lemma_freq, lemma_rank = lemma_data[lemma]
	else:
		lemma_freq, lemma_rank = [0,0]
	if options.outmode == "text":
		print(norm + "\t" + pos + "\t" + lemma + "\t" + str(norm_count) + "\t" + str("%.2f" % round(norm_freq,2)) + "\t" + str(norm_rank)+ "\t" + str(lemma_count) + "\t" + str("%.2f" % round(lemma_freq,2)) + "\t" + str(lemma_rank))
	else:
		rows.append([norm, pos, lemma, str(norm_count), str("%.2f" % round(norm_freq,2)), str(norm_rank), str(lemma_count), str("%.2f" % round(lemma_freq,2)), str(lemma_rank)])


out_colloc = []
for norm in norms:
	if norm in collocate_freqs and norm in norm_freqs:  # Only retrieve collocations for confirmed lemmas
		for collocate in collocate_freqs[norm]:
			if collocate in norms and collocate in norm_freqs:
				# Valid pair
				assoc = get_assoc(norm_counts[norm],norm_counts[collocate],collocate_freqs[norm][collocate],cooc_pool)
				if options.outmode == "text":
					print("\t".join([norm, collocate, str(collocate_freqs[norm][collocate]), str(assoc)]))
				else:
					out_colloc.append([norm, collocate, collocate_freqs[norm][collocate], assoc])


if options.outmode == "db":
	utf_rows = []
	for row in rows:
		new_row = []
		for field in row:
			field = field
			new_row.append(field)
		utf_rows.append(new_row)
	update_db(utf_rows)
	utf_rows = []
	for row in out_colloc:
		#if row[0] not in norm2pos:
		#	continue
		#else:
		#	if not any([x in norm2pos[row[0]] for x in ["N","NPROP","V","VSTAT","VIMP","ADV"]]):
		#		continue
		if row[1] not in norm2pos:
			continue
		else:
			if not any([x in norm2pos[row[1]] for x in ["N","NPROP","V","VSTAT","VIMP","ADV"]]):
				continue
		if row[0] == row[1]:
			continue
		if row[1].encode("utf8") in stop_list:
			continue
		new_row = []
		for field in row[:-2]:
			new_row.append(field)
		new_row += row[-2:]
		utf_rows.append(new_row)
	update_db(utf_rows,table="collocates")


