#!/usr/bin/python2
# -*- coding: utf-8 -*-

import io, os, re, platform, json, unicodedata
import __main__
import unicodedata
from base64 import urlsafe_b64encode
import sqlite3 as lite


def get_con():
	if platform.system() == 'Windows':
		con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')
	con.create_function("REGEXP", 2, lambda expr, item: re.search(expr.lower(), item.lower()) is not None)
	return con


def make_active(html_input,button_id):
	return re.sub(r'(id="'+button_id+'")',r'class="active" \\1',html_input)


def wrap(html_input, caller=None):
	wrapper = open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "wrapper.html",'r').read()
	calling_script = __main__.__file__ if caller is None else caller
	calling_script = calling_script.replace(".cgi","")
	bug_report = ""
	bug_string = """<div id="bug_report">
				Found a bug or a problem? Please report it at: <a href="https://github.com/KELLIA/dictionary/issues">https://github.com/KELLIA/dictionary/issues</a>
				</div>"""
	if calling_script.endswith("results"):
		title = "Search results"
		activate = "none"
		bug_report += bug_string
	elif calling_script.endswith("entry"):
		title = "Entry detail"
		activate = "none"
		bug_report += bug_string
	elif calling_script.endswith("search"):
		title = "Search"
		activate = "home"
	elif calling_script.endswith("about"):
		title = "About"
		activate = "about"
	elif calling_script.endswith("help"):
		title = "How to search"
		activate = "help"
	elif calling_script.endswith("network"):
		title = "Term network"
		activate = "none"
	else:
		title = calling_script
		activate = "home"

	wrapped = wrapper.replace("**pagecontent**",html_input+bug_report)

	titled = wrapped.replace("**pagetitle**",title)

	activated = make_active(titled, activate)

	return activated


def separate_coptic(search_text):
	#coptic = search_text.split(" ")[0]
	#english = search_text.split(" ")[1]
	#return ([coptic],[english])
	words = search_text.split(" ")
	coptic_words = []
	non_coptic_words = []
	for word in words:
		coptic = ("COPTIC" in unicodedata.name(chr) for chr in unicode(word.decode("utf8")))
		if any(coptic):
			coptic_words.append(word)
		else:
			non_coptic_words.append(word)

	return (coptic_words, non_coptic_words)


def strip_hyphens(text):
	text = text.replace('-', '').replace(ur"\u0304","").replace(ur"\ufe26","").replace(ur"\ufe24","").replace(ur"\ufe25","")
	text = text.replace(ur'\u2013', '')
	text = text.replace(ur"\u2E17","")
	return text


def get_annis_query(coptic, oref, cs_pos=None, dialect="S", word_attr="lemma"):
	coptic = strip_hyphens(coptic).encode("utf8")
	oref = strip_hyphens(oref).encode("utf8")

	annis_base = "https://annis.copticscriptorium.org/annis/scriptorium#"
	if dialect == "B":
		corpus_list = "_c=Ym9oYWlyaWMuMWNvcmludGhpYW5zLGJvaGFpcmljLm1hcmssYm9oYWlyaWMubGlmZS5pc2FhYyxib2hhaXJpYy5udCxib2hhaXJpYy5vdA"  # Bohairic
	else:
		corpus_list = "_c=c2hlbm91dGUuYTIyLGpvaGFubmVzLmNhbm9ucyxzaGVub3V0ZS5hYnJhaGFtLHBzZXVkby5iYXNpbCxzaGVub3V0ZS5kaXJ0LHNhaGlkaWMub3Qsc2hlbm91dGUubmlnaHQscGlzdGlzLnNvcGhpYSxzaGVub3V0ZS50cnVlLHBzZXVkby50aW1vdGh5LHNoZW5vdXRlLnRodW5kZXJlZCxwc2V1ZG8uY2hyeXNvc3RvbSxwc2V1ZG8udGhlb3BoaWx1cyxkb2MucGFweXJpLHBhY2hvbWl1cy5pbnN0cnVjdGlvbnMsc2hlbm91dGUuaG91c2Usc2hlbm91dGUudW5rbm93bjVfMSxzaGVub3V0ZS5saXN0ZW4sbGlmZS5jeXJ1cyxzaGVub3V0ZS5lcnJzLG1hZ2ljYWwucGFweXJpLHBzZXVkby5jZWxlc3RpbnVzLHNoZW5vdXRlLnRob3NlLHNhaGlkaWNhLm50LHNoZW5vdXRlLmNydXNoZWQsbWFydHlyZG9tLnZpY3RvcixiZXNhLmxldHRlcnMsbGlmZS5qb2huLmthbHliaXRlcyxzaGVub3V0ZS51bmNlcnRhaW4ueHIscHNldWRvLmF0aGFuYXNpdXMuZGlzY291cnNlcyxkb3JtaXRpb24uam9obixsaWZlLnBoaWIscHNldWRvLmVwaHJlbSxsaWZlLm9ubm9waHJpdXMsYXBvcGh0aGVnbWF0YS5wYXRydW0sc2hlbm91dGUuc2Vla3MsbGlmZS5wYXVsLnRhbW1hLG15c3Rlcmllcy5qb2huLHNhaGlkaWMucnV0aCxzYWhpZGljYS5tYXJrLHNoZW5vdXRlLnBsYWNlLHNoZW5vdXRlLmVhZ2VybmVzcyxsaWZlLmFwaG91LHNoZW5vdXRlLndpdG5lc3MsbGlmZS5ldXN0YXRoaXVzLnRoZW9waXN0ZSxwcm9jbHVzLmhvbWlsaWVzLGpvaG4uY29uc3RhbnRpbm9wbGUsc2hlbm91dGUuY29uc2lkZXJpbmcsc2FoaWRpY2EuMWNvcmludGhpYW5zLHNoZW5vdXRlLnByaW5jZSxzaGVub3V0ZS5mb3gscHNldWRvLmZsYXZpYW51cyxsaWZlLmxvbmdpbnVzLmx1Y2l1cyxsaWZlLnBpc2VudGl1cyxhY3RzLnBpbGF0ZSxib29rLmJhcnRob2xvbWV3LGhlbGlhcyxsYW1lbnQubWFyeSxtZXJjdXJpdXMsdGhlb2Rvc2l1cy5hbGV4YW5kcmlh"
	segmentation = "_bt=bm9ybV9ncm91cA"  # Norm segmentation
	ordering = "o=random"  # Random ordering
	if " " in coptic:
		coptic = coptic.replace(" ","")
		query = "_q=" + urlsafe_b64encode('norm_group=/.*' + coptic + '.*/')
	elif " " in oref:
		oref_parts = oref.split(" ")
		morph_list =[]
		norm_list = []
		for part in oref_parts:
			morph_list.append('morph="'+part+'"')
			norm_list.append('norm="'+part+'"')
		query = " . ".join(morph_list) + " | "
		query += " . ".join(norm_list)
		query = "_q=" + urlsafe_b64encode(query)
	elif cs_pos in ["VSTAT","VIMP"]: # This is an inflected entry, look for norm and pos
		query = "_q=" + urlsafe_b64encode('norm="' + coptic + '" _=_ pos="'+str(cs_pos)+'"')
	else:
		if cs_pos in ["N","V"] and word_attr == "norm":  # Could be an inflected verb or noun
			query = "_q=" + urlsafe_b64encode(word_attr + '="' + coptic + '" _=_ pos="'+str(cs_pos)+'"')
		else:
			query = "_q=" + urlsafe_b64encode(word_attr + '="' + coptic + '"')

	return annis_base + "&".join([query,corpus_list,segmentation,ordering])


