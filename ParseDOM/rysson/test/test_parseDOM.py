# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function
from future import standard_library
from future.builtins import *
standard_library.install_aliases()

from unittest import TestCase
from unittest import skip as skiptest, skipIf as skiptestIf

from ..parseDOM import parseDOM


class TestParseDOM(TestCase):

    def test_tag(self):
        with self.subTest('A'):
            self.assertEqual(parseDOM('<a>A</a>', 'a'), ['A'])
        with self.subTest('A, A'):
            self.assertEqual(parseDOM('<a>A</a><a>B</a>', 'a'), ['A', 'B'])
        with self.subTest('A, X'):
            self.assertEqual(parseDOM('<a>A</a><x>X</x>', 'a'), ['A'])
        with self.subTest('X, A'):
            self.assertEqual(parseDOM('<x>X</x><a>A</a>', 'a'), ['A'])
        with self.subTest('X > A'):
            self.assertEqual(parseDOM('<x><a>A</a></x>', 'a'), ['A'])
        with self.subTest('A > X'):
            self.assertEqual(parseDOM('<a><x>A</x></a>', 'a'), ['<x>A</x>'])

    #@skiptest('Not fixed yet')
    def test_tag_nested(self):
        with self.subTest('A > A'):
            self.assertEqual(parseDOM('<a>A<a>B</a></a>', 'a'), ['A<a>B</a>', 'B'])
        with self.subTest('A > A ...'):
            self.assertEqual(parseDOM('<a>A<a>B</a>C</a>Q', 'a'), ['A<a>B</a>C', 'B'])
            self.assertEqual(parseDOM('<a>A<a></a>C</a>Q', 'a'), ['A<a></a>C', ''])
            self.assertEqual(parseDOM('<a><a>B</a>C</a>Q', 'a'), ['<a>B</a>C', 'B'])
            self.assertEqual(parseDOM('<a>A<a>B</a></a>Q', 'a'), ['A<a>B</a>', 'B'])
            self.assertEqual(parseDOM('<a><a>B</a></a>Q', 'a'), ['<a>B</a>', 'B'])
            self.assertEqual(parseDOM('<a><a></a></a>Q', 'a'), ['<a></a>', ''])
        with self.subTest('A > A > A'):
            self.assertEqual(parseDOM('<a>A<a>B<a>C</a></a></a>', 'a'), ['A<a>B<a>C</a></a>', 'B<a>C</a>', 'C'])
        with self.subTest('A, A > A'):
            self.assertEqual(parseDOM('<a>C</a><a>A<a>B</a></a>', 'a'), ['C', 'A<a>B</a>', 'B'])
        with self.subTest('A > A, A'):
            self.assertEqual(parseDOM('<a>A<a>B</a></a><a>C</a>', 'a'), ['A<a>B</a>', 'B', 'C'])
        with self.subTest('A > A, A > A'):
            self.assertEqual(parseDOM('<a>A<a>B</a></a><a>C<a>D</a></a>', 'a'), ['A<a>B</a>', 'B', 'C<a>D</a>', 'D'])
        with self.subTest('A > X > A ...'):
            self.assertEqual(parseDOM('<a>A<x>B<a>C</a>D</x>E</a>Q', 'a'), ['A<x>B<a>C</a>D</x>E', 'C'])

    def test_tag_single(self):
        with self.subTest('A/'):
            self.assertEqual(parseDOM('<a/>', 'a'), [''])
        with self.subTest('A /'):
            self.assertEqual(parseDOM('<a />', 'a'), [''])
        with self.subTest('X > A/, A'):
            self.assertEqual(parseDOM('<x><a/></x><a>A</a>', 'a'), ['', 'A'])
        with self.subTest('X > A /, A'):
            self.assertEqual(parseDOM('<x><a /></x><a>A</a>', 'a'), ['', 'A'])
        with self.subTest('X > A/, A ...'):
            self.assertEqual(parseDOM('<x><a/></x><a>A</a>Q', 'a'), ['', 'A'])
        with self.subTest('X > A /, A ...'):
            self.assertEqual(parseDOM('<x><a /></x><a>A</a>Q', 'a'), ['', 'A'])
        with self.subTest('X > ( A/, A )'):
            self.assertEqual(parseDOM('<x><a/><a>A</a></x>', 'a'), ['', 'A'])
        with self.subTest('X > ( A /, A )'):
            self.assertEqual(parseDOM('<x><a /></x><a>A</a></x>', 'a'), ['', 'A'])
        with self.subTest('X > ( A/, A ) ...'):
            self.assertEqual(parseDOM('<x><a/><a>A</a></x>Q', 'a'), ['', 'A'])
        with self.subTest('X > ( A /, A ) ...'):
            self.assertEqual(parseDOM('<x><a /><a>A</a></x>Q', 'a'), ['', 'A'])
        with self.subTest('X > ( A /, A ... )'):
            self.assertEqual(parseDOM('<x><a /><a>A</a>Q</x>', 'a'), ['', 'A'])
        with self.subTest('X > ( A/, A ... )'):
            self.assertEqual(parseDOM('<x><a/><a>A</a>Q</x>', 'a'), ['', 'A'])

    def test_tag_nested_single(self):
        with self.subTest('A > A/'):
            self.assertEqual(parseDOM('<a>A<a/>B</a>', 'a'), ['A<a/>B', ''])
            self.assertEqual(parseDOM('<a>A<a/></a>', 'a'), ['A<a/>', ''])
            self.assertEqual(parseDOM('<a><a/>B</a>', 'a'), ['<a/>B', ''])
            self.assertEqual(parseDOM('<a><a/></a>', 'a'), ['<a/>', ''])
        with self.subTest('A > A /'):
            self.assertEqual(parseDOM('<a>A<a />B</a>', 'a'), ['A<a />B', ''])
            self.assertEqual(parseDOM('<a>A<a /></a>', 'a'), ['A<a />', ''])
            self.assertEqual(parseDOM('<a><a />B</a>', 'a'), ['<a />B', ''])
            self.assertEqual(parseDOM('<a><a /></a>', 'a'), ['<a />', ''])
        with self.subTest('A > A/ ...'):
            self.assertEqual(parseDOM('<a>A<a/>B</a>Q', 'a'), ['A<a/>B', ''])
        with self.subTest('A > A / ...'):
            self.assertEqual(parseDOM('<a>A<a />B</a>Q', 'a'), ['A<a />B', ''])
        with self.subTest('A > A/ ... /a'):
            self.assertEqual(parseDOM('<a>A<a/>B</a>Q</a>', 'a'), ['A<a/>B', ''])
        with self.subTest('A > A / ... /a'):
            self.assertEqual(parseDOM('<a>A<a />B</a>Q</a>', 'a'), ['A<a />B', ''])
        with self.subTest('A > X > A/ ...'):
            self.assertEqual(parseDOM('<a>A<x>B<a/>C</x>D</a>Q', 'a'), ['A<x>B<a/>C</x>D', ''])
        with self.subTest('A > X > A / ...'):
            self.assertEqual(parseDOM('<a>A<x>B<a />C</x>D</a>Q', 'a'), ['A<x>B<a />C</x>D', ''])
        with self.subTest('A > X > A/ ... /a'):
            self.assertEqual(parseDOM('<a>A<x>B<a/>C</x>D</a>Q</a>', 'a'), ['A<x>B<a/>C</x>D', ''])
        with self.subTest('A > X > A / ... /a'):
            self.assertEqual(parseDOM('<a>A<x>B<a />C</x>D</a>Q</a>', 'a'), ['A<x>B<a />C</x>D', ''])

    def test_tag_broken_nested(self):
        with self.subTest('A > X > ~A~ ...'):
            self.assertEqual(parseDOM('<a>A<x>B<a>C</x>D</a>Q', 'a'), ['A<x>B<a>C</x>D', 'C'])
        with self.subTest('A > X > ~A~ ... /a'):
            self.assertEqual(parseDOM('<a>A<x>B<a>C</x>D</a>Q</a>', 'a'), ['A<x>B<a>C</x>D', 'C'])
        with self.subTest('A > X > ( ~A~, ~A~ ) ... /a'):
            self.assertEqual(parseDOM('<a>A<x>B<a>C<a>D</x>E</a>Q</a>', 'a'), ['A<x>B<a>C<a>D</x>E', 'C<a>D', 'D'])
        with self.subTest('A > ( X > ~A~, X > ~A~ ) ... /a'):
            self.assertEqual(parseDOM('<a>A<x>B<a>C</x>D<x>E<a>F</x>G</a>Q</a>', 'a'), ['A<x>B<a>C</x>D<x>E<a>F</x>G', 'C', 'F'])

    def test_tag_broken_nested_single(self):
        '<a>z<x>x<a>aa</a>y</x></a>',
        '<a>z<x>x<a>y</x></a>Q</a>',

    def test_no_attrs(self):
        self.assertEqual(parseDOM('<a x="1">A</a>', 'a'), ['A'])
        self.assertEqual(parseDOM('<a>A</a><a x="1">B</a>', 'a'), ['A', 'B'])

    def test_1_attrs(self):
        self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': '1'}), [])
        self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': '1'}), ['A'])
        self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': '1'}), [])
        self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': '1'}), [])
        self.assertEqual(parseDOM('<a>A</a><a x="1">B</a>', 'a', {'x': '1'}), ['B'])
        self.assertEqual(parseDOM('<a x="1">A</a><a>B</a>', 'a', {'x': '1'}), ['A'])
        self.assertEqual(parseDOM('<a x="1">A<a>B</a></a>', 'a', {'x': '1'}), ['A<a>B</a>'])

    def test_2_attrs(self):
        self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': '1', 'y': '2'}), [])
        self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': '1', 'y': '2'}), [])
        self.assertEqual(parseDOM('<a y="2">A</a>', 'a', {'x': '1', 'y': '2'}), [])
        self.assertEqual(parseDOM('<a x="2" y="2">A</a>', 'a', {'x': '1', 'y': '2'}), [])
        self.assertEqual(parseDOM('<a x="1" y="3">A</a>', 'a', {'x': '1', 'y': '2'}), [])
        self.assertEqual(parseDOM('<a x="1" y="2">A</a>', 'a', {'x': '1', 'y': '2'}), ['A'])
        self.assertEqual(parseDOM('<a>A</a><a x="1" y="2">B</a>', 'a', {'x': '1', 'y': '2'}), ['B'])
        self.assertEqual(parseDOM('<a x="1">A</a><a x="1" y="2">B</a>', 'a', {'x': '1', 'y': '2'}), ['B'])
        self.assertEqual(parseDOM('<a y="2">A</a><a x="1" y="2">B</a>', 'a', {'x': '1', 'y': '2'}), ['B'])
        self.assertEqual(parseDOM('<a x="1" y="2">A</a><a x="1" y="2">B</a>', 'a', {'x': '1', 'y': '2'}), ['A', 'B'])
        self.assertEqual(parseDOM('<a x="1" y="2"><a>A</a></a>', 'a', {'x': '1', 'y': '2'}), ['<a>A</a>'])

    def test_content(self):
        with self.subTest('A'):
            self.assertEqual(parseDOM('<a>A</a>', 'a'), ['A'])
            self.assertEqual(parseDOM('<a>A</a>Q', 'a'), ['A'])
            self.assertEqual(parseDOM('Q<a>A</a>', 'a'), ['A'])
            self.assertEqual(parseDOM('Q<a>A</a>Q', 'a'), ['A'])
        with self.subTest('Omit ">" in attr'):
            self.assertEqual(parseDOM('<a z=">">A</a>Q', 'a'), ['A'])

    def test_ret_attr(self):
        with self.subTest('A {content}'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=False), ['A'])
        with self.subTest('A[x] {content}'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret=False), ['A'])
        with self.subTest('A {attr}'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret='x'), [])
        with self.subTest('A[x] {attr}'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret='x'), ['1'])


    def test_x(self):
        assert 0
        self.assertEqual(1, 2)


