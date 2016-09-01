#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from helper import wrap

print "Content-type: text/html\n"

page_out = 	open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "howto.html",'r').read()

wrapped = wrap(page_out)

print wrapped