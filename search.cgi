#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import re
import cgi, cgitb
import os
from helper import wrap
cgitb.enable()

print("Content-type: text/html\n")
        
if __name__ == "__main__":
	search_page = """
    <form id="search" action="results.cgi" method="GET" accept-charset="UTF-8">
	<table>
	<tr>
	<td>
        Coptic Word: </td><td><input type="text" name="coptic" id="coptic" class="keyboardInput" lang="cop">
        </td></tr>
	<tr>
        <td>Dialect:</td>
        <td><select name="dialect" id="dialect_select" class="search_dropdown">
            <option value="any">Any</option>
            <option value="A">A: &nbsp;&nbsp;&nbsp;Akhmimic</option>
            <option value="K">Ak: &nbsp;Old Coptic</option>
            <option value="B">B:&nbsp;&nbsp;&nbsp; Bohairic</option>
            <option value="F">F:&nbsp; &nbsp;&nbsp;Fayyumic</option>
            <option value="M">M: &nbsp;&nbsp;Mesokemic</option>
            <option value="L">L: &nbsp;&nbsp;&nbsp;Lycopolitan</option>
            <option value="P">P: &nbsp;&nbsp;&nbsp;Proto-Theban</option>
            <option value="S">S: &nbsp;&nbsp;&nbsp;Sahidic</option>
            <option value="V">V: &nbsp;&nbsp;&nbsp;South Fayyumic Greek</option>
            <option value="W">W: &nbsp;&nbsp;Crypto-Mesokemic Greek</option>
            <option value="?">?: &nbsp;&nbsp;&nbsp;Greek (usage unclear)</option>
        </select>
        </td></tr>
        <tr><td>Scriptorium&nbsp;tag:</td>
        <td><select name="pos" class="search_dropdown" id="pos_select">
            <option value="any">Any</option>
            <option value="A">A</option>
            <option value="ART">ART</option>
            <option value="C">C</option>
            <option value="CONJ">CONJ</option>
            <option value="N">N</option>
            <option value="NEG">NEG</option>
            <option value="NUM">NUM</option>
            <option value="PDEM">PDEM</option>
            <option value="PINT">PINT</option>
            <option value="PPER">PPER</option>
            <option value="PPERO">PPERO</option>
            <option value="PPOS">PPOS</option>
            <option value="PREP">PREP</option>
            <option value="PTC">PTC</option>
            <option value="V">V</option>
            <option value="VBD">VBD</option>
            <option value="VSTAT">VSTAT</option>
        </select>
        </td></tr>
        <tr><td>Definition:</td><td> <input type="text" name="definition" id="definition"></td></tr>
        <tr><td>&nbsp;</td><td><div>Definition text: 
        <div>&nbsp;&nbsp;<input type="radio" name="def_search_type" value="exact sequence" checked>exact sequence</input><br/>
        &nbsp;&nbsp;<input type="radio" name="def_search_type" value="all words">contains all words</input></div></div>
        <div>Definition language:<br>
        <select name="lang" class="search_dropdown" id="lang">
        	<option value="any">Any</option>
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="de">German</option>
        </select>

        </div>
		</td></tr></table>
        <input type="submit" value="Search" class="search_button" id="search_submit">
    </form>
"""

	wrapped = wrap(search_page)
	kbd_include = """
	<script type="text/javascript" src="js/keyboard.js" charset="UTF-8"></script>
	<link rel="stylesheet" type="text/css" href="css/keyboard.css?version=2">
	"""
	wrapped = wrapped.replace("<head>\n","<head>"+kbd_include)
	print(wrapped)
	
