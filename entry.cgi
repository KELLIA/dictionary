#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
import cgitb
import os
import platform
import re
import sqlite3 as lite
import string
import sys
from collections import defaultdict

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

def process_orthstring(orthstring, orefstring, cursor):
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
			orth_geo = re.match(r'^(.*)~(.?\^\^([A-Za-z0-9]*))$', orth_geo_string)
			if orth_geo is not None:
				orth = orth_geo.group(1)
				orth_geo_dict[orth].append(orth_geo.group(2).encode("utf8"))
		for distinct_orth in orth_geo_dict:
			geo_string = " ".join(orth_geo_dict[orth])
			form_id = ""
			if "^^" in geo_string:
				geo_string, form_id = geo_string.split("^^")
			annis_query = get_annis_query(orth, oref)
			orth_html += '<tr><td class="orth_entry">' + distinct_orth.encode("utf8") + '</td><td class="dialect">' + \
						 geo_string.encode("utf8") + '</td><td class="tla_orth_id">TLA: ' + \
						  form_id.encode("utf8") + '</td><td class="morphology">' + \
						 gramstring.encode("utf8") + '</td><td class="annis_link">ANNIS: <a href="' + annis_query + \
						 '" target="_new"><i class="fa icon-annis" title="Search in ANNIS"></i></a></td>'
			freq_data = get_freqs(distinct_orth)
			freq_info = """	<td><div class="expandable">
					            <a class="dict_tooltip" href="">
					            <i class="fa fa-sort-numeric-asc freq_icon">&nbsp;</i>
            					<span><b>ANNIS frequencies:</b><br/>**freqs**</span>
            					</a>
          					</div></td>"""

			freq_info = freq_info.replace("**freqs**",freq_data)
			orth_html += freq_info

			colloc_data = get_collocs(distinct_orth,cursor)
			if len(colloc_data) > 0:
				colloc_info = """	<td><div class="expandable">
										<a class="dict_tooltip" href="">
										<i class="fa fa-comment-o freq_icon">&nbsp;</i>
										<span><b>Top collocations in ANNIS: (5 word window)</b><br/><table class="colloc_tab">
										<tr><th>&nbsp;</th><th>Word</th><th>Co-occurrences</th><th>Association (MI3)</th></tr>"""
				for r, row in enumerate(colloc_data):
					word, collocate, cooc, assoc = row
					#colloc_info += '<li><a href="https://corpling.uis.georgetown.edu/coptic-dictionary/results.cgi?quick_search='+ \
					#			   collocate + '">' + collocate + "</a> (" + str(cooc) + "," + str(assoc)+")</li>"
					colloc_info += '<tr><td style="text-align:right">'+str(r+1)+'.</td><td><a href="results.cgi?quick_search='+ \
								   collocate + '">' + collocate + '</a></td><td style="text-align: center">' + str(cooc) + '</td><td style="text-align: center">' + str("%.2f" % assoc) + "</td></tr>"
				colloc_info += """</table></span>
										</a>
									</div></td></tr>"""
				orth_html += colloc_info.encode("utf8")

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
			biblio = sense_parts.group(4).encode("utf8")
			if len(biblio) > 0:
				biblio = "Bibliography: " + biblio
			ref_bibl = sense_parts.group(2).encode("utf8") + " " + biblio
			xr = re.search(r'xr. #(.*?)#', ref_bibl)
			if xr is not None:
				word = xr.group(1)
				link = '<a href="results.cgi?coptic=' + word + '">' + word + "</a>"
				ref_bibl = re.sub(r'xr. #(.*?)#', r'xr. ' + link, ref_bibl)
			ref_bibl = re.sub(r'(CD ([0-9]+)[ab]?-?[0-9]*[ab]?)',r'''<a href="http://coptot.manuscriptroom.com/crum-coptic-dictionary/?docID=800000&pageID=\2" target="_new" style="text-decoration-style: solid;">\1</a><a class="hint" data-tooltip="W.E. Crum's Dictionary">?</a>''',ref_bibl)
			ref_bibl = re.sub(r'KoptHWb( [0-9]+(, ?[0-9]+)*)?',r'KoptHWb\1<a class="hint" data-tooltip="Koptisches Handw&ouml;rterbuch /\nW. Westendorf">?</a>',ref_bibl)
			ref_bibl = re.sub(r'CED( [0-9]+(, ?[0-9]+)*)?',r'CED\1<a class="hint" data-tooltip="J. Černý, Coptic Etymological Dictionary, Cambridge: Cambridge Univ. Press, 1976">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(DELC [0-9A-Za-z]+(, ?[0-9A-Za-z]+)*)',r'\1<a class="hint" data-tooltip="W. Vycichl, Dictionnaire étymologique de la langue copte, Leuven: Peeters, 1983">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(ChLCS [0-9A-Za-z]+(, ?[0-9A-Za-z]+)*)',r'\1<a class="hint" data-tooltip="P. Cherix, Lexique Copte (dialecte sahidique), Copticherix, 2006-2018">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(ONB [0-9]+(, ?[0-9]+)*)',r'\1<a class="hint" data-tooltip="T. Orlandi, Koptische Papyri theologischen Inhalts (Mitteilungen aus der Papyrussammlung der Österreichischen Nationalbibliothek (Papyrus Erzherzog Rainer) / Neue Serie, 9), Wien: Hollinek, 1974">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(WbGWKDT [0-9]+(, ?[0-9]+)*)',r'\1<a class="hint" data-tooltip="H. Förster, Wörterbuch der griechischen Wörter in den koptischen dokumentarischen Texten. Berlin/Boston: de Gruyter, 2002">?</a>',ref_bibl)
			ref_bibl = re.sub(r'((Kasser )?CDC [0-9A-Za-z]+(, ?[0-9A-Za-z]+)*)',r'''\1<a class="hint" data-tooltip="R. Kasser, Compléments au dictionnaire copte de Crum, Kairo: Inst. Français d'Archéologie Orientale, 1964">?</a>''',ref_bibl)
			ref_bibl = re.sub(r'(LCG [0-9]+(, ?[0-9]+)*)',r'\1<a class="hint" data-tooltip="B. Layton, A Coptic grammar: with a chrestomathy and glossary; Sahidic dialect, Wiesbaden: Harrassowitz, 2000">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(Till D [0-9]+(, ?[0-9]+)*)',r'\1<a class="hint" data-tooltip="W. Till, Koptische Dialektgrammatik: mit Lesestücken und Wörterbuch, München: Beck, 1961">?</a>',ref_bibl)
			ref_bibl = re.sub(r'(Osing, Pap. Ox. [0-9]+(, ?[0-9]+)*)',r'\1<a class="hint" data-tooltip="J. Osing: Der spätägyptische Papyrus BM 10808, Harrassowitz, Wiesbaden 1976">?</a>',ref_bibl)
			ref_bibl = re.sub("DDGLC ref:","DDGLC Usage ID:",ref_bibl)
			#ref_bibl = re.sub(r'KoptHWb( [0-9]+)?',r'KoptHWb\1<i class="fa fa-info-circle" data-tooltip="Koptisches Handw&ouml;rterbuch /\nW. Westendorf"></i>',ref_bibl)

			engstr = "Engl. " if (de_parts is not None or fr_parts is not None) else ""
			sense_html += '<tr><td class="entry_num">' + sense_parts.group(1).encode("utf8") + '.</td><td class="sense_lang">'+engstr+'</td><td class="trans">' + en_definition.encode("utf8") + '</td></tr>'
			if fr_parts is not None:
				sense_html += '<tr><td></td><td class="sense_lang">Fran. </td><td class="trans">' + fr_definition.encode("utf8") + '</td></tr>'
			if de_parts is not None:
				sense_html += '<tr><td></td><td class="sense_lang">Dtsch. </td><td class="trans">' + de_definition.encode("utf8") + '</td></tr>'
			sense_html += '<tr><td></td><td class="bibl" colspan="2">' + ref_bibl + '</td></tr>'
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
		con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
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


