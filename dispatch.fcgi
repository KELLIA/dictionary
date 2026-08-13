#!/usr/bin/python2
# -*- coding: utf-8 -*-

import cgi, re
from collections import OrderedDict
from wsgiref.simple_server import make_server

from helper import get_con
from search import search_main
from help import help_main
from about import about_main
from entry import entry_main
from network import network_main
from network_thumb import network_thumb_main
from results import results_main


class Request(object):
    pass


con = get_con()


def app(e, start_response):
    req = Request()
    # POST data
    req.form = cgi.FieldStorage(fp=e['wsgi.input'], environ=e)
    # GET data
    req.params = cgi.parse_qs(e['QUERY_STRING'])
    req.path = e['PATH_INFO']
    req.path = req.path.replace("coptic-dictionary-dispatch/","")

    start_response('200 OK', [('Content-type', 'text/html')])

    if req.path == '/' or req.path== '/search.py':
        return [search_main()] # .encode("utf8")]
    elif req.path == '/about.py':
        return [about_main()] # .encode("utf8")]
    elif req.path == '/help.py':
        return [help_main()] # .encode("utf8")]
    elif req.path == '/entry.py':
        return [entry_main(req.form, con=con)] #.encode("utf8")]
    elif req.path == '/results.py':
        page = results_main(req.form, con=con)
        if 'window.location' in page:  # Redirect to entry.py due to unique search result, serve that instead
            form = OrderedDict()
            getval = lambda k, d: form.__getitem__(k) if k in form else d
            setattr(form, "getvalue", getval)
            m = re.search(r'\?tla=([^&"]+)', page)
            if m is not None:  # Found via TLA ID
                form["tla"] = m.group(1)
                return [entry_main(form, con=con)]
            m = re.search(r'\?entry=([^&]+)&super=([^&"]+)', page)
            if m is not None:  # Found via entry and super entry
                form.update({"entry": m.group(1), "super": m.group(2)})
                return [entry_main(form, con=con)]
        return [results_main(req.form, con=con)] #.encode("utf8")]
    elif req.path == '/network.py':
        return [network_main(req.form, con=con).encode("utf8")]
    elif req.path == '/network_thumb.py':
        return [network_thumb_main(req.form, con=con).encode("utf8")]
    elif ".py" not in req.path:
        return [""]


server = make_server('127.0.0.1', 8764, app=app)
server.serve_forever()
