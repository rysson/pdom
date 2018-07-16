# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function

from .base import TestCase
from unittest import skip as skiptest, skipIf as skiptestIf

from ..dom import dom_select
from ..dom import aWord, aWordStarts, aStarts, aEnds, aContains
from ..dom import DomMatch   # for test only


class TestDomSelect(TestCase):

    def test_tag(self):
        self.assertEqual(dom_select('<a>A</a>', 'a'), ['A'])
        self.assertEqual(dom_select('<a>A</a>', 'b'), [])
        self.assertEqual(dom_select('<a>A1</a><a>A2</a>', 'a'), ['A1', 'A2'])

    def test_id_empty(self):
        self.assertEqual(dom_select('<a id="0">A</a>', '#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', '#1'), ['A'])
        self.assertEqual(dom_select('<a id="1">A</a><b id="2">B</b>', '#1'), ['A'])

    def test_id_tag(self):
        self.assertEqual(dom_select('<a id="0">A</a>', 'a#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'a#1'), ['A'])
        self.assertEqual(dom_select('<a>A</a>', 'b#1'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'b#1'), [])
        self.assertEqual(dom_select('<a id="1">A1</a><a>A2</a>', 'a#1'), ['A1'])
        self.assertEqual(dom_select('<a id="1">A1</a><a id="2">A2</a>', 'a#1'), ['A1'])

    def test_class_1_empty(self):
        self.assertEqual(dom_select('<a class="0">A</a>', '.1'), [])
        self.assertEqual(dom_select('<a class="1">A</a>', '.1'), ['A'])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="2">A2</a>', '.1'), ['A1'])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="1">A2</a>', '.1'), ['A1', 'A2'])
        self.assertEqual(dom_select('<a class="1">A</a><b class="1">B</b>', '.1'), ['A', 'B'])

    def test_class_1_tag(self):
        self.assertEqual(dom_select('<a class="0">A</a>', 'a.1'), [])
        self.assertEqual(dom_select('<a class="1">A</a>', 'a.1'), ['A'])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="2">A2</a>', 'a.1'), ['A1'])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="1">A2</a>', 'a.1'), ['A1', 'A2'])
        self.assertEqual(dom_select('<a class="1">A</a><b class="1">B</b>', 'a.1'), ['A'])

    def test_class_n_empty(self):
        self.assertEqual(dom_select('<a class="0 9">A</a>', '.1'), [])
        self.assertEqual(dom_select('<a class="1 2">A</a>', '.1'), ['A'])
        self.assertEqual(dom_select('<a class="2 1">A</a>', '.1'), ['A'])
        self.assertEqual(dom_select('<a class="0 1 2">A</a>', '.1'), ['A'])
        self.assertEqual(dom_select('<a class="11 2 3">A</a>', '.1'), [])

    def test_class_n_tag(self):
        self.assertEqual(dom_select('<a class="0 9">A</a>', 'a.1'), [])
        self.assertEqual(dom_select('<a class="1 2">A</a>', 'a.1'), ['A'])
        self.assertEqual(dom_select('<a class="1">A1</a><a class="11 2">A2</a>', 'a.1'), ['A1'])
        self.assertEqual(dom_select('<a class="1 2">A1</a><a class="1 3">A2</a>', 'a.1'), ['A1', 'A2'])
        self.assertEqual(dom_select('<a class="1 2 3">A</a><b class="1">B</b>', 'a.1'), ['A'])

    def test_id_class_empty(self):
        self.assertEqual(dom_select('<a id="0">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a class="0">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a class="2">A</a>', '#1.2'), [])
        self.assertEqual(dom_select('<a id="1" class="2">A</a>', '#1.2'), ['A'])
        self.assertEqual(dom_select('<a class="2" id="1">A</a>', '#1.2'), ['A'])
        self.assertEqual(dom_select('<a id="1" class="2 3">A</a>', '#1.2'), ['A'])

    def test_id_class_tag(self):
        self.assertEqual(dom_select('<a id="0">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a id="1">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a class="0">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a class="2">A</a>', 'a#1.2'), [])
        self.assertEqual(dom_select('<a id="1" class="2">A</a>', 'a#1.2'), ['A'])
        self.assertEqual(dom_select('<a class="2" id="1">A</a>', 'a#1.2'), ['A'])
        self.assertEqual(dom_select('<a id="1" class="2 3">A</a>', 'a#1.2'), ['A'])
        self.assertEqual(dom_select('<b id="1" class="2">B</b>', 'a#1.2'), [])
        self.assertEqual(dom_select('<b class="2" id="1">B</b>', 'a#1.2'), [])
        self.assertEqual(dom_select('<b id="1" class="2 3">B</b>', 'a#1.2'), [])

    def test_descend(self):
        self.assertEqual(dom_select('<a>A</a>', 'a b'), [])
        self.assertEqual(dom_select('<b>B</b>', 'a b'), [])
        self.assertEqual(dom_select('<a>A</a><b>B</b>', 'a b'), [])
        self.assertEqual(dom_select('<a>A<b>B</b></a>', 'a b'), ['B'])
        self.assertEqual(dom_select('<b>B</b><a>A</a>', 'a b'), [])
        self.assertEqual(dom_select('<b>B<a>A</a></b>', 'a b'), [])
        self.assertEqual(dom_select('<a><b><c>C</c></b></a>', 'a b'), ['<c>C</c>'])
        self.assertEqual(dom_select('<a><b><c>C</c></b></a>', 'a b c'), ['C'])

