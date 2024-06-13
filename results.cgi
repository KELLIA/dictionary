#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sqlite3 as lite
import re
import cgi, cgitb
import os, platform
from helper import wrap, lemma_exists, get_lemmas_for_word
from helper import separate_coptic, strip_hyphens
from operator import itemgetter
from math import ceil
cgitb.enable()

print "Content-type: text/html\n"

	
def first_orth(orthstring):
	first_orth = re.search(r'\n(.*?)~', orthstring)
	if first_orth is not None:
		return first_orth.group(1)
	else:
		return "NONE"

def second_orth(orthstring):
	first_search = re.search(r'\n(.*?)~', orthstring)
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
	if len(senses) > 1:
		sense_html = '<ol class="sense_list">'
		opener = "<li>"
		closer = ""
	else:
		sense_html = ""
		opener = '<div class="single_sense">'
		closer = "</div>"

	for sense in senses:
		definition = re.search(r'~~~(.*);;;', sense)
		if definition is not None:
			sense_html += opener + definition.group(1).encode("utf8") + closer
	if len(senses) > 1:
		sense_html += "</ol>"
	return sense_html
	
	
def retrieve_related(word):
	sql_command = 'SELECT * FROM entries WHERE entries.etym REGEXP ?'
	parameters = [r'.*cf\. #' + word + '#.*']
	sql_command += " ORDER BY ascii"
	
	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	else:
		con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')

	con.create_function("REGEXP", 2, lambda expr, item : re.search(expr.lower(), item.lower()) is not None)
	
	with con:
		cur = con.cursor()
		cur.execute(sql_command, parameters)
		rows = cur.fetchall()
		
		tablestring = '<div class="content">\n' + "Entries related to '" + word.encode("utf8") + "'<br/>"
		if len(rows) == 1:
			row = rows[0]
			#entry_url = "entry.cgi?entry=" + str(row[0]) + "&super=" + str(row[1])
			entry_url = "entry.cgi?tla=" + str(row[-2])
			#return '<meta http-equiv="refresh" content="0; URL="' + entry_url + '" />'
			#return '<script>window.location = "' + entry_url + '";</script>'
# 		elif len(rows) > 100:
# 			tablestring += 'Search had ' + str(len(rows)) + ' results - showing first 100'
# 			rows = rows[:100]
		elif len(rows) == 0 and len(word) > 0:  # no matches found
			tablestring += str(len(rows)) + ' results for <span class="anti">' + word.encode("utf8") + "</span>\n"
			if lemma_exists(word.encode("utf8")):
				tablestring += "<br/>This may be a form of:<br/>\n"
				tablestring += '<table id="results" class="entrylist">'
				rows = get_lemmas_for_word(word.encode("utf8"))
				for row in rows:
					tablestring += "<tr>"

					orth = row[0]
					link = "results.cgi?coptic=" + row[0]
					lem_pos = str(row[1])
					#print lem_pos

					tablestring += '<td class="orth_cell">' + '<a href="' + link.encode("utf8") + '">'
					tablestring += orth.encode("utf8")
					tablestring += "</a>" + "</td>"
					tablestring += '<td class="pos_cell">' + '(for '+word.encode("utf8") +'/' + lem_pos + ')</td>'

					tablestring += "</tr>"
				tablestring += "</table>\n</div>\n"
				return tablestring
		else:
			tablestring += str(len(rows)) + ' Results'
		tablestring += '<table id="results" class="entrylist">'
		for row in rows:
			tablestring += "<tr>"

			orth = first_orth(row[2])
			second = second_orth(row[2])
			if len(str(row[-2])) > 0:
				link = "entry.cgi?tla=" + str(row[-2])
			else:
				link = "entry.cgi?entry=" + str(row[0]) + "&super=" + str(row[1])

			tablestring += '<td class="orth_cell">' + '<a href="' + link + '">' + orth.encode("utf8") + "</a>" +"</td>"
			tablestring += '<td class="second_orth_cell">' +  second.encode("utf8")  +"</td>"
			
			sense = sense_list(row[5])
			tablestring += '<td class="sense_cell">' + sense + "</td>"
			
			tablestring += "</tr>"
		tablestring += "</table>\n</div>\n"
		return tablestring
	

