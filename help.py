#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
from helper import wrap


def help_main():
    page_out = 	open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "howto.html",'r').read()
    wrapped = wrap(page_out, caller="help")
    return wrapped


if __name__ == "__main__":
    print "Content-type: text/html\n"
    wrapped = help_main()
    print wrapped