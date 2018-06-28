# -*- coding: utf-8 -*-

import re
from . import dom_parser
from .dom_parser import parse_dom

def parseDOM(html, name='', attrs=None, ret=False):
    if attrs: attrs = dict((key, re.compile(value + ('$' if value else ''))) for key, value in attrs.items())
    results = dom_parser.parse_dom(html, name, attrs, ret)
    if ret:
        results = [result.attrs[ret.lower()] for result in results]
    else:
        results = [result.content for result in results]
    return results

