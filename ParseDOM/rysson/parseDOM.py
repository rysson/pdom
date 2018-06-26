# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function
from future import standard_library
from future.builtins import *
standard_library.install_aliases()

import sys
import re
from collections import defaultdict


if sys.version_info < (3,0):
    type_str, type_bytes = unicode, str
else:
    type_str, type_bytes, unicode, basestring = str, bytes, str, str


class AttrDict(dict):
    """dict() + attribute access"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('AttrDict has no attribute "{}"'.format(key))

    def __setattr__(self, key, value):
        self[key] = value


def aWord(s):
    '''Realize [attribute~=value] selector'''
    return'''[^'"]*?(?<=['" ]){}(?=['" ])[^'"]*?'''.format(s)

def aWordStarts(s):
    '''Realize [attribute|=value] selector'''
    return'''[^'"]*?(?<=['" ]){}[^'"]*?'''.format(s)

def aStarts(s):
    '''Realize [attribute^=value] selector'''
    return'''(?<=['"]){}[^'"]*?'''.format(s)

def aEnds(s):
    '''Realize [attribute$=value] selector'''
    return'''[^'"]*?{}(?=['"])'''.format(s)

def aContains(s):
    '''Realize [attribute*=value] selector'''
    return u'''[^'"]*?{}[^'"]*?'''.format(s)


def parseDOM(html, name=u"", attrs={}, ret=False):
    # Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen
    # Refactoring by Robert Kalinowski <robert.kalinowski@sharkbits.com>

    #print('parseDOM: name="{name}", attrs={attrs}, ret={ret}'.format(**locals()))   # XXX DEBUG
    if isinstance(html, type_bytes):
        try:
            html = [html.decode("utf-8")] # Replace with chardet thingy
        except:
            html = [html]
    elif isinstance(html, type_str):
        html = [html]
    elif not isinstance(html, list):
        return u""

    pats = AttrDict()
    pats.anyTag       = r'''[\w-]+'''
    pats.anyAttrVal   = r'''(?:=(?:[^\s/>'"]+|"[^"]*?"|'[^']*?'))?'''
    pats.askAttrVal   = r'''(?:=(?:([^\s/>'"]+)|"([^"]*?)"|'([^']*?)'))?'''
    pats.anyAttr      = r'''(?:\s+[\w-]+{val})*'''.format(val=pats.anyAttrVal)
    pats.mtag         = lambda n: r'''{n}(?=[\s/>])'''.format(n=n)
    pats.mattr        = lambda n, v: (r'''\s+{n}(?:=(?:{v}(?=[\s/>])|"{v}"|'{v}'))''' \
                                      if v and v is not True else \
                                      r'''{n}(?=[\s/>=])''').format(n=n, v=v)
    pats.melem        = lambda t, a, v: \
        r'''<{tag}{anyAttr}{attr}{anyAttr}\s*/?>'''.format(tag=pats.mtag(t), attr=pats.mattr(a, v), **pats)  \
        if a else \
        r'''<{tag}{anyAttr}\s*/?>'''.format(tag=t, **pats)
    #pats.mbegin       = lambda n: r'''<{tag}{anyAttr}\s*(?P<end>/?)>'''.format(tag=t, **pats)
    #pats.mend         = lambda n: r'''</{tag}\s*>'''.format(tag=pats.mtag(n))
    pats.getTag       = r'''<([\w-]+(?=[\s/>]))'''

    if not name.strip():
        name = pats.anyTag   # any tag

    ret_lst = []
    for item in html:
        lst = []
        for key, vals in (attrs or {None: None}).items():
            if not isinstance(vals, list):
                vals = [ vals ]
            for val in vals:
                #lst2 = re.findall(pats.melem(name, key, val), item, re.S)
                lst2 = list((r.group(), r.span()) for r in re.finditer(pats.melem(name, key, val), item, re.S))
                if lst:
                    # Delete anything missing from the next list.
                    for i in range(len(lst)-1, -1, -1):  # or range(len(lst))[::-1]
                        if not lst[i] in lst2:
                            del lst[i]
                else:
                    # First match
                    lst = lst2

        #print('L', lst)
        if ret:
            # Get attribute value
            lst2 = []
            pat = r'''<{tag}{anyAttr}\s+{attr}{askAttrVal}{anyAttr}\s*/?>'''
            for match, (ms, me) in lst:
                if isinstance(ret, list):
                    # Many attributes at once
                    lst2.append(list(
                        a or b or c for rt in ret for a, b, c in re.findall(pat.format(tag=name, attr=rt, **pats), match, re.S)
                    ))
                else:
                    # Single attribute
                    lst2 += re.findall(pat.format(tag=name, attr=ret, **pats), match, re.S)
            lst = lst2
        else:
            # Element content (innerHTML)
            lst2 = []
            for match, (ms, me) in lst:
                if match.endswith('/>'):   # <tag/> has no content
                    lst2.append('')
                    continue
                # Recover tag name (important for "*")
                r = re.match(pats.getTag, match, re.S)
                tag = r.group(1) if r else name
                # find closing tag
                ce = me
                pat = '(?:<(?P<beg>{anyTag}){anyAttr}\s*>)|(?:</(?P<end>{anyTag})\s*>)'
                #print('CP', pat.format(tag=tag, **pats))
                tag_stack = [ tag ]
                for r in re.compile(pat.format(tag=tag, **pats), re.S).finditer(item, me):
                    #print('C', r.groupdict())
                    d = AttrDict(r.groupdict())
                    if d.beg:
                        tag_stack.append(d.beg)
                    elif d.end:
                        while tag_stack:
                            tag_stack, last = tag_stack[:-1], tag_stack[-1]
                            if last == d.end:
                                break
                        if not tag_stack:
                            ce = r.start()
                            break;
                lst2.append(item[me:ce])

                #start = ms
                #end = item.find(endstr, start)
                #pos = item.find("<" + name, start + 1 )

                #while pos < end and pos != -1:
                #    tend = item.find(endstr, end + len(endstr))
                #    if tend != -1:
                #        end = tend
                #    pos = item.find("<" + name, pos + 1)

                #if start == -1 and end == -1:
                #    temp = u""
                #elif start > -1 and end > -1:
                #    temp = item[start + len(match):end]
                #elif end > -1:
                #    temp = item[:end]
                #elif start > -1:
                #    temp = item[start + len(match):]

                #if ret:
                #    endstr = item[end:item.find(">", item.find(endstr)) + 1]
                #    temp = match + temp + endstr

                #item = item[item.find(temp, item.find(match)) + len(temp):]
                #lst2.append(temp)
            lst = lst2
        ret_lst += lst

    return ret_lst



def findInHtml(html, selectors):
    """
    Find data in HTML in simple quite fast way in pure Python.
    """
    print(' --- search for "{}"'.format(selectors))
    ret = []
    if isinstance(selectors, basestring):
        ret = None
        selectors = [ selectors ]
    rl_re = re.compile(r'''xxx''')   # TODO:  split elector by ","
    rs_re = re.compile(r'''(?P<tag>\w+)(?P<attr1>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)?|(?P<attr2>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)''')
    ra_re = re.compile(r'''#(?P<id>[^[\s.#]+)|\.(?P<class>[\w-]+)|\[(?P<attr>[\w-]+)(?:(?P<aop>[~|^$*]?=)(?:"(?P<aval1>[^"]*)"|'(?P<aval2>[^']*)'|(?P<aval0>(?<!['"])[^]]+)))?\]|::(?P<pseudo>\w+)(?:\((?P<psarg>\w+(?:,\s*\w+)*)\))?''')
    attrSelectors = {
        None:  lambda v: True,
        '=':   lambda v: v,
        '~=':  aWord,
        '|=':  aWordStarts,
        '^=':  aStarts,
        '$=':  aEnds,
        '*=':  aContains,
    }
    for selalt in selectors:
        res = []  # All matches for single selector
        for sel in selalt.split(','):  # TODO:  omit ',' in quotas
            part = html
            for rs in rs_re.finditer(sel):
                tag = rs.groupdict()['tag'] or u''
                ats = rs.groupdict()['attr1'] or rs.groupdict()['attr2'] or u''
                if tag == u'*':
                    tag = u''
                #print(f'tag="{tag}", attr="{ats}"')
                attrs, retat = defaultdict(lambda: []), []
                for ra in ra_re.finditer(ats):
                    #print('RA', ra.groupdict())
                    if ra.groupdict()['id']:
                        attrs['id'].append(ra.groupdict()['id'])
                    elif ra.groupdict()['class']:
                        attrs['class'].append(aWord(ra.groupdict()['class']))
                    elif ra.groupdict()['attr']:
                        key = ra.groupdict()['attr']
                        op  = ra.groupdict()['aop']
                        val = ra.groupdict()['aval0'] or ra.groupdict()['aval1'] or ra.groupdict()['aval2'] or u''
                        try:
                            attrs[key].append(attrSelectors[op](val))
                        except KeyError:
                            raise KeyError('Attribute selector "{op}" is not supported'.format(op=op))
                    elif ra.groupdict()['pseudo']:
                        pseudo = ra.groupdict()['pseudo']
                        psarg = ra.groupdict()['psarg'] or u''
                        if pseudo == 'attr':
                            if ',' in psarg:
                                retat += list(a.strip() for a in psarg.split(','))
                            else:
                                retat = psarg
                    #print('RA', ra.groupdict(), attrs)
                #print(' -RS', attrs)
                part = parseDOM(part, tag, dict(attrs), retat or False)
            #ret += parseDOM(html, sel)
            res += part
        if ret == None:
            ret = res
        else:
            ret.append(res)
    return ret


def test_findInHtml(html):
    #print(findInHtml(html, 'p'))
    #print(findInHtml(html, 'p b[u]'))
    #print(findInHtml(html, 'p[q=2] b[a="x y"][b="z"][e]'))
    #print(findInHtml(html, '[q=2].stare#z #a.nowe b.inne[a~="x y"][b="z"].nie'))
    #findInHtml(html, 'p[a=1]')
    print(findInHtml(html, 'p[a~="22"]'))
    print(findInHtml(html, 'p[a~="22"]::attr(b), div[a~="22"]::attr(c)'))
    print(findInHtml(html, 'p[a*="2 3"]'))
    print(findInHtml(html, 'p[a="2 3"]'))
    print(findInHtml(html, 'p[a="1 2 3"]'))
    print(findInHtml(html, 'div[c=5]::attr(d)'))
    print(findInHtml(html, 'div[c=5]'))

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
    html = u'''
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

    #test_parseDOM(html)
    print(' - - - - -')
    test_findInHtml(html)