def retrieve_entries(word, dialect, pos, definition, def_search_type, def_lang, search_desc="", params=None, tla_search=None):
	if params is None:
		params = {}
	sql_command = 'SELECT * FROM entries WHERE '
	constraints = []
	parameters = []

	#what's in the 'Search' column--based on word, word_search_type, dialect
	if len(word) > 0:
		try:
			re.compile(word)
			op = 'REGEXP'
		except:
			op = '='

		if dialect == 'any':
			word_search_string = r'.*\n' + word + r'~.*'
		else:
			word_search_string = r'.*\n' + word + r'~' + dialect + r'?\n.*'

		word_constraint = "entries.search "+op+" ?"
		parameters.append(word_search_string)
		if " " in word:
			word_constraint = "(" + word_constraint + " OR entries.oRef = ?)"
			parameters.append(word)
		constraints.append(word_constraint)

	elif dialect != 'any':
		dialect_constraint = "entries.search REGEXP ?"
		constraints.append(dialect_constraint)
		parameters.append(r'.*~' + dialect + r'?(\^\^[^\n]*)*\n')

	# POS column, based on pos
	if pos != 'any':
		pos_constraint = "entries.POS = ?"
		constraints.append(pos_constraint)
		parameters.append(pos)

	# one or all of the sense columns--which is specified by def_lang, search within it based on definition and def_search_type
	if def_search_type == 'exact sequence' and tla_search is None:
		def_search_string = r'.*\b' + definition + r'\b.*'
		try:
			re.compile(def_search_string)
			op = 'REGEXP'
		except:
			op = '='
		if def_lang == 'any':
			def_constraint = "(entries.en "+op+" ? OR entries.de "+op+" ? OR entries.fr "+op+" ?)"
			constraints.append(def_constraint)
			parameters.append(def_search_string)
			parameters.append(def_search_string)
			parameters.append(def_search_string)
		elif def_lang == 'en':
			def_constraint = "entries.en "+op+" ?"
			constraints.append(def_constraint)
			parameters.append(def_search_string)
		elif def_lang == 'fr':
			def_constraint = "entries.fr "+op+" ?"
			constraints.append(def_constraint)
			parameters.append(def_search_string)
		elif def_lang == 'de':
			def_constraint = "entries.de "+op+" ?"
			constraints.append(def_constraint)
			parameters.append(def_search_string)

	elif def_search_type == 'all words' and tla_search is None:
		words = definition.split(' ')
		for one_word in words:
			try:
				re.compile(one_word)
				op = 'REGEXP'
			except:
				op = '='
			def_search_string = r'.*\b' + one_word + r'\b.*'
			if def_lang == 'any':
				def_constraint = "(entries.en "+op+" ? OR entries.de "+op+" ? OR entries.fr "+op+" ?)"
				constraints.append(def_constraint)
				parameters.append(def_search_string)
				parameters.append(def_search_string)
				parameters.append(def_search_string)
			elif def_lang == 'en':
				def_constraint = "entries.en "+op+" ?"
				constraints.append(def_constraint)
				parameters.append(def_search_string)
			elif def_lang == 'fr':
				def_constraint = "entries.fr "+op+" ?"
				constraints.append(def_constraint)
				parameters.append(def_search_string)
			elif def_lang == 'de':
				def_constraint = "entries.de "+op+" ?"
				constraints.append(def_constraint)
				parameters.append(def_search_string)
	if tla_search is not None:
		constraints.append("xml_id = ?")
		parameters.append(tla_search)

	sql_command += " AND ".join(constraints)
	sql_command += " ORDER BY ascii"

	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	else:
		con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')

	con.create_function("REGEXP", 2, lambda expr, item : re.search(expr.lower(), item.lower(), flags=re.UNICODE) is not None)
	with con:
		cur = con.cursor()
		cur.execute(sql_command, parameters)
		rows = cur.fetchall()

		tablestring = '<div class="content">\n' + search_desc.encode("utf8") + "<br/>\n"
		if len(rows) == 1:
			row = rows[0]
			super_id = str(row[1])
			entry_id = str(row[0])
			tla_id = str(row[-2])

			if len(tla_id)>0:
				entry_url = "entry.cgi?tla=" + tla_id
			else:
				entry_url = "entry.cgi?entry=" + entry_id + "&super=" + super_id
			#return '<meta http-equiv="refresh" content="0; URL="' + entry_url + '" />'
			return '<script>window.location = "' + entry_url + '";</script>'
		elif len(rows) > 100:
			page = 1 if "page" not in params else int(params["page"])
			start = (page-1)*100
			prev_url = next_url = first_url = last_url = "results.cgi?"
			args = []
			for param in params:
				if params[param] == "" or param == "page":
					continue
				elif params[param] == "any":
					if param in ["pos","dialect","def_lang"]:
						continue
				elif (param == "related" and str(params[param])=="false") or (param == "def_search_type" and params[param]=="exact sequence") or \
						(param == "def_search_type" and params[param]=="all words"):
					continue
				args.append(param + "=" + str(params[param]))
			last_page = int(ceil(len(rows)/100.0))
			next_url += "&".join(sorted(args + ["page=" + str(page+1)]))
			first_url += "&".join(sorted(args + ["page=1"]))
			last_url += "&".join(sorted(args + ["page=" + str(last_page)]))
			prev_url += "&".join(sorted(args + ["page=" + str(page-1)]))

			if start > 1:
				prev_button = '''<a class="btn btn-default btn-page" href="'''+prev_url+'''"><i class="fa fa-chevron-left"></i> Previous</a>'''
				first_button = '''<a class="btn btn-default btn-page" href="'''+first_url+'''"><i class="fa fa-chevron-left"></i><i class="fa fa-chevron-left"></i> First</a>'''
			else:
				first_button = '''<a class="btn btn-default btn-page" disabled="disabled"><i class="fa fa-chevron-left"></i><i class="fa fa-chevron-left"></i> First</a>'''
				prev_button = '''<a class="btn btn-default btn-page" disabled="disabled"><i class="fa fa-chevron-left"></i> Previous</a>'''
			if start+100 < len(rows):
				end = start+100
				next_button = '''<a class="btn btn-default btn-page" href="'''+next_url+'''">Next <i class="fa fa-chevron-right"></i></a>'''
				last_button = '''<a class="btn btn-default btn-page" href="'''+last_url+'''">Last <i class="fa fa-chevron-right"></i><i class="fa fa-chevron-right"></i></a>'''
			else:
				end = len(rows)
				last_button = '''<a class="btn btn-default btn-page" disabled="disabled">Last <i class="fa fa-chevron-right"></i><i class="fa fa-chevron-right"></i></a>'''
				next_button = '''<a class="btn btn-default btn-page" disabled="disabled">Next <i class="fa fa-chevron-right"></i></a>'''
			tablestring += 'Search had ' + str(len(rows)) + ' results - showing results ' + str(start+1) + ' to ' + str(end)
			rows = rows[start:end]
			tablestring +="<div>" + first_button + prev_button + next_button + last_button + "</div>\n"
		elif len(rows) == 0 and len(word) > 0:  # no matches found
			tablestring += str(len(rows)) + ' results for <span class="anti">' + word.encode("utf8") + "</span>\n"
			if lemma_exists(word.encode("utf8")):
				tablestring += "<br/>This may be a form of:<br/>\n"
				tablestring += '<table id="results" class="entrylist">'
				rows = get_lemmas_for_word(word.encode("utf8"))
				for row in rows:
					tablestring += "<tr>"

					orth = row[0]
					link = "results.cgi?coptic=" + row[0]
					lem_pos = str(row[1])
					#print lem_pos

					tablestring += '<td class="orth_cell">' + '<a href="' + link.encode("utf8") + '">'
					tablestring += orth.encode("utf8")
					tablestring += "</a>" + "</td>"
					tablestring += '<td class="pos_cell">' + '(for '+word.encode("utf8") +'/' + lem_pos + ')</td>'

					tablestring += "</tr>"
				tablestring += "</table>\n</div>\n"
				return tablestring
		else:
			tablestring += str(len(rows)) + ' Results'
		tablestring += '<table id="results" class="entrylist">'
		for row in rows:
			tablestring += "<tr>"

			orth = first_orth(row[2])
			second = second_orth(row[2])

			super_id = str(row[1])
			entry_id = str(row[0])
			tla_id = str(row[-2])

			if len(tla_id) >0:
				link = "entry.cgi?tla=" + tla_id
			else:
				link = "entry.cgi?entry=" + entry_id + "&super=" + super_id
			
			tablestring += '<td class="orth_cell">' + '<a href="' + link + '">' + orth.encode("utf8") + "</a>" +"</td>"
			tablestring += '<td class="second_orth_cell">' +  second.encode("utf8")  +"</td>"
			
			sense = sense_list(row[5])
			tablestring += '<td class="sense_cell">' + sense + "</td>"
			
			tablestring += "</tr>"
		tablestring += "</table>\n</div>\n"

		return tablestring
					
			
