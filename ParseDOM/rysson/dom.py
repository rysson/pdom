# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function
#try:
#    from future import standard_library
#    from future.builtins import *
#    standard_library.install_aliases()
#except ImportError:
#    print('WARNING: no furure module')

import sys
import re
from collections import defaultdict
from collections import namedtuple
from inspect import isclass
try:
    from requests import Response
except ImportError:
    Response = None

if sys.version_info < (3,0):
    type_str, type_bytes = unicode, str
    class Enum: pass
else:
    type_str, type_bytes, unicode, basestring = str, bytes, str, str
    from enum import Enum



class AttrDict(dict):
    """dict() + attribute access"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('AttrDict has no attribute "{}"'.format(key))

    def __setattr__(self, key, value):
        self[key] = value


class Patterns(AttrDict):
    """All usefull patterns"""
    def __init__(self):
        pats = self
        pats.anyTag       = r'''[\w-]+'''
        pats.anyAttrVal   = r'''(?:=(?:[^\s/>'"]+|"[^"]*?"|'[^']*?'))?'''
        pats.askAttrVal   = r'''(?:=(?:(?P<val1>[^\s/>'"]+)|"(?P<val2>[^"]*?)"|'(?P<val3>[^']*?)'))?'''
        pats.anyAttrName  = r'''[\w-]+'''
        pats.askAttrName  = r'''(?P<attr>[\w-]+)'''
        pats.anyAttr      = r'''(?:\s+{anyAttrName}{anyAttrVal})*'''.format(**pats)
        pats.mtag         = lambda n: r'''{n}(?=[\s/>])'''.format(n='(?:{})'.format(n))
        pats.mattr        = lambda n, v: \
                r'''(?:\s+{attr}{anyAttrVal})'''.format(attr=n, **pats) \
                if v is True else \
                r'''\s+{n}(?:=(?:{v}(?=[\s/>])|"{v}"|'{v}'))'''.format(n='(?:{})'.format(n), v='(?:{})'.format(v or ''))
        pats.melem        = lambda t, a, v: \
            r'''<{tag}(?:\s+(?!{attr}){anyAttrName}{anyAttrVal})*\s*/?>'''.format(tag=pats.mtag(t), attr=a, **pats)  \
            if a and v is False else \
            r'''<{tag}{anyAttr}{attr}{anyAttr}\s*/?>'''.format(tag=pats.mtag(t), attr=pats.mattr(a, v), **pats)  \
            if a else \
            r'''<{tag}{anyAttr}\s*/?>'''.format(tag=pats.mtag(t), **pats)
        pats.getTag       = r'''<([\w-]+(?=[\s/>]))'''
        pats.openCloseTag = '(?:<(?P<beg>{anyTag}){anyAttr}\s*>)|(?:</(?P<end>{anyTag})\s*>)'.format(**pats)
        pats.nodeTag = '(?:<(?P<beg>{anyTag}){anyAttr}(?:\s*(?P<slf>/))?\s*>)|(?:</(?P<end>{anyTag})\s*>)'.format(**pats)


pats = Patterns()
remove_tags_re = re.compile(pats.nodeTag)

class DomMatch(namedtuple('DomMatch', ['attrs', 'content'])):
    __slots__ = ()
    #__slots__ = (match)

    @property
    def text(self):
        return remove_tags_re.sub('', self.content)


class Result(Enum):
    Content = 0
    Node = 1
    Text = 2
    InnerHTML = Content
    OuterHTML = 3


class ExtraResult(list):
    r"""
    Helper to tell dom_search() more details about result.

    Parameters
    ----------
    vals : list
        List of object (e.g. attributes) in result.
    separate : bool, default False
        If true dom_search() return content and values separated.
    """
    def __init__(self, vals, separate=False, skip_missing=True):
        super(ExtraResult, self).__init__(vals)
        self.separate = separate
        self.skip_missing = skip_missing


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


def _tostr(s):
    """Change bytes to string (also in list)"""
    if isinstance(s, DomMatch):
        s = s.content
    elif isinstance(s, (list, tuple)):
        return list(_tostr(z) for z in s)
    if s is None or s is False or s is True:
        s = ''
    elif isinstance(s, type_bytes):
        try:
            s =  s.decode("utf-8")
        except:
            pass
    elif not isinstance(s, basestring):
        s = str(s)
    return s



def dom_search(html, name=None, attrs=None, ret=None, exclude_comments=False):
    """
    Simple parse HTML/XML to get tags.

    Function parses HTML/XML, finds tags with attribites
    and returns matching tags content or attribute.

    Paramters
    ---------
    html : str or bytes or DomMatch or list of str or list of bytes or list of DomMatch
        HTML/XML source. Directly or list of HTML/XML parts.
    name : str or bytes or None
        Tag name ot None if you want to match any tag. Can be regex string (e.g. "div|p").
    attr : dict or None
        Attributes to match or None if attributes has no matter. See below.
    ret : str or list of str or DomMatch or False or None
        What to return. Tag content if False or None, DomMatch nodes or attributes.

    Returns
    -------
    list of str
        List of matched tags content (innerHTML) or matched attribute values if ret is used.
    list of DomMatch
        List of DomMatch mached nodes (attribute and content tuples) if ret is DomMatch.

    """
    # Author: Robert Kalinowski <robert.kalinowski@sharkbits.com>
    # Idea is taken form parseDOM() by Tobias and Henrik:
    #   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

    #print('dom_search: name="{name}", attrs={attrs}, ret={ret}'.format(**locals()))   # XXX DEBUG
    if Response and isinstance(html, Response):
        html = html.text
    if isinstance(html, DomMatch) or not isinstance(html, (list, tuple)):
        html = [ html ]


    if exclude_comments:
        # TODO: make it good, it's to simple, should ommit quotation in attribute
        re_comments = re.compile('<!--.*?-->', re.DOTALL)

    name = _tostr(name).strip()
    if not name or name == '*':
        name = pats.anyTag   # any tag

    class BreakAtrrloop(Exception): pass

    def find_closing(name, match, item, ms, me):
        if match.endswith('/>'):   # <tag/> has no content
            return me, me
        # Recover tag name (important for "*")
        r = re.match(pats.getTag, match, re.DOTALL)
        tag = r.group(1) if r else name
        # find closing tag
        ce = me
        tag_stack = [ tag ]
        for r in re.compile(pats.openCloseTag, re.DOTALL).finditer(item, me):
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
        return me, ce

    ret_lst, ret_nodes = [], []
    try:
        separate = ret.separate
        skip_missing = ret.skip_missing
    except AttributeError:
        separate = False
        skip_missing = True

    # return list of values if ret is list  [a] -> [x]
    # else return values                    a   -> x
    if isinstance(ret, (list, tuple)):
        retlstadd = ret_lst.append
    else:
        retlstadd, ret = ret_lst.extend, [ ret ]

    for item in html:
        item = _tostr(item)
        if exclude_comments:
            item = re_comments.sub(item, '')
        if not item:
            continue

        lst = None
        try:
            for key, vals in (attrs or {None: None}).items():
                if not isinstance(vals, list):
                    vals = [ vals ]
                elif not vals:   # empty values means any value
                    vals = [ True ]
                for val in vals:
                    vkey = key
                    #print(f'-- key: {vkey!r}, val: "{val}"')
                    if key and val is None:  # Skip this attribute
                        vkey = None
                        #print(f'-> key: {vkey!r}, val: "{val}"')
                    #print('PAT', pats.melem(name, vkey, val))
                    lst2 = list((r.group(), r.span()) for r in re.finditer(pats.melem(name, vkey, val), item, re.DOTALL))
                    #print(' L2', lst2)
                    #print(' L ', lst)
                    if lst is None:   # First match
                        lst = lst2
                    else:             # Delete anything missing from the next list.
                        for i in range(len(lst)-1, -1, -1):
                            if not lst[i] in lst2:
                                del lst[i]
                    if not lst:
                        break
        except BreakAtrrloop:
            pass
        if not lst:
            continue
        #print('LST', lst)

        def parse_node(match, ms, me):
            attrs = dict((attr.lower(), a or b or c) \
                for attr, a, b, c in \
                re.findall(r'\s+{askAttrName}{askAttrVal}'.format(**pats), match, re.DOTALL))
            cs, ce = find_closing(name, match, item, ms, me)
            #print('node', match, DomMatch(attrs, item[cs:ce]))
            return DomMatch(attrs, item[cs:ce])

        for match, (ms, me) in lst:
            #print('MATCH', match, ms, me)
            lst2 = []
            node = None
            if separate:
                node = parse_node(match, ms, me)
                ret_nodes.append(node)
            for ritem in ret:
                if ritem is True:
                    ritem = Result.Node
                elif ritem is False or ritem is None:
                    ritem = Result.Content
                elif isclass(ritem) and issubclass(ritem, DomMatch):
                    ritem = Result.Node

                #print('  -> ritem', ritem)
                if ritem == Result.Content:
                    # Element content (innerHTML)
                    cs, ce = find_closing(name, match, item, ms, me)
                    lst2.append(item[cs:ce])
                elif ritem == Result.Text:
                    # Only text (remove all tags from content)
                    cs, ce = find_closing(name, match, item, ms, me)
                    lst2.append(remove_tags_re.sub('', item[cs:ce]))
                elif ritem == Result.Node:
                    # Get full node (content and all attributes)
                    if node is None:
                        node = parse_node(match, ms, me)
                    lst2.append(node)
                else:   # attribute
                    if node is None:
                        node = parse_node(match, ms, me)
                    try:
                        lst2.append(node.attrs[ritem])
                    except KeyError:
                        if not skip_missing:
                            lst2.append(None)
            if lst2 or not skip_missing:
                retlstadd(lst2)

    if separate:
        return ret_lst, ret_nodes
    return ret_lst





def dom_select(html, selectors):
    """
    Find data in HTML in simple quite fast way in pure Python.
    """
    #print(' --- search for "{}"'.format(selectors))
    ret = []
    if isinstance(selectors, basestring):
        ret = None
        selectors = [ selectors ]
    rl_re = re.compile(r'''xxx''')   # TODO:  split elector by ","
    # find single tag (with params)
    rs_re = re.compile(r'''(?P<tag>\w+)(?P<attr1>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)?|(?P<attr2>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)''')
    # find params (id, class, attr and pseudo)
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
            part, out = html, []
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
                            retat += list(a.strip() for a in psarg.split(','))
                        elif pseudo == 'content':
                            retat.append(Result.Content)
                        elif pseudo == 'node':
                            retat.append(Result.Node)
                        elif pseudo == 'text':
                            retat.append(Result.Text)
                        else:
                            raise KeyError('Pseudo-class "{op}" is not supported'.format(op=pseudo))
                    #print('RA', ra.groupdict(), attrs)
                #print(' -RS', attrs)
                if retat:
                    part = dom_search(part, tag, dict(attrs), retat)
                else:
                    out = part = dom_search(part, tag, dict(attrs))
            #ret += dom_search(html, sel)
            res += part
        if ret == None:
            ret = res
        else:
            ret.append(res)
    return ret


# --- Old (alien) APIs ---

def parseDOM(html, name=None, attrs=None, ret=None, exclude_comments=False):
    return dom_search(html, name, attrs, ret)

def parse_dom(html, name='', attrs=None, req=False, exclude_comments=False):
    return dom_search(html, name, attrs, ret=DomMatch)


# --- Module methods ---

search = dom_search
select = dom_select



if __name__ == '__main__':
    def test_dom_select(html):
        #print(dom_select(html, 'p'))
        #print(dom_select(html, 'p b[u]'))
        #print(dom_select(html, 'p[q=2] b[a="x y"][b="z"][e]'))
        #print(dom_select(html, '[q=2].stare#z #a.nowe b.inne[a~="x y"][b="z"].nie'))
        #dom_select(html, 'p[a=1]')
        print(dom_select(html, 'p[a~="22"]'))
        print(dom_select(html, 'p[a~="22"]::attr(b), div[a~="22"]::attr(c)'))
        print(dom_select(html, 'p[a*="2 3"]'))
        print(dom_select(html, 'p[a="2 3"]'))
        print(dom_select(html, 'p[a="1 2 3"]'))
        print(dom_select(html, 'div[c=5]::attr(d)'))
        print(dom_select(html, 'div[c=5]'))

    def test_dom_search(html):
        r = dom_search(html, 'ul', {'class': 'a(?: c)?'})
        print(r)
        r1 = dom_search(r, 'a')
        print(r1)
        r2 = dom_search(r, 'a', ret='href')
        print(r2)
        print(list(zip(r1, r2)))
        print(dom_search(html, 'p', {'a': '1', 'b': '2'}))
        print(dom_search(html, 'p', {'a': [aWord('1'), aWord('2')]}))
        print(dom_search(html, 'p', {'a': [aWord('1'), aContains('2')]}))
        print(dom_search(html, 'p', {'a': aStarts('2')}))
        print(dom_search(html, 'p', {'a': aEnds('2')}))
        print(dom_search(html, 'p', {'a': aWordStarts('2')}))

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

    #exit()

    #test_dom_search(html)
    print(' - - - - -')
    #test_dom_select(html)
    #print(dom_select('<a>A1</a><a>A2</a><b>B1</b><b>B2</b>', 'a'))
    #print(dom_select('<a>A1</a><a>A2</a><b>B1</b><b>B2</b>', ['a', 'b']))
    #print(dom_select('<a x=1><b y=2>B</b></a>', 'a::attr(x) b::attr(y)'))
    #print(dom_search('<a x=1><b y=2 z=3>B</b></a>', 'a', ret=False))
    #print(dom_search('<a x=1><b y=2 z=3>B</b></a>', 'a', ret='x'))
    #print(dom_search('<a x=1><b y=2 z=3>B</b></a>', 'a', ret=['x']))
    #print(dom_search('<a x=1><b y=2 z=3>B</b></a>', 'b', ret=['y', 'z']))

    #print(dom_search('<a x=11>A11<b y=12 z=13>B1</b>A12</a><a x=21>A21<b y=22 z=23>B2</b>A22</a>',
    #                 'a',
    #                 ret=ExtraResult(['x', 'y', 'z', Result.Text])
    #                 #ret='x'
    #                 ))

    print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret='x'))
    print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret=['x']))
    print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret=ExtraResult(['x'], separate=True)))
    #print(dom_select('<a x=11>A11<b y=12 z=13>B1</b>A12</a><a x=21>A21<b y=22 z=23>B2</b>A22</a>',
    #                 'a::attr(x)::text()'))


