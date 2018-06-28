# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function
from future import standard_library
from future.builtins import *
standard_library.install_aliases()

from unittest import TestCase
from unittest import skip as skiptest, skipIf as skiptestIf

from ..parseDOM import parseDOM
from ..parseDOM import aWord, aWordStarts, aStarts, aEnds, aContains
from ..parseDOM import DomMatch   # for test only



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

    def test_many_parts(self):
        with self.subTest('Parts: A'):
            self.assertEqual(parseDOM(['<a>A</a>', '<a>A</a>'], 'a'), ['A', 'A'])
        with self.subTest('Parts: A, A'):
            self.assertEqual(parseDOM(['<a>A</a><a>B</a>', '<a>A</a><a>B</a>'], 'a'), ['A', 'B', 'A', 'B'])
        with self.subTest('Parts: [A, B], [B A]'):
            self.assertEqual(parseDOM(['<a>A</a><b>B</b>', '<b>A</b><a>B</a>'], 'a'), ['A', 'B'])
        with self.subTest('Parts: A, B'):
            self.assertEqual(parseDOM(['<a>A</a><b>B</b>', '<a>A</a><b>B</b>'], 'a'), ['A', 'A'])
        with self.subTest('Parts: A > A'):
            self.assertEqual(parseDOM(['<a>A<a>B</a>C</a>', '<a>A<a>B</a>C</a>'], 'a'), ['A<a>B</a>C', 'B', 'A<a>B</a>C', 'B'])

    def test_many_parts_attr(self):
        with self.subTest('Parts: A[x], A'):
            self.assertEqual(parseDOM(['<a x="1">A</a><a>B</a>', '<a x="1">A</a><a>B</a>'], 'a', {'x': '1'}), ['A', 'A'])

    def test_many_parts_ret(self):
        with self.subTest('Parts: A, A {attr}'):
            self.assertEqual(parseDOM(['<a x="1">A</a><a>B</a>', '<a x="1">A</a><a>B</a>'], 'a', {}, ret='x'), ['1', '1'])
        with self.subTest('Parts: A[x], A {attr}'):
            self.assertEqual(parseDOM(['<a x="1">A</a><a>B</a>', '<a x="1">A</a><a>B</a>'], 'a', {'x': '1'}, ret='x'), ['1', '1'])

    #def test_x(self):
    #    pass
    #    #assert 0
    #    #self.assertEqual(1, 2)



