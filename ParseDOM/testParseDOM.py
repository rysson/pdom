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

type_str = type('')
bytes_str = type(b'')
if sys.version_info >= (3,0):
    basestring = str


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
    line = []
    if args:
        line.append(', '.join(repr(a) for a in args))
    if kwargs:
        line.append(', '.join(str(k)+'='+repr(v) for k,v in kwargs.items()))
    line = ','.join(line)
    py2_setup = 'from testParseDOM import *; html=prepare_html()'
    html = prepare_html()
    vars = globals()
    vars.update(locals())
    for i in range(6):
        n = int(10**i)
        #check('mrknow.parseDOM', html, 'a')
        cmd = '{fun}(html, {line})'.format(fun=fun, line=line)
        if sys.version_info >= (3,0):
            t = T.timeit(cmd, number=n, globals=vars)
        else:
            t = T.timeit(cmd, 'from testParseDOM import prepare_html,mrknow,cherry,rysson; html=prepare_html()', number=n)
        if t > 0.2:
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

    html = prepare_html()

    allmods = ('mrknow', 'cherry', 'rysson')
    mods = ('cherry', 'rysson')
    if github:
        print('#### Python{py}\n\nTest | mrknow | cherry | rysson |\n----- | ----- | ----- | -----'.format(py=sys.version_info[0]))
        print(' | '.join(['tags'] + list('{t:.3f}'.format(t=check(mod + '.parseDOM', 'a')) for mod in mods)))
        print(' | '.join(['attrs'] + list('{t:.3f}'.format(t=check(mod + '.parseDOM', 'a', {'x': '1'})) for mod in mods)))
    else:
        for mod in allmods:
            t = check(mod + '.parseDOM', 'a')
            print('Tag:  Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
        for mod in allmods:
            t = check(mod + '.parseDOM', 'a', {'x': '1'})
            print('Attr: Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
        for mod in mods:
            t = check(mod + '.parse_dom', 'a')
            print('Node: Python{py}, module: {mod}, time: {t:.3f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