def get_collocs(word, cursor):
	thresh = 15
	sql = "SELECT * from collocates WHERE lemma=? and not collocate in ('ⲡ','ⲛ','ⲧ','ⲟⲩ') and assoc > ? ORDER BY assoc DESC LIMIT 20"
	rows = cursor.execute(sql,(word,thresh)).fetchall()
	return rows


if __name__ == "__main__":

	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	elif platform.system() == 'Windows':
		#con = lite.connect('coptic-dictionary' + os.sep + 'alpha_kyima_rc1.db')
		con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')

	form = cgi.FieldStorage()

	tla_id = cgi.escape(form.getvalue("tla", "")).replace("(","").replace(")","").replace("=","")

	if len(tla_id) > 0:
		# Get corresponding entry_id and super_id
		with con:
			cur = con.cursor()

			tla_query = "SELECT Id, Super_Ref FROM entries WHERE entries.xml_id = ?;"
			cur.execute(tla_query,(tla_id,))
			result = cur.fetchone()
			if len(result) > 0:
				entry_id = result[0]
				super_id = result[1]
			else:
				entry_id = cgi.escape(form.getvalue("entry", "")).replace("(","").replace(")","").replace("=","")
				super_id = cgi.escape(form.getvalue("super", "")).replace("(","").replace(")","").replace("=","")
	else:
		entry_id = cgi.escape(form.getvalue("entry", "")).replace("(","").replace(")","").replace("=","")
		super_id = cgi.escape(form.getvalue("super", "")).replace("(","").replace(")","").replace("=","")
	#entry_id = 6033
	#super_id = 2342

	entry_page = '<div class="content">'

	with con:
		cur = con.cursor()

		this_sql_command = "SELECT * FROM entries WHERE entries.id = ?;"
		cur.execute(this_sql_command,(entry_id,))
		this_entry = cur.fetchone()
		grk_id = this_entry[-2]
		entry_xml_id = this_entry[-1]

		if this_entry is None:
			entry_page +="No entry found\n</div>\n"
			print wrap(entry_page)
			sys.exit()

		related_sql_command = "SELECT * FROM entries WHERE (entries.super_ref = ? AND entries.id != ?)"
		if len(grk_id) > 0:
			related_sql_command += " OR (entries.grkId = ? AND entries.id != ?)"
			params = (super_id,entry_id,grk_id,entry_id)
		else:
			related_sql_command += ";"
			params = (super_id,entry_id)
		cur.execute(related_sql_command, params)
		related_entries = cur.fetchall()

		# orth (and morph) info
		entry_page += process_orthstring(this_entry[2], this_entry[-3], cur) #this_entry[-3] -> oRef column
		tag = this_entry[3].encode("utf8")
		if tag == "NULL" or tag == "NONE":
			tag = "--"
		entry_page += '<div class="tag">\n\tScriptorium tag: ' + tag + "\n</div>\n"

		# from sense info
		entry_page += '<div class="sense_info"><b style="font-family: antinoouRegular">Senses:</b><br/>'
		entry_page += process_sense(this_entry[4], this_entry[5], this_entry[6])
		entry_page += '</div>'

		# etym info
		entry_page += process_etym(this_entry[7].encode("utf8"))

		# link to other entries in the superentry
		if len(related_entries) > 0:
			entry_page += '<div class="see_also"><b style="font-family: antinoouRegular">See also:</b><br/>'
			entry_page += related(related_entries)
			entry_page += '</div>'

		entry_page += "</div>\n"
		
		xml_id_string = 'TLA lemma no. ' + entry_xml_id if entry_xml_id != "" else ""
		
		entry_page += '<div id="citation_info_box">Please cite as: '+xml_id_string.encode("utf8")+', in: <i>Coptic Dictionary Online</i>, ed. by the Koptische/Coptic Electronic Language and Literature International Alliance (KELLIA), http://www.coptic-dictionary.org/entry.cgi?tla='+entry_xml_id.encode("utf8")+' (accessed yyyy-mm-dd).</div>'

	wrapped = wrap(entry_page)
	
	# adding TLA lemma no. to title and citation info
	wrapped = re.sub(r"(Entry detail[^<>]*</h2>)",r"Entry "+xml_id_string.encode("utf8") +"</h2>\n",wrapped)

	print wrapped