class TestParseDOM_Extra(TestCase):

    def test_attr_bool(self):
        with self.subTest('A[x=True]'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': True}), [])
            self.assertEqual(parseDOM('<a x>A</a>', 'a', {'x': True}), ['A'])
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': True}), ['A'])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': True}), ['A'])
            self.assertEqual(parseDOM('<a y>A</a>', 'a', {'x': True}), [])
            self.assertEqual(parseDOM('<a y="">A</a>', 'a', {'x': True}), [])
            self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': True}), [])
        with self.subTest('A[x=False]'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': False}), ['A'])
            self.assertEqual(parseDOM('<a x>A</a>', 'a', {'x': False}), [])
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': False}), [])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': False}), [])
            self.assertEqual(parseDOM('<a x="1" y="2">A</a>', 'a', {'x': False}), [])
            self.assertEqual(parseDOM('<a y="2" x="1">A</a>', 'a', {'x': False}), [])
            self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': False}), ['A'])
        with self.subTest('A[x=None]'):
            self.assertEqual(parseDOM('<a x>A</a>', 'a', {'x': None}), ['A'])
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': None}), ['A'])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': None}), ['A'])
            self.assertEqual(parseDOM('<a y>A</a>', 'a', {'x': None}), ['A'])
            self.assertEqual(parseDOM('<a y="">A</a>', 'a', {'x': None}), ['A'])
            self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': None}), ['A'])

    def test_attr_empty(self):
        # atribbute value [] match any attrbuite value (attribute must exist)
        with self.subTest('A[x=[]]'):
            self.assertEqual(parseDOM('<a x>A</a>', 'a', {'x': []}), ['A'])
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': []}), ['A'])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': []}), ['A'])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': []}), ['A'])
            self.assertEqual(parseDOM('<a x="1 2">A</a>', 'a', {'x': []}), ['A'])
        with self.subTest('A[x=[]] - no attr'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': []}), [])
        with self.subTest('A[x=[]] - wrong attr'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', {'x': []}), [])
            self.assertEqual(parseDOM('<a y="">A</a>', 'a', {'x': []}), [])
            self.assertEqual(parseDOM('<a y="1">A</a>', 'a', {'x': []}), [])
        with self.subTest('A[x=[]] - wrong tag'):
            self.assertEqual(parseDOM('<b x="">A</b>', 'a', {'x': []}), [])
            self.assertEqual(parseDOM('<b y="">A</b>', 'a', {'x': []}), [])

    def test_attr_or(self):
        with self.subTest('A[x=1|2]'):
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': '1|2'}), [])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': '1|2'}), ['A'])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': '1|2'}), ['A'])
            self.assertEqual(parseDOM('<a x="3">A</a>', 'a', {'x': '1|2'}), [])
        with self.subTest('A[x=1|2][y]'):
            self.assertEqual(parseDOM('<a x="1" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="2" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="3" y="5">A</a>', 'a', {'x': '1|2', 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="1" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="2" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="3" y="6">A</a>', 'a', {'x': '1|2', 'y': '5'}), [])

    def test_attr_list_and(self):
        with self.subTest(r'A[x[\b1,2\b]]'):
            self.assertEqual(parseDOM('<a x="12">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b']}), ['A'])
            self.assertEqual(parseDOM('<a x="21">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b']}), [])
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b']}), [])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b']}), [])
            self.assertEqual(parseDOM('<a x="3">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b']}), [])
        with self.subTest(r'A[x[\b1,2\b]][y] (y matchs)'):
            self.assertEqual(parseDOM('<a x="12" y="5">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), ['A'])
            self.assertEqual(parseDOM('<a x="21" y="5">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="1" y="5">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="2" y="5">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="3" y="5">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
        with self.subTest(r'A[x[\b1,2\b]][y] (y does not match)'):
            self.assertEqual(parseDOM('<a x="12" y="6">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="21" y="6">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="1" y="6">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="2" y="6">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])
            self.assertEqual(parseDOM('<a x="3" y="6">A</a>', 'a', {'x': [r'\b1.*?', r'.*?2\b'], 'y': '5'}), [])

    def test_x(self):
        #self.assertEqual(1, 2)
        pass



class TestParseDOM_AttrFunc(TestCase):

    def test_attr_func_aWord_1(self):
        with self.subTest('One aWord() – empty'):
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': aWord('1')}), [])
        with self.subTest('One aWord() - single value'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x=" 1">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x="1 ">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x="11">A</a>', 'a', {'x': aWord('1')}), [])
        with self.subTest('One aWord() - many values'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x="1 2">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x="2 1">A</a>', 'a', {'x': aWord('1')}), ['A'])
            self.assertEqual(parseDOM('<a x="2 1 3">A</a>', 'a', {'x': aWord('1')}), ['A'])
        with self.subTest('One aWord() - miss'):
            self.assertEqual(parseDOM('<a x="12">A</a>', 'a', {'x': aWord('1')}), [])
            self.assertEqual(parseDOM('<a x="2 11 3">A</a>', 'a', {'x': aWord('1')}), [])
            self.assertEqual(parseDOM('<a x="2 3">A</a>', 'a', {'x': aWord('1')}), [])

    def test_attr_func_aWord_2(self):
        with self.subTest('Two aWord() - miss, no one exists'):
            self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a x="3">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a y="1 2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a y="11 22">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a x="12">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
        with self.subTest('Two aWord() - miss, one exists'):
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a x="2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a x="1 22">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
            self.assertEqual(parseDOM('<a x="11 2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), [])
        with self.subTest('Two aWord() - two exist'):
            self.assertEqual(parseDOM('<a x="1 2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="2 1">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="1 2 3">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="0 1 2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="0 1 2 3">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="0 2 1 3">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="1 0 2">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])
            self.assertEqual(parseDOM('<a x="2 0 1">A</a>', 'a', {'x': [ aWord('1'), aWord('2') ] }), ['A'])



class TestParseDOM_DomMatch(TestCase):
    # DomMach result, compatibile with Cherry dom_parse()

    def test_dommatch_base(self):
        with self.subTest('DomMatch ret'):
            self.assertEqual(parseDOM('<b>B</b>', 'a', ret=True), [])
            self.assertEqual(len(parseDOM('<a>A</a>', 'a', ret=True)), 1)
        with self.subTest('DomMatch type'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=True), [DomMatch({}, 'A')])
            self.assertEqual(type(parseDOM('<a>A</a>', 'a', ret=True)[0]), DomMatch)

    def test_dommatch_content(self):
        with self.subTest('DomMatch content by name'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=True)[0].content, 'A')
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret=True)[0].content, 'A')
        with self.subTest('DomMatch content by index'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=True)[0][1], 'A')
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret=True)[0][1], 'A')

    def test_dommatch_attr(self):
        with self.subTest('DomMatch attr by name'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=True)[0].attrs, {})
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret=True)[0].attrs, {'x': '1'})
        with self.subTest('DomMatch attr by index'):
            self.assertEqual(parseDOM('<a>A</a>', 'a', ret=True)[0][0], {})
            self.assertEqual(parseDOM('<a x="1">A</a>', 'a', ret=True)[0][0], {'x': '1'})
        with self.subTest('DomMatch many attrs'):
            self.assertEqual(parseDOM('<a x="1" y="2">A</a>', 'a', ret=True)[0].attrs, {'x': '1', 'y': '2'})
            self.assertEqual(parseDOM('<a y="2" x="1">A</a>', 'a', ret=True)[0].attrs, {'x': '1', 'y': '2'})

    def test_dommatch_source_list(self):
        sA, sAA = '<a>A</a>', '<a>A</a><a>A</a>'
        sAx, sAAx, sAxAx = '<a x="1">A</a>', '<a>A</a><a x="1">A</a>', '<a x="1">A</a><a x="1">A</a>'
        mA, mAA = DomMatch({}, sA), DomMatch({}, sAA)
        mAx, mAAx, mAxAx = DomMatch({}, sAx), DomMatch({}, sAAx), DomMatch({}, sAxAx)
        A, Ax = DomMatch({}, 'A'), DomMatch({'x': '1'}, 'A')
        with self.subTest('Source list -> DomMatch'):
            self.assertEqual(parseDOM([sA], 'a', ret=True), [A])
            self.assertEqual(parseDOM([sAA], 'a', ret=True), [A, A])
            self.assertEqual(parseDOM([sA, sA], 'a', ret=True), [A, A])
        with self.subTest('Source list (attr) -> DomMatch'):
            self.assertEqual(parseDOM([sAx], 'a', ret=True), [Ax])
            self.assertEqual(parseDOM([sAxAx], 'a', ret=True), [Ax, Ax])
            self.assertEqual(parseDOM([sAAx], 'a', ret=True), [A, Ax])
            self.assertEqual(parseDOM([sAx, sAx], 'a', ret=True), [Ax, Ax])

    def test_dommatch_source_dommatch_list(self):
        sA, sAA = '<a>A</a>', '<a>A</a><a>A</a>'
        sAx, sAAx, sAxAx = '<a x="1">A</a>', '<a>A</a><a x="1">A</a>', '<a x="1">A</a><a x="1">A</a>'
        mA, mAA = DomMatch({}, sA), DomMatch({}, sAA)
        mAx, mAAx, mAxAx = DomMatch({}, sAx), DomMatch({}, sAAx), DomMatch({}, sAxAx)
        A, Ax = DomMatch({}, 'A'), DomMatch({'x': '1'}, 'A')
        with self.subTest('Source DomMatch list -> DomMatch'):
            self.assertEqual(parseDOM([sA], 'a', ret=True), [A])
            self.assertEqual(parseDOM([sAA], 'a', ret=True), [A, A])
            self.assertEqual(parseDOM([sA, sA], 'a', ret=True), [A, A])
        with self.subTest('Source DomMatch list (attr) -> DomMatch'):
            self.assertEqual(parseDOM([mAx], 'a', ret=True), [Ax])
            self.assertEqual(parseDOM([mAxAx], 'a', ret=True), [Ax, Ax])
            self.assertEqual(parseDOM([mAAx], 'a', ret=True), [A, Ax])
            self.assertEqual(parseDOM([mAx, mAx], 'a', ret=True), [Ax, Ax])

    def test_dommatch_source_mixed_list(self):
        sA, sAA = '<a>A</a>', '<a>A</a><a>A</a>'
        sAx, sAAx, sAxAx = '<a x="1">A</a>', '<a>A</a><a x="1">A</a>', '<a x="1">A</a><a x="1">A</a>'
        mA, mAA = DomMatch({}, sA), DomMatch({}, sAA)
        mAx, mAAx, mAxAx = DomMatch({}, sAx), DomMatch({}, sAAx), DomMatch({}, sAxAx)
        A, Ax = DomMatch({}, 'A'), DomMatch({'x': '1'}, 'A')
        with self.subTest('Source mixed list -> DomMatch'):
            self.assertEqual(parseDOM([sA, mA], 'a', ret=True), [A, A])
            self.assertEqual(parseDOM([mA, sA], 'a', ret=True), [A, A])
        with self.subTest('Source mixed list (attr) -> DomMatch'):
            self.assertEqual(parseDOM([mAx], 'a', ret=True), [Ax])
            self.assertEqual(parseDOM([mAxAx], 'a', ret=True), [Ax, Ax])
            self.assertEqual(parseDOM([mAAx], 'a', ret=True), [A, Ax])
            self.assertEqual(parseDOM([mAx, mAx], 'a', ret=True), [Ax, Ax])

            #self.assertEqual(parseDOM('<a x="">A</a>', 'a', {'x': aWord('1')}), [])

