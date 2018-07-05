#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import re
import cgi, cgitb
import string
from collections import defaultdict
import os, platform, sys
from helper import wrap, get_annis_query
cgitb.enable()

print "Content-type: text/html\n"

def first_orth(orthstring):
	first_orth = re.search(r'(?:^|\n)([^\n].*?)~', orthstring)
	if first_orth is not None:
		return first_orth.group(1)
	else:
		return "NONE"

def second_orth(orthstring):
	first_search = re.search(r'(?:^|\n)([^\n].*?)~', orthstring)
	if first_search is not None:
		first = first_search.group(1)
	else:
		first = ""

	second_orth = re.search(r'\n(.*?)[^\n]*\n(.*?)~', orthstring)
	sub_entries = re.findall(r'\n(.*?)~', orthstring)
	distinct_entries = set([])
	for entry in sub_entries:
		if entry.encode("utf8") != first.encode("utf8"):
			distinct_entries.add(entry)
	count_sub_entries = len(distinct_entries)
	dots = ", ..." if count_sub_entries > 2 else ""

	if second_orth is not None:
		if second_orth.group(2) != first:
			return second_orth.group(2) + dots
	return "--"

def sense_list(sense_string):
	senses = sense_string.split("|||")
	sense_html = "<ol>"
	for sense in senses:
		definition = re.search(r'~~~(.*);;;', sense)
		if definition is not None:
			sense_html += "<li>" + definition.group(1).encode("utf8") + "</li>"
	sense_html += "</ol>"
	return sense_html

def process_orthstring(orthstring, orefstring):
	forms = orthstring.split("|||")
	orefs = orefstring.split("|||")
	orth_html = '<table id="orths">'
	for i, form in enumerate(forms):
		parts = form.split("\n")
		oref = orefs[i]
		gramstring = parts[0]
		orth_geo_dict = defaultdict(list)
		orth = "NONE"
		for orth_geo_string in parts[1:]:
			orth_geo = re.match(r'^(.*)~(.?)$', orth_geo_string)
			if orth_geo is not None:
				orth = orth_geo.group(1)
				orth_geo_dict[orth] += orth_geo.group(2).encode("utf8")
		for distinct_orth in orth_geo_dict:
			geo_string = " ".join(orth_geo_dict[orth])
			annis_query = get_annis_query(orth, oref)
			orth_html += '<tr><td class="orth_entry">' + distinct_orth.encode("utf8") + '</td><td class="morphology">' + \
						 gramstring.encode("utf8") + '</td><td class="dialect">' + geo_string.encode("utf8") + \
						 '</td><td class="annis_link"><a href="' + annis_query + \
						 '" target="_new"><i class="fa icon-annis" title="Search in ANNIS"></i></a></td>'
			freq_data = get_freqs(distinct_orth)
			freq_info = """	<td><div class="expandable">
					            <a class="dict_tooltip" href="">
					            <i class="fa fa-sort-numeric-asc freq_icon">&nbsp;</i>
            					<span><b>ANNIS frequencies:</b><br/>**freqs**</span>
            					</a>
          					</div></td></tr>"""

			freq_info = freq_info.replace("**freqs**",freq_data)
			orth_html += freq_info
	orth_html += "</table>"
	return orth_html

def process_sense(de, en, fr):
	en_senses = en.split("|||")
	fr_senses = fr.split("|||")
	de_senses = de.split("|||")
	sense_html = '<table id="senses">'
	for i in xrange(len(en_senses)):
		en_sense = en_senses[i]
		fr_sense = fr_senses[i]
		de_sense = de_senses[i]
		sense_parts = re.search(r'([0-9]+)\|(.*)~~~(.*);;;(.*)', en_sense)

		if sense_parts is not None:
			en_definition = sense_parts.group(3)
			fr_parts = re.search(r'[0-9]+\|.*~~~(.*);;;.*', fr_sense)
			if fr_parts is not None:
				fr_definition = fr_parts.group(1)
			de_parts = re.search(r'[0-9]+\|.*~~~(.*);;;.*', de_sense)
			if de_parts is not None:
				de_definition = de_parts.group(1)
			ref_bibl = sense_parts.group(2).encode("utf8") + " " + sense_parts.group(4).encode("utf8")
			xr = re.search(r'xr. #(.*?)#', ref_bibl)
			if xr is not None:
				word = xr.group(1)
				link = '<a href="results.cgi?coptic=' + word + '">' + word + "</a>"
				ref_bibl = re.sub(r'xr. #(.*?)#', r'xr. ' + link, ref_bibl)
			ref_bibl = re.sub(r'(CD ([0-9]+)[ab]?-?[0-9]*[ab]?)',r'<a href="http://coptot.manuscriptroom.com/crum-coptic-dictionary/?docID=800000&pageID=\2" target="_new">\1</a>',ref_bibl)

			sense_html += '<tr><td class="entry_num">' + sense_parts.group(1).encode("utf8") + '.</td><td class="trans">' + en_definition.encode("utf8") + '</td></tr>'
			if fr_parts is not None:
				sense_html += '<tr><td></td><td class="trans">' + fr_definition.encode("utf8") + '</td></tr>'
			if fr_parts is not None:
				sense_html += '<tr><td></td><td class="trans">' + de_definition.encode("utf8") + '</td></tr>'
			sense_html += '<tr><td></td><td class="bibl">' + ref_bibl + '</td></tr>'
	sense_html += "</table>"
	return sense_html

