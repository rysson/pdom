# -*- coding: utf-8 -*-

#from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys
import timeit as T
import mrknow
import cherry
import rysson
from rysson.pdom import Node

PY2 = sys.version_info < (3,0)
PY3 = sys.version_info >= (3,0)

type_str = type('')
bytes_str = type(b'')
if PY3:
    basestring = str


class cls(object):
    def __init__(self, C):
        self._cls = C
    def __str__(self):
        return self._cls.__name__
    def __repr__(self):
        return self._cls.__name__


def prepare_html():
    a = '<a>aaa</a>'
    b = '<b>bb1{a}bb2{a}bb3</b>\n'.format(**locals())
    c = '<c>cc1{a}cc2{b}cc3{b}cc4</c>\n'.format(**locals())
    ax = dict((i, '<a x="{i}">aaa:x{i}</a>'.format(**locals())) for i in range(1, 4))
    L = locals()
    bx = dict((i, '<b x="{i}">bb0:x{i}{a}bb1:x{i}{ax[1]}bb2:x{i}{ax[2]}bb9:x{i}</b>\n'.format(i=i, **L)) for i in range(1, 4))
    L = locals()
    cx = dict((i, '<c x="{i}">cc:x{i}{ax[1]}cc0:x{i}{b}cc1:x{i}{bx[1]}cc2:x{i}{bx[2]}cc9:x{i}</c>\n'.format(i=i, **L)) for i in range(1, 4))
    return '<div>\n' + (''.join(cx.values()) * 1000) + '</div>\n'


def check(fun, *args, **kwargs):
    prepare_html = kwargs.pop('prepare_html', globals()['prepare_html'])
    line = []
    if args:
        line.append(', '.join(repr(a) for a in args))
    if kwargs:
        line.append(', '.join(str(k)+'='+repr(v) for k,v in kwargs.items()))
    line = ','.join(line)
    if PY2:
        py2_setup = 'from testParseDOM import prepare_html,mrknow,cherry,rysson,Node; html=prepare_html()'
    else:
        html = prepare_html()
        vars = globals()
        vars.update(locals())
    cmd = '{fun}(html, {line})'.format(fun=fun, line=line)
    for i in range(6):
        n = int(10**i)
        #check('mrknow.parseDOM', html, 'a')
        if PY2:
            t = T.timeit(cmd, py2_setup, number=n)
        else:
            t = T.timeit(cmd, number=n, globals=vars)
        if t > 0.2:
            return t / n
    return t / n


def test_pat_1(github=False):
    if github:
        #print("parseDOM('...', 'a' [, {'x':'1'} ]) | mrknow | cherry | rysson\n---- | ---- | ---- | ----")
        print("parseDOM('...', 'a') | mrknow | cherry | rysson\n---- | ---- | ---- | ----")
    for pat in (
        '<a>A</a>Q',
        '<a>A<a>B</a>C</a>Q',
        '<a>A<a/>B</a>Q',
        #'<x><a/></x><a>Z</a>Q',
        #'<x><a/><a>Z</a></x>Q',
        #'<a>z<x>x<a/>y</x></a>Q</a>Q',
        #'<a>z<x>x<a>aa</a>y</x></a>Q',
        #'<a>z<x>x<a>y</x></a>Q</a>R',
        '<a>A<x>B<a>C</x>D</a>Q</a>R',
        '<a>A</a><a x="1">B</a>Q',
        '<a z=">">A</a>Q',
        #('<a x="1">A</a><a x="2">B</a>Q', {'x': '1'}, False),
        #('<a x="1">A</a><a y="2">B</a>Q', {'x': '1'}, False),
        #('<a x="1">A</a><a x="1" y="2">B</a>Q', {'x': '1'}, False),
        #('<a x="1">A</a><a x="1" y="2">B</a>Q', {'x': '1', 'y': '2'}, False),
        ('<a x="1">A</a>Q', {'x': '1'}, 'x'),
        ('<a x="1">A</a>Q', {'x': '1'}, 'y'),
        ('<a x="1" x="2">A</a>Q', {'x': '1'}, 'x'),
    ):
        attr, ret = {}, False
        if not isinstance(pat, basestring):
            pat, attr, ret = pat
        if github:
            if attr:
                line = [ "`{}`, `{}`".format(pat, attr) ]
            else:
                line = [ "`{}`".format(pat) ]
        else:
            print('----- Pattern: {}'.format(pat))
        match = rysson.parseDOM(pat, 'a', attr)
        for mod in ('mrknow', 'cherry', 'rysson'):
            if github:
                lst = eval('{0}.parseDOM("""{1}""", "a", attr, ret)'.format(mod, pat), globals(), locals())
                res = '[' + ', '.join("'{}'".format('`{}`'.format(v) if v else '') for v in lst) + ']'
                if match == lst:
                    res = '**\033[32;1m{}\033[0m**'.format(res)
                line.append(res)
            else:
                eval('print("{0}: ", {0}.parseDOM("""{1}""", "a", attr, ret))'.format(mod, pat), globals(), locals())
        if github:
            print(' | '.join(line))
    exit()

