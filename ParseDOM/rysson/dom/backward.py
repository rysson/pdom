# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

from .base import Result, DomMatch
from .search import dom_search

def parseDOM(html, name=None, attrs=None, ret=None, exclude_comments=False):
    return dom_search(html, name, attrs,
                      Result.Content if ret is None else ret,
                      exclude_comments=exclude_comments)

def parse_dom(html, name='', attrs=None, req=False, exclude_comments=False):
    return dom_search(html, name, attrs, ret=DomMatch,
                      exclude_comments=exclude_comments)

