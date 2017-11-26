#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script takes a tagged lemma table and an ANNIS url with a corpus list
to collect:
 1. A list of lemmas to look up inflected word forms
 2. Frequencies from ANNIS corpora for each lemma and word form
"""

from argparse import ArgumentParser
import re, sys, os, requests
from collections import defaultdict
from itertools import groupby


def read_lemmas(filename):
	"""

	:param filename: a tab delimited text file name, with three columns: word, pos, lemma
	:return: list of triples (word, pos, lemma)
	"""
	lines = open(filename).read().replace("\r","").split("\n")
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
		#line = line.decode("utf8")
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


def get_freqs(url):

	# TODO: remove duplicate data from sahidica.nt also in Mark and 1Cor
	corpora = ["shenoute.eagerness", "shenoute.fox", "shenoute.a22", "shenoute.abraham.our.father", "shenoute.dirt",
			   "apophthegmata.patrum", "sahidica.nt", "sahidic.ot", "pseudo.theophilus","martyrdom.victor","johannes.canons",
			   "besa.letters", "sahidica.mark", "sahidica.1corinthians", "doc.papyri"]
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
		field = fields[index]
		query = escape(query)
		params = "&".join([corpora, query, field])

		api_call = url + "annis-service/annis/query/search/frequency?"
		api_call += params
		resp = requests.get(api_call)
		text_content = resp.text
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


def update_db(row_list):
	import sqlite3 as lite
	con = lite.connect('..'+os.sep+'alpha_kyima_rc1.db')

	with con:
		cur = con.cursor()

		cur.execute("DROP TABLE IF EXISTS lemmas")
		cur.execute(
			"CREATE TABLE lemmas(word TEXT, pos TEXT, lemma TEXT, word_count TEXT, word_freq REAL, word_rank INT, " +
			"lemma_count TEXT, lemma_freq REAL, lemma_rank INT)")

		cur.executemany("INSERT INTO lemmas (word, pos, lemma, word_count, word_freq, word_rank, lemma_count, lemma_freq, lemma_rank) VALUES " +
						"(?, ?, ?, ?, ?, ?, ?, ?, ?);", row_list)
		con.commit()

parser = ArgumentParser()
parser.add_argument("-l","--lemma_list",action="store",dest="lemma_list",default="C:\\TreeTagger\\bin\\coptic\\copt_lemma_lex.tab")
parser.add_argument("-u","--url",action="store",dest="url",default="https://corpling.uis.georgetown.edu/")
parser.add_argument("-o","--outmode",action="store",dest="outmode",default="db")


options = parser.parse_args()

# Get lemmas from TT dict
# TODO: Also get norm-pos-lemma mappings from ANNIS items not in the TT dict
lemma_list = read_lemmas(options.lemma_list)

norm_counts, lemma_counts = get_freqs(options.url)

total = float(sum(norm_counts.values()))
norm_freqs = {}
lemma_freqs = {}

for norm in norm_counts:
	freq = (norm_counts[norm]/total) * 10000
	norm_freqs[norm] = freq
for lemma in lemma_counts:
	freq = (lemma_counts[lemma]/total) * 10000
	lemma_freqs[lemma] = freq

norm_freqs_as_list = [[val,key] for key,val in norm_freqs.iteritems()]
add_rank(norm_freqs_as_list)
lemma_freqs_as_list = [[val,key] for key,val in lemma_freqs.iteritems()]
add_rank(lemma_freqs_as_list)

norm_data = {}
lemma_data = {}

for freq, norm, rank in norm_freqs_as_list:
	norm_data[norm] = (freq,rank)
for freq, lemma, rank in lemma_freqs_as_list:
	lemma_data[lemma] = (freq,rank)


rows = []
for row in lemma_list:
	norm, pos, lemma = row
	if norm.decode("utf8") in norm_counts:
		norm_count = norm_counts[norm.decode("utf8")]
	else:
		norm_count = 0
	if norm.decode("utf8") in norm_data:
		norm_freq, norm_rank = norm_data[norm.decode("utf8")]
	else:
		norm_freq, norm_rank = [0,0]
	if lemma.decode("utf8") in lemma_counts:
		lemma_count = lemma_counts[lemma.decode("utf8")]
	else:
		lemma_count = 0
	if lemma.decode("utf8") in lemma_data:
		lemma_freq, lemma_rank = lemma_data[lemma.decode("utf8")]
	else:
		lemma_freq, lemma_rank = [0,0]
	if options.outmode == "text":
		print norm + "\t" + pos + "\t" + lemma + "\t" + str(norm_count) + "\t" + str("%.2f" % round(norm_freq,2)) + "\t" + str(norm_rank)+ "\t" + str(lemma_count) + "\t" + str("%.2f" % round(lemma_freq,2)) + "\t" + str(lemma_rank)
	else:
		rows.append([norm, pos, lemma, str(norm_count), str("%.2f" % round(norm_freq,2)), str(norm_rank), str(lemma_count), str("%.2f" % round(lemma_freq,2)), str(lemma_rank)])


if options.outmode == "db":
	utf_rows = []
	for row in rows:
		new_row = []
		for field in row:
			field = field.decode("utf8")
			new_row.append(field)
		utf_rows.append(new_row)
	update_db(utf_rows)