if __name__ == '__main__':
    github = sys.argv[1:2] == ['--github']
    print('zażółć', 3/2, 3//2, type(''), type(b''), bytes, basestring)
    #test_pat_1(github=github)

    #html = prepare_html()

    def html_attr():
        return (('<a x="1">A</a>' * 999) + '<a x="1" y="2">') * 1000
    if False:
        print('-- search --')
        print('attr -:   {t:.3f}'.format(t=check('rysson.dom_search', 'a', ret=cls(Node), prepare_html=html_attr)))
        print('attr x:   {t:.3f}'.format(t=check('rysson.dom_search', 'a', {'x': True}, ret=cls(Node), prepare_html=html_attr)))
        print('-- select --')
        print('attr -:   {t:.3f}'.format(t=check('rysson.dom_select', 'a', prepare_html=html_attr)))
        print('attr x:   {t:.3f}'.format(t=check('rysson.dom_select', 'a[x]', prepare_html=html_attr)))
        print('attr x,y: {t:.3f}'.format(t=check('rysson.dom_select', 'a[x][y]', prepare_html=html_attr)))
        print('attr y,x: {t:.3f}'.format(t=check('rysson.dom_select', 'a[y][x]', prepare_html=html_attr)))


    def html_contains():
        return ('<a>A' + ('<b>B</b>' * 999) + 'C</a>') * 1000
    def html_contains_mass():
        return '<a>A</a>' * 1000000
    if False:
        print('-- select --')
        print('contains a:   {t:.3f}'.format(t=check('rysson.dom_select', 'a', prepare_html=html_contains))),
        print('contains a.A: {t:.3f}'.format(t=check('rysson.dom_select', 'a:contains(A)', prepare_html=html_contains))),
        print('contains a.C: {t:.3f}'.format(t=check('rysson.dom_select', 'a:contains(C)', prepare_html=html_contains))),
        print('contains a.X: {t:.3f}'.format(t=check('rysson.dom_select', 'a:contains(X)', prepare_html=html_contains))),
        print('  --mass a.A: {t:.3f}'.format(t=check('rysson.dom_select', 'a:contains(A)', prepare_html=html_contains_mass))),
        print('  --mass a.X: {t:.3f}'.format(t=check('rysson.dom_select', 'a:contains(X)', prepare_html=html_contains_mass))),


    allmods = ('mrknow', 'cherry', 'rysson')
    mods = ('cherry', 'rysson')
    print('-- compare modules {} --\n'.format(', '.join(allmods)))
    if github:
        print('#### Python{py}\n\nTest  | mrknow | cherry | rysson |\n----- | ----- | ----- | -----'.format(py=sys.version_info[0]))
        print(' | '.join(['tags '] + list('{t:.3f}'.format(t=check(mod + '.parseDOM', 'a')) for mod in allmods)))
        print(' | '.join(['attrs'] + list('{t:.3f}'.format(t=check(mod + '.parseDOM', 'a', {'x': '1'})) for mod in allmods)))
        print('> rysson.Node: {t:.3f}'.format(t=check('rysson.parseDOM', 'a', ret=cls(Node))))
    else:
        for mod in allmods:
            t = check(mod + '.parseDOM', 'a')
            print('Tag:  Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
        print('> rysson.Node: {t:.3f}'.format(t=check('rysson.parseDOM', 'a', ret=cls(Node))))
        for mod in allmods:
            t = check(mod + '.parseDOM', 'a', {'x': '1'})
            print('Attr: Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
        for mod in mods:
            t = check(mod + '.parse_dom', 'a')
            print('Node: Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
        for mod in 'rysson',:
            t = check(mod + '.dom_select', 'a')
            print('SelN: Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))

