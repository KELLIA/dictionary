#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
from helper import wrap

print "Content-type: text/html\n"

page_out = 	open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "about.html",'r').read()

wrapped = wrap(page_out)

print wrapped