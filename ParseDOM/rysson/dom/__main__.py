# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

from .select import dom_select


def main():
    print('=== Tests ===')

    import requests
    import argparse
    import pprint
    pprint = pprint.PrettyPrinter(indent=2).pprint

    aparser = argparse.ArgumentParser()
    aparser.add_argument('url', metavar='URL', nargs=1, help='URL or file')
    aparser.add_argument('selectors', metavar='SEL', nargs='+', help='selector to parse')
    aparser.add_argument('--debug', action='store_true', help='debug info')
    args = aparser.parse_args()
    #print(args)

    url = args.url[0]
    if url.startswith('file://'):
        url = url[7:]
    if '://' in url:
        with requests.Session() as sess:
            res = sess.get(url)
            page = res.text
    else:
        with open(url) as f:
            page = f.read()
    #print(page[:200])
    for sel in args.selectors:
        pprint(dom_select(page, sel))


if __name__ == '__main__':
    main()
