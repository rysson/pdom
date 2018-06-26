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
        if t > 0.5:
            return t / n


def test_pat_1():
    for pat in (
        '<x><a/></x><a>Z</a>',
        '<x><a/><a>Z</a></x>',
        '<a>z<x>x<a/>y</x></a>Q</a>',
        '<a>z<x>x<a>aa</a>y</x></a>',
        '<a>z<x>x<a>y</x></a>Q</a>',
    ):
        print('----- Pattern: {}'.format(pat))
        for mod in ('mrknow', 'cherry', 'rysson'):
            eval('print("{0}: ", {0}.parseDOM("{1}", "a"))'.format(mod, pat), globals(), locals())
    exit()

if __name__ == '__main__':
    print('zażółć', 3/2, 3//2, type(''), type(b''), bytes, basestring)
    test_pat_1()

    html = prepare_html()

    for mod in ('mrknow', 'cherry', 'rysson'):
        t = check(mod + '.parseDOM', 'a')
        print('Tag:  Python{py}, module: {mod}, time: {t:.6f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
    for mod in ('mrknow', 'cherry', 'rysson'):
        t = check(mod + '.parseDOM', 'a', {'x': '1'})
        print('Attr: Python{py}, module: {mod}, time: {t:.6f} [s]'.format(py=sys.version_info[0], mod=mod, t=t))