def get_annis_entity_query(coptic, entity_type):
	if " " in coptic:
		coptic = coptic.replace(" ","")
	coptic = strip_hyphens(coptic).encode("utf8")

	annis_base = "https://annis.copticscriptorium.org/annis/scriptorium#"
	corpus_list = "_c=Y29wdGljLnRyZWViYW5r"  # Currently just treebank
	segmentation = "_bt=bm9ybV9ncm91cA"  # norm segmentation
	ordering = "o=random"  # Random ordering
	q = 'entity="'+str(entity_type)+'" ->head lemma="' + coptic + '"'
	query = "_q=" + urlsafe_b64encode(q)

	return annis_base + "&".join([query,corpus_list,segmentation, ordering])


def lemma_exists(word):
	lemma_count = len(generic_query("select lemmas.Word from lemmas where lemmas.Word = ? and not lemmas.lemma = lemmas.word;",(word.decode("utf8"),)))>0
	if lemma_count > 0:
		lemma = get_lemmas_for_word(word)[0][0]
		regex_word = '.*\n' + lemma + '~.*'
		regex_word = regex_word
		found = generic_query("SELECT * FROM entries WHERE entries.name REGEXP ? ORDER BY ascii", (regex_word,))
		if len(found) > 0:
			return True
	return False


def get_lemmas_for_word(word):
	return generic_query("select Lemma, POS from lemmas where Word = ?;",(word.decode("utf8"),))


def get_morphs(word):
	return generic_query("select parts from morphs where compound = ?;",(word.decode("utf8"),))


def generic_query(sql,params):

	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	elif platform.system() == "Windows":
		con = lite.connect('.' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')

	with con:
		con.create_function("REGEXP", 2, lambda expr, item: re.search(expr.lower(), item.lower()) is not None)
		cur = con.cursor()
		cur.execute(sql,params)
		return cur.fetchall()


def only_coptic(text):
	text = re.sub(r'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲥⲟⲝⲡⲣⲥⲧⲫⲭⲩⲱϭϫϩϥϯ]','',text)
	return text


def link_greek(etym):

	m = re.search(r"cf\. Gr\.[^<>]+</span>([^<>]+)<i>",etym)
	if m is None:
		return etym
	else:
		greek = m.group(1).strip()
		greek= greek.decode("utf8")

	try:
		# Convert polytonic Greek to beta-code using perseids-tools/beta-code-py conversion table
		betamap = io.open("unicode_to_beta_code.tab", encoding="utf8").read().split("\n")
		UNICODE_TO_BETA_CODE_MAP  = dict((line.split("\t")[0],line.split("\t")[1]) for line in betamap)

		updated_map = {}
		updated_map.update(UNICODE_TO_BETA_CODE_MAP)

		chars = [c for c in greek]
		if not all([c in updated_map for c in chars]):
			return etym
		else:
			mapped = "".join((list(map(lambda x: updated_map.get(x, x), chars))))

			link = ' <a title="Look up in Logeion" href="https://logeion.uchicago.edu/'+greek+'">'+greek + '&nbsp;<img src="img/logeion.png" style="border: 1px solid black;"/></a> '
			link += '<a title="Look up in Perseus" href="http://www.perseus.tufts.edu/hopper/resolveform?type=exact&lookup='+mapped+'&lang=greek"><img src="img/perseus.png" style="border: 1px solid black;"/></a> '
			linked = re.sub(r'(cf\. Gr\.[^<>]*</span>)[^<>]+(<i>)',r'\1'+link+r'\2',etym)

			return linked.encode("utf8")
	except:
		# Beta code conversion failed, return unaltered string
		return etym


