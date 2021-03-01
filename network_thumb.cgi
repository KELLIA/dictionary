#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi, cgitb, platform, os
import sqlite3 as lite
from helper import wrap
cgitb.enable()

print "Content-type: text/html\n"

page = """
<script src="js/jquery-1.7.2.min.js"></script>
<script src="js/vis-network.min.js"></script>
<script src="js/term_network.js"></script>
<input type="hidden" name="target_data" id="target_data" value="**DATA**">
<input type="hidden" name="target_word" id="target_word" value="**WORD**">
<div id="mynetwork" style="height: 80px; width: 80px"></div>
<script>
load_data();
</script>
"""

if __name__ == "__main__":
    form = cgi.FieldStorage()
    params = {}
    word = cgi.escape(form.getvalue("word", "")).replace("(", "").replace(")", "").replace("=", "").replace("<","").strip()
    pos = cgi.escape(form.getvalue("pos", "--")).replace("(", "").replace(")", "").replace("=", "").strip()
    tla = cgi.escape(form.getvalue("tla", "--")).replace("(", "").replace(")", "").replace("=", "").strip()
    word = word.decode("utf8")
    if pos not in ["N","V","VSTAT","VIMP","PREP"] or len(word.strip())==0:
        rows = []
        page = """<div class="content">No network data found for your query</div>"""
    if platform.system() == 'Linux':
        con = lite.connect('alpha_kyima_rc1.db')
    else:
        con = lite.connect('utils' + os.sep + 'alpha_kyima_rc1.db')
    with con:
        cur = con.cursor()
        cur.execute("select pos, word, phrase, freq from networks where pos=? and word=? order by freq DESC limit 20", (pos,word))
        rows = cur.fetchall()
        if len(rows) < 1:
            rows = []
            page = """<div class="content">No network data found for your query</div>"""

    output = []
    for row in rows:
        output.append("||".join(list(row)[:-1] + [str(row[-1])]))

    tsv = "%%".join(output) + "\n"
    page = page.replace("**DATA**",tsv)
    page = page.replace("**WORD**",word)

    wrapped = page
    wrapped = wrapped.replace("Term network",
      'Term network for TLA form no. **TLA**: <span style="font-family: antinoouRegular, sans-serif; font-size: larger">' + word + '</span>')
    if tla != "--":
        wrapped = wrapped.replace("**TLA**",tla)
    else:
        wrapped = wrapped.replace("TLA form no. **TLA**:","")

    print wrapped.encode("utf8")