class TestParseDOM_Extra(TestCase):

    def test_attr_or(self):
        with self.subTest('A[x=1|2]'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': '1|2'}), ['A'])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': '1|2'}), ['A'])
            self.assertEqual(parseDOM('<a x="3">A</a>', 'a', {'x': '1|2'}), [''])
        with self.subTest('A[x=1|2][y]'):
            self.assertEqual(parseDOM('<a x="1" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="2" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="3" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="1" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="2" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="3" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [''])
        #with self.subTest('A[x[]][y[]]'):

    @skiptest('Not fixed yet')
    def test_attr_list_and(self):
        with self.subTest('A[x[]]'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': ['1', '2']}), ['A'])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': ['1', '2']}), ['A'])
            self.assertEqual(parseDOM('<a x="3">A</a>', 'a', {'x': ['1', '2']}), [''])
        with self.subTest('A[x[]][y]'):
            self.assertEqual(parseDOM('<a x="1" y="5">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="2" y="5">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="3" y="5">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="1" y="6">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="2" y="6">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), [''])
            self.assertEqual(parseDOM('<a x="3" y="6">A</a>', 'a', {'x': ['1', '2'], 'y': '5'}), [''])
        #with self.subTest('A[x[]][y[]]'):

    def test_x(self):
        #self.assertEqual(1, 2)
        pass