if __name__ == "__main__":
	form = cgi.FieldStorage()
	params = {}
	word = cgi.escape(form.getvalue("coptic", "")).replace("(","").replace(")","").replace("=","").strip()
	dialect = cgi.escape(form.getvalue("dialect", "any")).replace("(","").replace(")","").replace("=","").strip()
	pos = cgi.escape(form.getvalue("pos", "any")).replace("(","").replace(")","").replace("=","").strip()
	definition = cgi.escape(form.getvalue("definition", "")).replace("(","").replace(")","").replace("=","").strip()
	def_search_type = cgi.escape(form.getvalue("def_search_type", "exact sequence")).replace("(","").replace(")","").replace("=","")
	def_lang = cgi.escape(form.getvalue("lang", "any")).replace("(","").replace(")","").replace("=","").strip()
	related = cgi.escape(form.getvalue("related", "false")).replace("(","").replace(")","").replace("=","")
	quick_string = cgi.escape(form.getvalue("quick_search", "")).replace("(","").replace(")","").replace("=","").strip()
	page = 1
	page = cgi.escape(form.getvalue("page", "1")).replace("(","").replace(")","").replace("=","").strip()
	params["coptic"] = word
	params["dialect"] = dialect
	params["pos"] = pos
	params["definition"] = definition
	params["def_search_type"] = def_search_type
	params["def_lang"] = def_lang
	params["related"] = related
	params["quick_search"] = quick_string
	try:
		page = abs(int(page))
	except:
		page = 1
	params["page"] = page
	tla_search = None
	if quick_string != "":
		separated = separate_coptic(quick_string)
		def_search_type = "all words"
		word = " ".join(separated[0])
		definition = " ".join(separated[1])
		m = re.match(r'(C[0-9]+)$',definition)
		if m is not None:
			tla_search = m.group(1)
			# Check that this TLA ID exists
			if platform.system() == 'Linux':
				con = lite.connect('alpha_kyima_rc1.db')
			else:
				con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
			with con:
				cur = con.cursor()
				cur.execute("select xml_id from entries where xml_id=?", (tla_search,))
				rows = cur.fetchall()
				if len(rows) < 1:
					tla_search = None
		m = re.match(r'(CF[0-9]+)$',definition)
		if m is not None:
			newline = """
"""
			tla_search = ".*" + m.group(1) + "([^0-9].*|$)"
			# Check that this TLA ID exists
			if platform.system() == 'Linux':
				con = lite.connect('alpha_kyima_rc1.db')
			else:
				con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
			with con:
				con.create_function("REGEXP", 2, lambda expr, item: re.search(expr.lower(), item.lower()) is not None)
				cur = con.cursor()
				cur.execute("select xml_id from entries where Name REGEXP ?", (tla_search,))
				rows = cur.fetchall()
				if len(rows) < 1:
					cur.execute("select xml_id from entries where lemma_form_id = ?", (m.group(1),))
					rows = cur.fetchall()
					if len(rows) <1:
						tla_search = None
					else:
						tla_search = rows[0][0]
				else:
					tla_search = rows[0][0]

	word = word.decode("utf8")
	word = strip_hyphens(word)
	definition = definition.decode("utf8")
	word_desc = """ for '<span style="font-family: antinoouRegular, sans-serif;">""" + word +"</span>'" if len(word)  > 0 else ""
	dialect_desc = " in dialect " + dialect + " or unspecified" if dialect != "any" and len(dialect)  > 0 else ""
	definition_desc = " definitions matching <i>" + definition + "</i> in language <i>"  + def_lang + "</i>" if len(definition)  > 0 else ""
	pos_desc = " restricted to POS tag " + pos if pos != "any" else ""
	search_desc = "You searched " + word_desc + dialect_desc + definition_desc + pos_desc
	results_page = retrieve_entries(word, dialect, pos, definition, def_search_type, def_lang, search_desc,params=params,tla_search=tla_search)

	### related entry stuff
	if word != "": # nothing to do if no coptic word searched?
		if related == "false":
			link = "results.cgi?coptic=" + word + "&dialect=" + dialect + "&pos=" + pos + "&definition=" + definition + "&def_search_type=" + def_search_type + "&lang=" + def_lang + "&related=true"
			#results_page += '<a href="' + link.encode("utf8") + '">Include related entries</a>'
			if not "window.location" in results_page:  # No need to retrieve related if we are redirecting due to a unique entry being found
				results_page = results_page[:-8] + '<a href="' + link.encode("utf8") + '">Include related entries</a></div>\n'
		elif related == "true":
			if not "window.location" in results_page:  # No need to retrieve related if we are redirecting due to a unique entry being found
				results_page += retrieve_related(word)
	
	
	wrapped = wrap(results_page)
	wrapped = wrapped.replace('<link rel="canonical" href="https://coptic-dictionary.org/" />','<link rel="canonical" href="https://coptic-dictionary.org/results.cgi" />')
	
	if len(quick_string) > 0:
		quick_target = 'placeholder="Quick Search"'
		wrapped = wrapped.replace(quick_target, quick_target + ' value="' + quick_string + '"')
	print(wrapped)
