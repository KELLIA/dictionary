#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
from helper import wrap


def about_main():
    page_out = 	open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "about.html",'r').read()
    wrapped = wrap(page_out, caller="about")
    return wrapped


if __name__ == "__main__":
    print "Content-type: text/html\n"
    wrapped = about_main()
    print wrapped