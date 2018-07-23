# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function

from .base import TestCase
from unittest import skip as skiptest, skipIf as skiptestIf

from ..dom import dom_select
from ..dom import aWord, aWordStarts, aStarts, aEnds, aContains
from ..dom import Node, DomMatch   # for test only


class N(Node):
    __slots__ = Node.__slots__ + ('content', )
    def __init__(self, content, attrs=None, tag=None, **kwargs):
        if tag is None:
            tag = content[:1].lower()
        super(N, self).__init__('<{}>'.format(tag))
        self._Node__name = tag
        self.content = content
        self._Node__attrs = attrs or kwargs or {}
    def __eq__(self, other):
        #for a in 'name', 'attrs', 'content':
        #    print('====?', getattr(self, a), getattr(other, a))
        return self.name == other.name and self.attrs == other.attrs and self.content == other.content

class NC(N):
    def __init__(self, content, cls=None, tag=None, **kwargs):
        super(NC, self).__init__(content, tag=tag, **kwargs)
        if cls is not None:
            self._Node__attrs['class'] = cls


class TestDomSelect(TestCase):

    def test_tag(self):
        self.assertEqual(dom_select('<a>A</a>', 'a'), [N('A')])
        self.assertEqual(dom_select('<a>A</a>', 'b'), [])
        self.assertEqual(dom_select('<a>A1</a><a>A2</a>', 'a'), [N('A1'), N('A2')])

    def test_id_empty(self):
        self.assertEqual(dom_select('<a id="0">A</a>', '#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', '#1'), [N('A', id='1')])
        self.assertEqual(dom_select('<a id="1">A</a><b id="2">B</b>', '#1'), [N('A', id='1')])

    def test_id_tag(self):
        self.assertEqual(dom_select('<a id="0">A</a>', 'a#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'a#1'), [N('A', id='1')])
        self.assertEqual(dom_select('<a>A</a>', 'b#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'b#1'), [])
        self.assertEqual(dom_select('<a id="1">A1</a><a>A2</a>', 'a#1'), [N('A1', id='1')])
        self.assertEqual(dom_select('<a id="1">A1</a><a id="2">A2</a>', 'a#1'), [N('A1', id='1')])

    def test_class_1_empty(self):
        self.assertEqual(dom_select('<a class="0">A</a>', '.1'), [])
        self.assertEqual(dom_select('<a class="1">A</a>', '.1'), [NC('A', '1')])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="2">A2</a>', '.1'), [NC('A1', '1')])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="1">A2</a>', '.1'), [NC('A1', '1'), NC('A2', '1')])
        self.assertEqual(dom_select('<a class="1">A</a><b class="1">B</b>', '.1'), [NC('A', '1'), NC('B', '1')])

    def test_class_1_tag(self):
        self.assertEqual(dom_select('<a class="0">A</a>', 'a.1'), [])
        self.assertEqual(dom_select('<a class="1">A</a>', 'a.1'), [NC('A', '1')])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="2">A2</a>', 'a.1'), [NC('A1', '1')])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="1">A2</a>', 'a.1'), [NC('A1', '1'), NC('A2', '1')])
        self.assertEqual(dom_select('<a class="1">A</a><b class="1">B</b>', 'a.1'), [NC('A', '1')])

    def test_class_n_empty(self):
        self.assertEqual(dom_select('<a class="0 9">A</a>', '.1'), [])
        self.assertEqual(dom_select('<a class="1 2">A</a>', '.1'), [NC('A', '1 2')])
        self.assertEqual(dom_select('<a class="2 1">A</a>', '.1'), [NC('A', '2 1')])
        self.assertEqual(dom_select('<a class="0 1 2">A</a>', '.1'), [NC('A', '0 1 2')])
        self.assertEqual(dom_select('<a class="11 2 3">A</a>', '.1'), [])

    def test_class_n_tag(self):
        self.assertEqual(dom_select('<a class="0 9">A</a>', 'a.1'), [])
        self.assertEqual(dom_select('<a class="1 2">A</a>', 'a.1'), [NC('A', '1 2')])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="11 2">A2</a>', 'a.1'), [NC('A1', '1')])
        self.assertEqual(dom_select('<a class="1 2">A1</a><a class="1 3">A2</a>', 'a.1'), [NC('A1', '1 2'), NC('A2', '1 3')])
        self.assertEqual(dom_select('<a class="1 2 3">A</a><b class="1">B</b>', 'a.1'), [NC('A', '1 2 3')])

    def test_id_class_empty(self):
        self.assertEqual(dom_select('<a id="0">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a class="0">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a class="2">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a id="1" class="2">A</a>', '#1.2'), [NC('A', '2', id='1')])
        self.assertEqual(dom_select('<a class="2" id="1">A</a>', '#1.2'), [NC('A', '2', id='1')])
        self.assertEqual(dom_select('<a id="1" class="2 3">A</a>', '#1.2'), [NC('A', '2 3', id='1')])

    def test_id_class_tag(self):
        self.assertEqual(dom_select('<a id="0">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a class="0">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a class="2">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a id="1" class="2">A</a>', 'a#1.2'), [NC('A', '2', id='1')])
        self.assertEqual(dom_select('<a class="2" id="1">A</a>', 'a#1.2'), [NC('A', '2', id='1')])
        self.assertEqual(dom_select('<a id="1" class="2 3">A</a>', 'a#1.2'), [NC('A', '2 3', id='1')])
        self.assertEqual(dom_select('<b id="1" class="2">B</b>', 'a#1.2'), [])
        self.assertEqual(dom_select('<b class="2" id="1">B</b>', 'a#1.2'), [])
        self.assertEqual(dom_select('<b id="1" class="2 3">B</b>', 'a#1.2'), [])

    def test_descend(self):
        self.assertEqual(dom_select('<a>A</a>', 'a b'), [])
        self.assertEqual(dom_select('<b>B</b>', 'a b'), [])
        self.assertEqual(dom_select('<a>A</a><b>B</b>', 'a b'), [])
        self.assertEqual(dom_select('<a>A<b>B</b></a>', 'a b'), [N('B')])
        self.assertEqual(dom_select('<b>B</b><a>A</a>', 'a b'), [])
        self.assertEqual(dom_select('<b>B<a>A</a></b>', 'a b'), [])
        self.assertEqual(dom_select('<a><b><c>C</c></b></a>', 'a b'), [N('<c>C</c>', tag='b')])
        self.assertEqual(dom_select('<a><b><c>C</c></b></a>', 'a b c'), [N('C')])