def process_etym(etym):
	xrs = re.findall(r' #(.*?)#', etym)
	if xrs is not None:
		for xr in xrs:
			word = xr
			link = '<a href="results.cgi?coptic=' + word + '">' + word + "</a>"
			word = re.sub(r'\(', '\\(', word)
			word = re.sub(r'\)', '\\)', word)
			etym = re.sub(r'#' + word + '#', link, etym)
	return '<div class="etym">\n\t' + etym + '\n</div>'


def related(related_entries):
	tablestring = '<table id="related" class="entrylist">'
	for entry in related_entries:
		tablestring += "<tr>"

		orth = first_orth(entry[2])
		second = second_orth(entry[2])

		link = "entry.cgi?entry=" + str(entry[0]) + "&super=" + str(entry[1])

		tablestring += '<td class="related_orth">' + '<a href="' + link + '">' + orth.encode("utf8") + "</a>" +"</td>"
		tablestring += '<td class="second_orth_cell">' +  second.encode("utf8")  +"</td>"

		sense = sense_list(entry[5])
		tablestring += '<td class="related_sense">' + sense + "</td>"

		tablestring += "</tr>"
	tablestring += "</table>"
	return tablestring


def get_freqs(item):
	item = item.replace("-","")#.replace("⸗".encode("utf8"),"")
	output = "<ul>\n"
	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	elif platform.system() == 'Windows':
		con = lite.connect('coptic-dictionary' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')

	with con:
		cur = con.cursor()

		sql = "SELECT word_freq, word_rank FROM lemmas WHERE word = ?;"
		cur.execute(sql,(item,))
		res = cur.fetchone()
		if res is not None:
			freq, rank = res
			output += "<li>Word form frequency per 10,000: "+str(freq)+" (# "+str(rank)+")</li>\n"
		else:
			output += "<li>Not found as word form in ANNIS</li>\n"
		sql = "SELECT lemma_freq, lemma_rank FROM lemmas WHERE word = ?;"
		cur.execute(sql, (item,))
		res = cur.fetchone()
		if res is not None:
			freq, rank = res
			output += "<li>Lemma frequency per 10,000: "+str(freq)+" (# "+str(rank)+")</li>\n"
		else:
			output += "<li>Not found as lemma in ANNIS</li>\n"

	return output + "</ul>\n"


if __name__ == "__main__":
	form = cgi.FieldStorage()
	entry_id = cgi.escape(form.getvalue("entry", "")).replace("(","").replace(")","").replace("=","")
	super_id = cgi.escape(form.getvalue("super", "")).replace("(","").replace(")","").replace("=","")

	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	elif platform.system() == 'Windows':
		con = lite.connect('coptic-dictionary' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')

	entry_page = '<div class="content">'

	with con:
		cur = con.cursor()

		this_sql_command = "SELECT * FROM entries WHERE entries.id = ?;"
		cur.execute(this_sql_command,(entry_id,))
		this_entry = cur.fetchone()

		if this_entry is None:
			entry_page +="No entry found\n</div>\n"
			print wrap(entry_page)
			sys.exit()

		related_sql_command = "SELECT * FROM entries WHERE entries.super_ref = ? AND entries.id != ?;"
		cur.execute(related_sql_command, (super_id,entry_id))
		related_entries = cur.fetchall()

		# orth (and morph) info
		entry_page += process_orthstring(this_entry[2], this_entry[-1])
		tag = this_entry[3].encode("utf8")
		if tag == "NULL" or tag == "NONE":
			tag = "--"
		entry_page += '<div class="tag">\n\tScriptorium tag: ' + tag + "\n</div>\n"

		# from sense info
		entry_page += process_sense(this_entry[4], this_entry[5], this_entry[6])

		# etym info
		entry_page += process_etym(this_entry[7].encode("utf8"))

		# link to other entries in the superentry
		if len(related_entries) > 0:
			entry_page += '<div class="see_also"><b style="font-family: antinoouRegular">See Also:</b><br/>'
			entry_page += related(related_entries)
			entry_page += '</div>'

		entry_page += "</div>"

	wrapped = wrap(entry_page)
	print wrapped
