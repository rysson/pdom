#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function
from future import standard_library
from future.builtins import *
standard_library.install_aliases()

import sys
import re
from collections import defaultdict
from rysson import *
#from mrknow import *
#from cherry import *
from unittest import TestCase
from unittest import skip as skiptest, skipIf as skiptestIf

html = '''
<ul class="a", data="vvv">
<a href="a/a">Aa</a> qwe aaa
<a href="a/b">Ab</a> asd aaa
<a href="a/c">Ac</a> zxc aaa
</ul>
<ul class="b" data="nnn">
<a href="b/a">Ba</a> qwe bbb
<a href="b/b">Bb</a> asd bbb
<a href="b/c">Bc</a> zxc bbb
</ul>
<ul class="a c", data="mmm">
<a href="c/a">Ca</a> qwe ccc
<a href="c/b">Cb</a> asd ccc
<a href="c/c">Cc</a> zxc ccc
</ul>
<p a="1" b="2">12a</p>
<p b="2" a="1">12b</p>
<p a="1">12-c</p>
<p b="2">12-d</p>
<p c="3" e="żółć">12-<b>33</b>-e</p>
<div c="3">12-<b>33</b>-e</div>
<p a="1 2 3">1.2.3</p>
<p a="1 22 3">1.22.3</p>
<p a="22 1 3">22.1.3</p>
<p a="1 3 22" b=42>1.3.22</p>
<p a="1 020 3">1.020.3</p>
<p a="1 022 3">1.022.3</p>
<p a="1 220 3">1.220.3</p>
<div a="1 22 3" c="44">1.22.3</div>
<div a="22 1 3" c="45">22.1.3</div>
<div c="4">c4..<b z="9">bz9</b></div>
<div
 c="5"
 d="<b>BB</b>">
 c4..
 <b
  z="0">
  bz0
 </b>
</div>
'''

class MrParseDOM(TestCase):

    def test_tag(self):
        self.assertEqual(parseDOM('<a>A</a>', 'a'), ['A'])
        self.assertEqual(parseDOM('<a>A</a><a>B</a>', 'a'), ['A', 'B'])
        self.assertEqual(parseDOM('<a>A</a><b>B</b>', 'a'), ['A'])
        self.assertEqual(parseDOM('<b>B</b><a>A</a>', 'a'), ['A'])
        self.assertEqual(parseDOM('<z><a>A</a></z>', 'a'), ['A'])

    #@skiptest('Not fixed yet')
    def test_nested(self):
        with self.subTest('A > A'):
            self.assertEqual(parseDOM('<a>A<a>B</a></a>', 'a'), ['A<a>B</a>', 'B'])
        with self.subTest('A > A > A'):
            self.assertEqual(parseDOM('<a>A<a>B<a>C</a></a></a>', 'a'), ['A<a>B<a>C</a></a>', 'B<a>C</a>', 'C'])

    def test_no_attrs(self):
        self.assertEqual(parseDOM('<a x="1">A</a>', 'a'), ['A'])
        self.assertEqual(parseDOM('<a>A</a><a x="1">B</a>', 'a'), ['A', 'B'])

    def test_1_attrs(self):
        self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': "1"}), [])
        self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': "1"}), ['A'])
        self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': "1"}), [])
        self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': "1"}), [])
        self.assertEqual(parseDOM('<a>A</a><a x="1">B</a>', 'a', {'x': "1"}), ['B'])
        self.assertEqual(parseDOM('<a x="1">A</a><a>B</a>', 'a', {'x': "1"}), ['A'])
        self.assertEqual(parseDOM('<a x="1">A<a>B</a></a>', 'a', {'x': "1"}), ['A<a>B</a>'])

    def test_content(self):
        self.assertEqual(parseDOM('<a>A</a>', 'a'), ['A'])
        self.assertEqual(parseDOM('<a z=">">A</a>', 'a'), ['A'])


def test_findInHtml(html):
    #print(findInHtml(html, 'p'))
    #print(findInHtml(html, 'p b[u]'))
    #print(findInHtml(html, 'p[q=2] b[a="x y"][b="z"][e]'))
    #print(findInHtml(html, '[q=2].stare#z #a.nowe b.inne[a~="x y"][b="z"].nie'))
    #findInHtml(html, 'p[a=1]')
    print(findInHtml(html, 'p[a~="22"]::attr(b), div[a~="22"]::attr(c)'))
    print(findInHtml(html, 'p[a*="2 3"]'))
    print(findInHtml(html, 'p[a="2 3"]'))
    print(findInHtml(html, 'p[a="1 2 3"]'))
    print(findInHtml(html, 'div[c=5]::attr(d)'))

def test_parseDOM(html):
    r = parseDOM(html, 'ul', {'class': 'a(?: c)?'})
    print(r)
    r1 = parseDOM(r, 'a')
    print(r1)
    r2 = parseDOM(r, 'a', ret='href')
    print(r2)
    print(list(zip(r1, r2)))
    print(parseDOM(html, 'p', {'a': '1', 'b': '2'}))
    print(parseDOM(html, 'p', {'a': [aWord('1'), aWord('2')]}))
    print(parseDOM(html, 'p', {'a': [aWord('1'), aContains('2')]}))
    print(parseDOM(html, 'p', {'a': aStarts('2')}))
    print(parseDOM(html, 'p', {'a': aEnds('2')}))
    print(parseDOM(html, 'p', {'a': aWordStarts('2')}))

if __name__ == '__main__':
    #test_parseDOM(html)
    print(' - - - - -')
    #test_findInHtml(html)
    print(parseDOM('<a>A<a>B</a></a>', 'a'))


