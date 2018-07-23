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


class NoResult(list):
    __slots__ = ()
    def __init__(self):
        super(NoResult, self).__init__()
    def append(self, v):
        raise NotImplementedError('NoResult is readonly')
    def extend(self, v):
        raise NotImplementedError('NoResult is readonly')
    def __setitem__(self, key, val):
        raise NotImplementedError('NoResult is readonly')
    # TODO: all methods



class AttrDict(dict):
    """dict() + attribute access"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('AttrDict has no attribute "{}"'.format(key))

    def __setattr__(self, key, value):
        self[key] = value


regex = re.compile


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

    @property
    def text(self):
        return remove_tags_re.sub('', self.content)


class Result(Enum):
    NoResult = 0
    Content = 1
    Node = 2
    Text = 3
    InnerHTML = Content
    OuterHTML = 4
    DomMatch = 91

    # --- internals -- 
    RemoveItem = 'REMOVE'


class MissingAttr(Enum):
    #: Do not skip any attribures, return None if missing.
    NoSkip = 0
    #: Skip only if attribute was direct requested (e.g. for 'a')
    #: else return None (e.g. for ['a']).
    SkipIfDirect = 1
    #: Skipp all missing attributes.
    SkipAll = 2


class ResultParam(object):
    r"""
    Helper to tell dom_search() more details about result.

    Parameters
    ----------
    args : str or list of str
        Object or list of object (e.g. attributes) in result.
    separate : bool, default False
        If true dom_search() return content and values separated.
    missing
        How to handle missing attributes, see MissingAttr.
    sync : bool or Result.RemoveItem
        If True result caontains None (or Result.RemoveItem) if not match
        If False result contains only matching items.
    """
    def __init__(self, args,
                 separate=False,
                 missing=MissingAttr.SkipIfDirect,
                 sync=False):
        self.args = args
        self.separate = separate
        self.missing = missing
        self.sync = sync


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
    return '''[^'"]*?{}[^'"]*?'''.format(s)


def _tostr(s):
    """Change bytes to string (also in list)"""
    if isinstance(s, Node):
        s = s.content
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


def _make_html_list(html):
    r"""Helper. Make list of HTML part."""
    if Response and isinstance(html, Response):
        html = html.text
    if isinstance(html, DomMatch) or not isinstance(html, (list, tuple)):
        html = [ html ]
    return html


def find_node(name, match, item, ms, me):
    r"""
    Helper. Find closing tag for given `name` tag.

    Parameters
    ----------
    name : str
        Tag name (name or regex pattern, can be e.g. '.*').
    match : str
        Found full tag string (tag with attributes).
    item : str
        Original HTML string or HTML part string.
    ms : int
        Offset in `item` for `match`.
    me : int
        Offset in `item` for `match` end.

    Returns
    -------
    ts : int
        Tag start ('<') index in `item`.
    cs : int
        Content start index in `item`.
        It's also tag end (one characteter after '>') index.
    ce : int
        Content end index in `item`.
        It's also closing tag start ('</') index.
    te : int
        Closing tag end index (one characteter after closing '>') in `item`.

    Function returns index of parsed node:

        <tag attr="val">content</tag>
        ↑               ↑      ↑     ↑
        ts              cs     ce    te

    item[ts:cs] -- tag
    item[cs:ce] -- content, innerHTML
    item[ce:te] -- closgin tag
    item[ts:te] -- whole tag, outerHTML
    """
    # Recover tag name (important for "*")
    r = re.match(pats.getTag, match, re.DOTALL)
    tag = r.group(1) if r else name or '[\w-]+'
    # <tag/> has no content
    if match.endswith('/>'):
        return tag, ms, me, me, me
    # find closing tag
    ce = ee = me
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
                ce, ee = r.start(), r.end()
                break;
    return tag, ms, me, ce, ee


class Node(object):
    r"""
    XML/HTML simplified node. Without structure.

    Parameters
    ----------
    tag : str
        Tag string (e.g. '<tag attr="val">'.
    item : str or None
        Part of HTML string containg this node.
    """

    __slots__ = ('ts', 'cs', 'ce', 'te',
                 'item', '__name', 'tagstr',
                 '__attrs',
                 #'__content',
                 #'__vals',
                 )

    def __init__(self, tagstr, item=None, tagindex=None):
        self.ts = self.cs = self.ce = self.te = 0
        self.tagstr = tagstr
        self.item = item or ''
        self.__name = None
        self.__attrs = None
        if tagindex is not None:
            self.ts, self.cs = tagindex

    def preparse(self, item=None, tagindex=None, tagname=None):
        r"""
        Preparsing node. Find closing tag for given `name` tag.

        item : str
            Original HTML string or HTML part string.
        ms : int
            Tag ('<') index in `item`.
        me : int
            End of tag (one characteter after '>') index in `item`.
        tagname : str or None
            Tag name (name or regex pattern, can be e.g. '.*').

        See find_node().
        """
        ms, me = (self.ts, self.cs) if tagindex is None else tagindex
        if item is None:
            item = self.item
        self.__name, self.ts, self.cs, self.ce, self.te = find_node(tagname, self.tagstr, item, ms, me)
        return self

    @property
    def attrs(self):
        r"""Returns parsed attributes."""
        if self.__attrs is None:
            self.__attrs =  dict((attr.lower(), a or b or c) \
                                 for attr, a, b, c in \
                                 re.findall(r'\s+{askAttrName}{askAttrVal}'.format(**pats),
                                            self.tagstr, re.DOTALL))
        return self.__attrs

    @property
    def content(self):
        r"""Returns tag content (innerHTML)."""
        if not self.te:
            self.preparse()
        return self.item[self.cs : self.ce]

    @property
    def text(self):
        r"""Returns tag text only."""
        return remove_tags_re.sub('', self.content)

    @property
    def name(self):
        r"""Returns tag name."""
        if self.__name is None:
            r = re.match(pats.getTag, self.tagstr or '', re.DOTALL)
            if r:
                self.__name = r.group(1)
        return self.__name or ''

    def __str__(self):
        return self.content

    def __repr__(self):
        return 'Node({attrs}, {content!r})'.format(attrs=self.attrs, content=self.content)


def find_closing(name, match, item, ms, me):
    r"""
    Helper. Find closing tag for given `name` tag.

    Parameters
    ----------
    name : str
        Tag name (name or regex pattern, can be e.g. '.*').
    match : str
        Found full tag string (tag with attributes).
    item : str
        Original HTML string or HTML part string.
    ms : int
        Offset in `item` for `match`.
    me : int
        Offset in `item` for `match` end.

    Returns
    -------
    int, int
        Content begin and content end offsets in `item`.

    """
    tag, ts, cs, ce, te = find_node(name, match, item, ms, me)
    return cs, ce


def dom_search(html, name=None, attrs=None, ret=None, exclude_comments=False):
    """
    Simple parse HTML/XML to get tags.

    Function parses HTML/XML, finds tags with attribites
    and returns matching tags content or attribute or Node().

    Paramters
    ---------
    html : str or bytes or Node or DomMatch or list of str or list of bytes or list of Node
        HTML/XML source. Directly or list of HTML/XML parts.
    name : str or bytes or None
        Tag name ot None if you want to match any tag. Can be regex string (e.g. "div|p").
    attr : dict or None
        Attributes to match or None if attributes has no matter. See below.
    ret : str or list of str or Node or DomMatch or False or None
        What to return. Tag content if False or None, Node or DomMatch nodes or attributes.
    exclude_comments : bool, default False
        If True, remove HTML comments before search.

    Returns
    -------
    list of str
        List of matched tags content (innerHTML) or matched attribute values if ret is used.
    list of Node
        List of mached nodes (attribute and content tuples) if ret is Node or Result.Node.
    list of DomMatch
        List of DomMatch mached nodes (attribute and content tuples) if ret is DomMatch or Result.DomMatch.

    """
    # Author: Robert Kalinowski <robert.kalinowski@sharkbits.com>
    #   Copyright (C) 2018 Robert Kalinowski
    # Idea is taken form parseDOM() by Tobias Ussing and Henrik Jensen.

    #print('dom_search: name="{name}", attrs={attrs}, ret={ret}'.format(**locals()))   # XXX DEBUG
    html = _make_html_list(html)

    if exclude_comments:
        # TODO: make it good, it's to simple, should ommit quotation in attribute
        re_comments = re.compile('<!--.*?-->', re.DOTALL)

    name = _tostr(name).strip()
    if not name or name == '*':
        name = pats.anyTag   # any tag

    class BreakAtrrloop(Exception): pass

    # convert retrun item type to enum
    rtype2enum = {
        True:     Result.Node,
        False:    Result.Content,
        None:     Result.Content,
        Node:     Result.Node,
        DomMatch: Result.DomMatch,
    }
    #elif isclass(ritem) and issubclass(ritem, Node):
    #    ritem = Result.Node

    ret_lst, ret_nodes = [], []

    # Get details about expected result type
    try:
        separate = ret.separate
        skip_missing = ret.missing
        sync = ret.sync
        ret = ret.args
    except AttributeError:
        separate = sync = False
        skip_missing = MissingAttr.SkipIfDirect

    # Return list of values if ret is list  [a] -> [x]
    # otherwise return just values          a   -> x
    if isinstance(ret, (list, tuple)):
        retlstadd = ret_lst.append
        skip_missing = skip_missing == MissingAttr.SkipAll
        sync_none = [None if sync is True else sync]
    else:
        retlstadd, ret = ret_lst.extend, [ ret ]
        skip_missing = skip_missing != MissingAttr.NoSkip
        sync_none = None if sync is True else sync

    for ii, item in enumerate(html):
        if sync and item in (None, Result.RemoveItem):
            #print('search - None')
            #retlstadd([item])
            ret_lst += [item]
            continue
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
                        if sync:
                            ret_lst.append(sync_none)
                            if separate:
                                ret_nodes.append(sync_none)
                        break
        except BreakAtrrloop:
            pass
        if not lst:
            continue
        #print('LST', lst)

        for match, match_index in lst:
            #print('MATCH', match, matchIndex)
            lst2 = []
            node = Node(tagstr=match, tagindex=match_index, item=item)
            if separate:
                ret_nodes.append(node)
            for ritem in ret:
                ritem = rtype2enum.get(ritem, ritem)
                #print('  -> ritem', ritem)
                if ritem == Result.Content:
                    # Element content (innerHTML)
                    lst2.append(node.content)
                elif ritem == Result.Text:
                    # Only text (remove all tags from content)
                    lst2.append(remove_tags_re.sub('', node.content))
                elif ritem == Result.Node:
                    # Get full node (content and all attributes)
                    lst2.append(node)
                elif ritem == Result.DomMatch:
                    # Get old node (content and all attributes)
                    lst2.append(DomMatch(node.attrs, node.content))
                elif ritem == Result.NoResult:
                    # Match tag, but return nothing
                    lst2.append(NoResult())
                else:   # attribute
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



# -------  DOM Select -------

#: Find alternatives with subgroups.
#s_alt_re = re.compile(r'''\s*((?:\(.*?\)|".*?"|[^,{}]+?)+|[{}])\s*''')
s_alt_re = re.compile(r'''\s*((?:\(.*?\)|".*?"|[^,{}\s+>]+?)+|[,{}+>])\s*''')
#: Find single tag (with params).
s_tag_re = re.compile(r'''(?P<tag>\w+)(?P<optional>\?)?(?P<attr1>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)?|(?P<attr2>[^\w\s](?:"[^"]*"|'[^']*'|[^"' ])*)''')
# Find params (id, class, attr and pseudo).
s_attr_re = re.compile(r'''#(?P<id>[^[\s.#]+)|\.(?P<class>[\w-]+)|\[(?P<attr>[\w-]+)(?:(?P<aop>[~|^$*]?=)(?:"(?P<aval1>[^"]*)"|'(?P<aval2>[^']*)'|(?P<aval0>(?<!['"])[^]]+)))?\]|::(?P<pseudo>\w+)(?:\((?P<psarg1>\w+(?:,\s*\w+)*)\))?|(?:\((?P<psarg2>\w+(?:,\s*\w+)*)\))''')

#: Attribute selector operation.
s_attrSelectors = {
    None:  lambda v: True,
    '=':   lambda v: v,
    '~=':  aWord,
    '|=':  aWordStarts,
    '^=':  aStarts,
    '$=':  aEnds,
    '*=':  aContains,
}

def _split_selector(selector):
    r"""
    Helper. Split alternatives in selector with subgroups.

    Parameters
    ----------
    selector : str
        CSS selector to split. Extra grouping { } can be used.

    Returns
    -------
    list
        List of splited selectors.

    Examaples
    ---------

    CSS groups.
    >>> _split_selector("A B")
    [['A', 'B']]

    >>> _split_selector("A, B")
    [['A'], ['B']]

    Also support extra groups.
    >>> _split_selector("A {B, C D}")
    [['A', [['B'], ['C', 'D']]]]
    """
    class Work(object):
        __slots__ = ('stack', 'cur', 'out', 'comma')
        def __init__(self):
            self.stack, self.out = [], []
            self.cur, self.comma = self.out, True
        def enter(self):
            new = []
            self.append(new)
            self.stack.append(self.cur)
            self.cur = new
        def exit(self):
            self.cur = self.stack.pop()
        def append(self, s):
            if w.comma:
                w.cur.append([s])
            else:
                w.cur[-1].append(s)
            w.comma = False
    w = Work()
    #print(" --- ", s_alt_re.findall(selector))
    for s in s_alt_re.finditer(selector):
        s = s.group(1)
        if s == ',':
            w.comma = True
        elif s == '{':
            w.enter()
            w.comma = True
        elif s == '}':
            if not w.stack:
                raise ValueError("Unexpected '}}' in '{}'".format(selector))
            w.exit()
            w.comma = False
        elif s in '+>':
            raise NotImplementedError('CSS + > selector not supperted yet')
        else:
            w.append(s)
    #print(w.out)
    return w.out


def _select_desc(res, html, selectors_desc, sync=False):
    r"""
    Select descending tags "A B". Supports aternatives "{A, B}".

    Parameters
    res : list of str
        Result list, where found tags are appended.
    html : list of str
        List of input HTML parts.
    selectors_desc : list of str
        List of descending selectors. Each item can be aternativr list.
    sync : boll or Result.RemoveItem, default False
        if not False run dp,search in sync mode (returns None if not match).
    """
    part, tree, out_stack = html, None, []
    # Go through descending selector
    for single_selector in selectors_desc:
        #print('=======  SINGLE', single_selector)
        if isinstance(single_selector, list):
            # subgroup of alterative nodes: " { A, B, ...} "
            subhtml = list(part if tree is None else tree)
            subpart = [part] if tree else []
            for sel in single_selector:
                #print('SEL-Alt', sel)
                res2 = []
                _select_desc(res2, subhtml, sel, sync=True)
                #print('mix!!! sh', subhtml)
                #print('mix!!! sr', res2)
                if not res2:
                    return
                subpart.append(res2)
            #print('---')
            #print('Mix!!! P', part)
            #print('MIX!!! S', subpart)
            # append as columns as rows
            part = list(p for p in zip(*subpart) if Result.RemoveItem not in p)
            #print('MIX!!! P', part)
            continue
        # single node selector
        #print('--- SINGLE', single_selector)
        rs = s_tag_re.match(single_selector)
        if not rs:
            raise ValueError("Unknow selector {}'".format(single_selector))
        tree_last = False
        dt = AttrDict(rs.groupdict())
        tag = dt.tag or ''
        ats = dt.attr1 or dt.attr2 or ''
        if tag == '*':
            tag = ''
        # node id, class, attribute selectors or pseudoclasses (what to return)
        #print(f'tag="{tag}", attr="{ats}"')
        attrs, retat = defaultdict(lambda: []), []
        for ra in s_attr_re.finditer(ats):
            da = AttrDict(ra.groupdict())
            #print('RA', ra.groupdict())
            if da.id:          # -- ID (#id)
                attrs['id'].append(da.id)
            elif da['class']:  # -- class (.class)
                attrs['class'].append(aWord(da['class']))
            elif da.attr:      # -- attr ([attr...])
                key = da.attr
                op  = da.aop
                val = da.aval0 or da.aval1 or da.aval2 or ''
                try:
                    attrs[key].append(s_attrSelectors[op](val))
                except KeyError:
                    raise KeyError('Attribute selector "{op}" is not supported'.format(op=op))
            elif da.pseudo or da.psarg2:   # -- pseudo class (opt. shortcut for ::attr)
                pseudo = da.pseudo or 'attr'
                psarg = da.psarg1 or da.psarg2 or ''
                if pseudo == 'attr':
                    retat += list(a.strip() for a in psarg.split(','))
                elif pseudo == 'content':
                    retat.append(Result.Content)
                elif pseudo == 'node':
                    retat.append(Result.Node)
                elif pseudo == 'text':
                    retat.append(Result.Text)
                elif pseudo == 'DomMatch':
                    retat.append(Result.DomMatch)
                elif pseudo == 'none':
                    retat.append(Result.NoResult)
                else:
                    raise KeyError('Pseudo-class "{op}" is not supported'.format(op=pseudo))
                if len(retat) > 1 and Result.NoResult in retat:
                    raise ValueError('::none can NOT be combined with any another modifier')
            #print('RA', ra.groupdict(), attrs)
        #print(' -RS', attrs)
        rsync = False if not sync else True if dt.optional else Result.RemoveItem
        if retat:
            #print(f'dom_search({part if tree is None else tree!r}, tag={tag!r}, ret={dict(attrs)}, sync={rsync}, separate=True)')
            part, tree = dom_search(part if tree is None else tree, tag, attrs=dict(attrs),
                                    ret=ResultParam(retat, missing=MissingAttr.NoSkip,
                                                    separate=True, sync=rsync))
            if not tree:
                #print('PART', part, 'RETURN.')
                #print('TREE', tree, 'RETURN!')
                return []
            if part and not dt.optional:
                for i, v in enumerate(part):
                    if v == [ Result.RemoveItem ]:
                        part[i] = Result.RemoveItem
            if retat == [Result.NoResult]:
                part = None
            else:
                out_stack.append(part)
            tree_last = True
            #print('PART', list(zip(part, tree)))
            #res += list(zip(res, part))
        else:
            #print(f'dom_search({part if tree is None else tree!r}, tag={tag!r}, ret={dict(attrs)}, sync={rsync})')
            part, tree = dom_search(part if tree is None else tree, tag, attrs=dict(attrs),
                                    ret=ResultParam(Result.Node, sync=rsync)), None
            if not part:
                #print('PART', part, 'RETURN!')
                #print('TREE', tree, 'RETURN.')
                return []
        #print('PART', part)
        #print('TREE', tree)
        #print('STACK', out_stack)
    #print('SelPART', part)
    #print('SelSTACK.1', out_stack)
    if part is None or len(out_stack) > 1 or (out_stack and not tree_last):
        if tree is None and part:
            out_stack.append(part)
        #print('SelSTACK.2', out_stack)
        #print('SelSTACK.3', list(zip(*out_stack)))
        res += list(zip(*out_stack))
    else:
        res += part
    return res


def _select_alt(res, html, selectors_alt):
    # Go through alternative selector
    for sel in selectors_alt:
        #print('SEL-ALT', sel)
        _select_desc(res, html, sel)


def dom_select(html, selectors):
    r"""
    Find data in HTML by jQuery (CSS) simplified selector.
    """
    #print(' --- search for "{}"'.format(selectors))
    ret = []
    if isinstance(selectors, basestring):
        ret = None
        selectors = [ selectors ]

    html = _make_html_list(html)

    # all selector from list
    for selalt in selectors:
        selalt = _split_selector(selalt)
        # Go through alternative selector
        res = []  # All matches for single selector
        _select_alt(res, html, selalt)
        #print('RES', res)
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
    #                 ret=ResultParam(['x', 'y', 'z', Result.Text])
    #                 #ret='x'
    #                 ))

    #print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret='x'))
    #print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret=['x']))
    #print(dom_search(['<a x="1">A</a><a>B</a>', '<a x="2">A</a><a>B</a>'], 'a', {}, ret=ResultParam(['x'], separate=True)))

    #print(_split_selector('A { B, C D {E, F}}, Z'))

    if False:
        out = dom_select(
            #['<a x=11>A11<b y=12 z=13>B1</b>A12</a><a x=21>A21<b y=22 z=23>B2</b>A22</a>',
            # '<a x=31>A31<b y=32 z=33>B1</b>A32</a><a x=31>A41<c y=42 z=43>B1</c>A42</a>', ],
            #'<a x=11>A1<b y=12>B1</b><c z=13>C1</c></a><a x=21>A2<b y=22>B2</b><c z=23>C2</c></a><a x=31>A3<b y=32>B3</b></a>',
            '<a x=11>A1<b y=12>B1</b><c z=13>C1</c></a><a x=31>A3<b y=32>B3</b></a>',

            'a::attr(x)::text() { b::attr(y), c::attr(z) }'  # [x, T [[y] [z]]]
            #'a::attr(x)::text() b::attr(y)'
            #'a b::attr(y)'
            #'a b'
            #'a::attr(x) b'
            #'a::attr(x)::text() b::none'
            #'b::none::none'
        )
        print(out)
        #for b, in out:
        #    print(b)

    'ul.dropdown-menu { a::attr(href), img::attr(src:"/(?P<name>.*?)\.[^.]*$") }'
    'ul.dropdown-menu { a::attr(href), img::attr(src) }'

    def printres(*args):
        print('\033[33;1m>\033[0m', *args, sep=' \033[33m|\033[0m ', end=' \033[33m|\033[0m\n')
    H = '<a x=11>A1<b y=12>B1</b><c z=13>C1</c></a><a x=31>A3<b y=32>B3</b></a>'
    if False:
        for (x, t), (y,), (z,) in dom_select(H, 'a::attr(x)::text() { b::attr(y), c::attr(z) }'):
            printres(t, x, y, z)
        for y, z in dom_select(H, 'b::attr(y,z)'):
            printres(y, z)
        for (x, t), (y,) in dom_select(H, 'a::attr(x)::text() b::attr(y)'):
            printres(t, x, y)
        #for row in dom_select(H, 'a::attr(x)::text() b::attr(y), a c::attr(z)'):
        for row in dom_select(H, 'a::attr(x) b, a c'):
            printres(row)
        for row in dom_select(H, '{a(x) b, a c}'):
            printres(row)
        print('..................')
        for row in dom_select(H, '{a c}'):
            printres(row)
        print('..................')
        for row in dom_select(H, 'a {b(y), c?(z)}'):
            printres(row)
        #for row in dom_select(H, 'a {b(y), c(z)} dI'):
        #for row in dom_select(H, 'a {b(y), c(z)}'):
        for row in dom_select(H, 'a { b, c?(z)}'):
            printres(row)
    H = '<a><b>B1></b><c>C1<d>D1></d><e>E1</e></c></a>' \
        '<a><b>B1></b><z>C1<d>D1></d><e>E1</e></z></a>' \
        '<a><b>B1></b><c>C1<d>D1></d><f>F1</f></c></a>'
    for row in dom_select(H, 'a { b, c? {d, e?}}'):
        printres(row)


