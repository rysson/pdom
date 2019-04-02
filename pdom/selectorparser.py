# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

from collections import defaultdict, namedtuple
from functools import reduce
from operator import xor
import re

from .base import aEqual, aWord, aWordStarts, aStarts, aEnds, aContains
from .base import s_attrSelectors, s_resSelectors, pats, regex
from .base import Node, DomMatch, Result, TagPosition, ItemSource, ResultParam
from .msearch import dom_search


#from arpeggio import Optional, ZeroOrMore, OneOrMore, EOF
#from arpeggio import RegExMatch as R
#from arpeggio import NonTerminal, Terminal
#from arpeggio import ParserPython, PTNodeVisitor, visit_parse_tree

from arpeggio.peg import ParserPEG
from arpeggio import visit_parse_tree, PTNodeVisitor
from arpeggio import NonTerminal, Terminal


DEBUG = False

def set_debug(debug):
    DEBUG = debug


#re_rm_comments = re.compile(r'(?:^|\n)\s*#.*$', re.MULTILINE)
re_rm_comments = re.compile(r'/\*.*?\*/', re.DOTALL)

Attr = namedtuple('Attr', 'attr value')
AttrOp = namedtuple('AttrOp', 'attr value op')
class AttrAppend(AttrOp):
    def __new__(cls, attr, value):
        return super().__new__(cls, attr, value, list.append)
class AttrExtend(AttrOp):
    def __new__(cls, attr, value):
        return super().__new__(cls, attr, value, list.extend)

NodeAttr = namedtuple('NodeAttr', 'attr value')

def filter_by_type(seq, types):
    return (item for item in seq if isinstance(item, types))

## --- DOM Selector Grammar ---
#def space():       return R(r'\s+')   # must be a space
#def sp():          return R(r'\s*')   # can be a space
#SP = Optional(sp)
#def ident():       return R(r'[\w-]+')
#def val():         return [ ("'", R(r"[^']*"), "'"), ('"', R(r'[^"]*'), '"'), R(r'''[\w-]+''') ]
#ZeroOrMoreValBr    = [("(", SP, val, ZeroOrMore(SP, ",", SP, val), SP, ")"), ("(", SP, ")")]
#def tag():         return [ ident, "*" ]
#def opt_tag():     return '?'
#def id_sel():      return '#', ident
#def class_sel():   return '.', ident
#def attr_op():     return R('[$^~|*]?=|~')
#def attr_sel():    return '[', ident, Optional(attr_op, val), ']'
#def pseudo_sel():  return ':', ident, Optional(ZeroOrMoreValBr)
#def pseudo_not():  return ':not', '(', simple_sel, ')'
#def param_sel():   return [ id_sel, class_sel, attr_sel, pseudo_not, pseudo_sel ]
#def res_attr():    return "(", SP, val, ZeroOrMore(SP, ",", SP, val), SP, ")"
#def res_param():   return "::", ident, Optional(ZeroOrMoreValBr)
#def simple_sel():  return [ (tag, Optional(opt_tag), ZeroOrMore(param_sel)), OneOrMore(param_sel) ]
#def one_sel():     return simple_sel, Optional(res_attr), ZeroOrMore(res_param)
#def oset_sel():    return "{", SP, sel_path, ZeroOrMore(SP, ",", SP, sel_path), SP, "}"
#def set_sel():     return "{{", SP, sel_path, ZeroOrMore(SP, ",", SP, sel_path), SP, "}}"
#def single_sel():  return [ one_sel, set_sel, oset_sel ]
#def path_type():   return R('\s*[>+]\s*|\s+')
#def sel_path():    return single_sel, ZeroOrMore(path_type, single_sel)
#def selector():    return sel_path, ZeroOrMore(SP, ",", SP, sel_path), EOF
#
#
##: DOM selector parser.
#parser = ParserPython(selector, skipws=False, debug=False)


def dump(tree, lvl=0, path=None):
    r"""Dump Arpeggio tree."""
    #print(type(tree))
    #path = (path or []) + [tree.rule_name or '']
    print('{:{}} {}.\033[33m{}\033[0m '.format('', lvl+1, '.'.join(path or ()), tree.rule_name), end='')
    path = (path or []) + [tree.rule_name or '']
    if isinstance(tree, NonTerminal):
        print(':')
        for it in tree:
            dump(it, lvl + 1, path)
    else:
        print(' = >>>\033[1;44m{}\033[0m<<<'.format(tree.value))


#
# TODO:  Remove __hash__ functions.
#        Add custom names for part-hash (hash only for search, not whole object).
#

class Selector(object):
    r"""Single selector (tag, attributes, psudo-elements etc.)."""
    def __init__(self, tag=None, attrs=None, param=None, result=None, nth=None,
                 path_type=None, optional=False):
        self.tag = tag or ''
        self.optional = optional
        self.attrs = defaultdict(list, attrs or [])
        self.result, self.nodefilterlist = [], []
        self.param = [] if param is None else list(param)
        self._hash = None
        self.nth = nth
        self.path_type = path_type
    def __repr__(self):
        return ('Selector(tag={tag!r}, attrs={attrs}, param={param}, result={result}, '
                'elem_pos={elem_pos}, item_source={item_source}, optional={optional}, '
                'nodefilter_len={nf_len})').format(nf_len=len(self.nodefilterlist), **vars(self))
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.tag) ^ hash(self.optional) ^ \
                    hash(str(sorted(self.attrs.items()))) ^ \
                    hash(str(self.result)) ^ hash(str(self.nodefilterlist)) ^ \
                    hash(self.elem_pos) ^ hash(self.item_source)
        return self._hash
    @property
    def path_type(self):
        return {TagPosition.RootLevel: '>',
                TagPosition.FirstOnly: '+',
                TagPosition.Any:       ' ',
                }.get(self.elem_pos, '')
    @path_type.setter
    def path_type(self, path_type):
        path_type = (path_type or '').strip()
        self.elem_pos = {'>': TagPosition.RootLevel,
                         '+': TagPosition.FirstOnly, }.get(path_type, TagPosition.Any)
        self.item_source = {'+': ItemSource.After, }.get(path_type, ItemSource.Content)

class GroupSelector(list):
    r"""Main group selector (A, B)."""
    def __hash__(self):
        return reduce(xor, map(hash, self))

class SelectorPath(list):
    r"""Selector path (A B, A > B)."""
    def __hash__(self):
        return reduce(xor, map(hash, self))

class SetSelector(list):
    r"""Set selector ( {A, B} )."""
    def __hash__(self):
        return reduce(xor, map(hash, self))

class OrderedSetSelector(SetSelector):
    r"""Ordered set selector ( {(A, B)} )."""


def nodefilterFalse(n):
    r"""Force node to does NOT match."""
    return False



class RulesVisitor(PTNodeVisitor):
    r"""
    Build selector structure for dom_select().
    """

    def visit_space(self, node, children):
        return

    def visit_tag(self, node, children):
        return Attr('tag', children[0])

    def visit_val(self, node, children):
        # children: V (len 1) or ' V ' (len 3) or " V " (len 3)
        assert len(children) in (1, 3)
        return children[1 if len(children) > 1 else 0]

    def visit_val_list_in_brackets(self, node, children):
        return children
    visit_zero_on_more_val_in_brackets = visit_val_list_in_brackets
    visit_one_on_more_val_in_brackets = visit_val_list_in_brackets

    def visit_opt_tag(self, node, children):
        return Attr('optional', True)

    def visit_id_sel(self, node, children):
        return NodeAttr('id', aEqual(children[0]))

    def visit_class_sel(self, node, children):
        return NodeAttr('class', aWord(children[0]))

    def visit_attr_sel(self, node, children):
        # children: A (len 1) or A OP V (len 3)
        assert len(children) in (1, 3)
        attr, op, val = (*children, None, True)[:3]
        return NodeAttr(attr, s_attrSelectors[op](val))

    def visit_pseudo_not(self, node, children):
        print(f'PSEUDO_NOT: node={node!r}, children={children}')
        sel = children[0]
        if any(getattr(f, 'pseudo_class', None) == ':not' for f in sel.nodefilterlist):
            raise ValueError(':not can not be nested')
        nf = self._pseudo_not(children[0])
        print(f'  -       : sel={sel}')
        print(f'PSEUDO_NOT: nf={nf!r}, {sel.nodefilterlist}')
        setattr(nf, 'pseudo_class', ':not')
        return AttrAppend('nodefilterlist', nf)

    def visit_pseudo_sel_args(self, node, children):
        return children[0], children[1:]

    visit_pseudo_sel_noarg = visit_pseudo_sel_args
    visit_pseudo_sel_1arg = visit_pseudo_sel_args

    def visit_pseudo_sel(self, node, children):
        print(f'PSEUDO_SEL: node={node!r}, children={children}')
        cmd, args = children[0]
        try:
            fun = getattr(self, '_pseudo_' + cmd.replace('-', '_'))
        except AttributeError:
            raise KeyError('Pseudo-class "{op}" is not supported'.format(op=cmd))
        nf = fun(*args)
        return AttrAppend('nodefilterlist', nf)

    #def visit_param_sel(self, node, children):
    #    print(f'PARAM_SEL: node={node!r}, children={children}')
    #    return children[0]

    def visit_simple_sel(self, node, children):
        print(f'SIMPLE_SEL: node={node!r}, children={children}')
        attrs = {}
        for k, v in (c for c in children if isinstance(c, NodeAttr)):
            attrs.setdefault(k, []).append(v)
        kwargs = {a.attr: a.value for a in children if isinstance(a, Attr)}
        sel = Selector(attrs=attrs, **kwargs)
        for item in children:
            if isinstance(item, AttrOp):
                item.op(getattr(sel, item.attr), item.value)
        return sel

    def visit_res_param_result(self, node, children):
        print(f'RES_PARAM_RESULT: node={node!r}, children={children}')
        return AttrAppend('result', s_resSelectors[children[0]])

    def visit_res_param_attrs(self, node, children):
        return AttrExtend('result', children[0])

    visit_res_attr = visit_res_param_attrs

    def visit_one_sel(self, node, children):
        print(f'ONE_SEL: node={node!r}, children={children}')
        sel = children[0]
        for item in filter_by_type(children, Attr):
            setattr(sel, item.attr, item.value)
        for item in filter_by_type(children, AttrOp):
            item.op(getattr(sel, item.attr), item.value)
        return sel

    def visit_single_sel(self, node, children):
        print(f'SINGLE_SEL: node={node!r}, children={children}')
        sel = children[0]
        return sel

    def visit_sel_path_item(self, node, children):
        print(f'SEL_PATH_ITEM: node={node!r}, children={children}')
        assert len(children) == 2
        op, sel = children
        sel.path_type = op
        return sel

    def visit_sel_path(self, node, children):
        print(f'SEL_PATH: node={node!r}, children={children}')
        return SelectorPath(children)

    def visit_selector(self, node, children):
        print(f'SELECTOR: node={node!r}, children={children}')
        return GroupSelector(children)

    def _pseudo_contains(self, value):
        def nodefilter(n, arg=value):
            return arg in n.text
        return nodefilter

    def _pseudo_content_contains(self, value):
        def nodefilter(n, arg=value):
            return arg in n.content
        return nodefilter

    def _pseudo_regex(self, value):
        rx = regex(value)
        def nodefilter(n, rx=rx):
            return rx.search(n.outerHTML)
        return nodefilter

    def _pseudo_has(self, value):
        # TODO:  Fix: :has(c) in "<b z="<c>">"
        rx = regex(pats.melem(value, None, None))
        def nodefilter(n, rx=rx):
            return rx.search(n.content)
        return nodefilter

    def _pseudo_empty(self):
        return lambda n: not n.content.strip()

    def _pseudo_first_child(self):
        if self.sel.item_source != ItemSource.Content:
            return nodefilterFalse
        if self.inside_pseudo_not:
            # Can't use shortcut in :not()
            rx = regex(pats.anyElem)
            def nodefilter(n):
                return not rx.search(n.item[:n.tag_start])
            return nodefilter
        self.sel.elem_pos = TagPosition.FirstOnly

    def _pseudo_last_child(self):
        rx = regex(pats.anyElem)
        def nodefilter(n):
            return not rx.search(n.item[n.tag_end:])
        return nodefilter

    def _pseudo_only_child(self):
        nodefilter = self._pseudo_first_child()
        return nodefilter or self._pseudo_last_child()

    def _pseudo_first_of_type(self):
        if self.sel.item_source != ItemSource.Content:
            return nodefilterFalse
        def nodefilter(n):
            rx = regex(pats.melem(n.name, None, None))
            return not rx.search(n.item[:n.tag_start])
        return nodefilter

    def _pseudo_last_of_type(self):
        def nodefilter(n):
            rx = regex(pats.melem(n.name, None, None))
            return not rx.search(n.item[n.tag_end:])
        return nodefilter

    def _pseudo_only_of_type(self):
        if self.sel.item_source != ItemSource.Content:
            return nodefilterFalse
        def nodefilter(n):
            rx = regex(pats.melem(n.name, None, None))
            return not rx.search(n.item[:n.tag_start]) and not rx.search(n.item[n.tag_end:])
        return nodefilter

    def _pseudo_enabled(self):
        self.sel.attrs['disabled'].append(False)

    def _pseudo_disabled(self):
        self.sel.attrs['disabled'].append(True)

    def _pseudo_not(self, sel):
        def nodefilter(node):
            # compare found node `node' with selector from :not()
            hit = dom_search(node.item[node.tag_start:node.tag_end], sel.tag, attrs=dict(sel.attrs),
                             ret=ResultParam(Result.Node, position=TagPosition.FirstOnly))
            for n in hit:
                n.move_to_item(item=node.item, off=node.tag_start)
                if all(f(n) for f in sel.nodefilterlist):
                    return False   # hit, :not() is false
            return True
        return nodefilter



def parse(rules):
    r"""
    Parse rules.

    Parameters
    ----------
    rules : str
        Rule file content.

    Ruturns
    -------
    Rules
        Parsed named tuple rules (way and events).
    """
    with open(os.path.join(os.path.dirname(__file__), 'selectorrules.peg')) as f:
        grammar = f.read()
    parser = ParserPEG(grammar, "selector", skipws=False, debug=DEBUG)
    rules = re_rm_comments.sub('',  rules)
    tree = parser.parse(rules)
    return visit_parse_tree(tree, RulesVisitor())


#class SelectorBuilderData(object):
#    r"""
#    Helper. Data for selector builder.
#    """
#
#    def __init__(self):
#        self.stack, self.out = [], GroupSelector()
#        self.cur = self.out
#        self.cur_ident = self.cur_attr_op = self.cur_val = None
#        self.cur_vals = []
#        self.path_type = self.ss_path_type = None
#
#    @property
#    def sel(self):
#        return self.cur[-1]
#
#
#class SelectorBuilder(object):
#    r"""
#    Build selector structure for dom_select().
#
#    Parameters
#    ----------
#    tree
#        Arpeggio parsed tree.
#    """
#
#    # TODO:  Exception from one base
#
#    def __init__(self, tree):
#        self.tree = tree
#        self.skip = {'sp'}
#        self._main_data = SelectorBuilderData()
#        self._not_data = None
#        self.d = self._main_data
#
#    @property
#    def sel(self):
#        return self.d.sel
#
#    @property
#    def out(self):
#        return self.d.out
#
#    @property
#    def inside_pseudo_not(self):
#        return bool(self._not_data)
#
#    def _build(self, item, lvl=0, path=None, parent=None):
#        name = item.rule_name or ''
#        cname = '.'.join((parent or '', name))
#        path = (path or []) + [item.rule_name or '']
#        if isinstance(item, NonTerminal):
#            if not name in self.skip:
#                self.enter(name, parent, item)
#            for it in item:
#                self._build(it, lvl + 1, path, name)
#            if not name in self.skip:
#                self.exit(name, parent, item)
#        else:
#            if not name in self.skip:
#                self.terminal(name, parent, item.value)
#
#    def build(self):
#        self._build(self.tree)
#
#    def _list_enter(self, lst=None):
#        new = [] if lst is None else lst
#        self._list_append(new)
#        self.d.stack.append(self.d.cur)
#        self.d.cur = new
#
#    def _list_exit(self):
#        self.d.cur = self.d.stack.pop()
#
#    def _list_append(self, s):
#        self.d.cur.append(s)
#
#    def enter(self, name, parent, children):
#        if DEBUG and __name__ == '__main__':
#            print('Entering Token', repr(name))
#        if name == 'sel_path':
#            self._list_enter(SelectorPath())
#        elif name == 'set_sel':
#            self._list_enter(SetSelector())
#            self.d.ss_path_type = self.d.path_type
#        elif name == 'oset_sel':
#            self._list_enter(OrderedSetSelector())
#            self.d.ss_path_type = self.d.path_type
#        elif name == 'one_sel':
#            self._list_append(Selector(path_type=self.d.path_type))
#        elif name == 'val':
#            val = children[:2][-1].value
#            if not self.d.cur_vals:
#                self.d.cur_val = val
#            self.d.cur_vals.append(val)
#        elif name == 'pseudo_not':
#            self.d = self._not_data = SelectorBuilderData()
#            self._list_append(Selector())
#
#    def exit(self, name, parent, children):
#        if DEBUG and __name__ == '__main__':
#            print('Exiting Token', repr(name))
#        if name == 'sel_path':
#            self.d.path_type = None
#            self._list_exit()
#        elif name in ('set_sel', 'oset_sel'):
#            self.d.ss_path_type = None
#            self._list_exit()
#        elif name == 'attr_sel':
#            assert self.d.cur_ident is not None
#            try:
#                self.sel.attrs[self.d.cur_ident].append(s_attrSelectors[self.d.cur_attr_op](self.d.cur_val))
#            except KeyError:
#                raise KeyError('Attribute selector "{op}" is not supported'.format(op=self.d.cur_val))
#        elif name == 'pseudo_sel':
#            assert self.d.cur_ident is not None
#            if self.d.cur_ident.isdigit():
#                self.sel.nth = int(self.d.cur_ident)
#            else:
#                # all other pseudo use filter function (or not, see code of _pseudo_* methods)
#                try:
#                    fun = getattr(self, '_pseudo_' + self.d.cur_ident.replace('-', '_'))
#                except AttributeError:
#                    raise KeyError('Pseudo-class "{op}" is not supported'.format(op=self.d.cur_ident))
#                nodefilter = fun(self.d.cur_val)
#                if nodefilter:
#                    self.sel.nodefilterlist.append(nodefilter)
#        elif name == 'pseudo_not':
#            if not self.inside_pseudo_not:
#                raise ValueError(':not() can NOT be empty')
#            if self.d == self._main_data:
#                raise ValueError(':not() can NOT be inside :not()')
#            self.d = self._main_data
#            try:
#                fun = self._pseudo_not
#            except AttributeError:
#                raise KeyError('Pseudo-class "{op}" is not supported'.format(op='not'))
#            nodefilter = fun(self.d.cur_val)
#            if nodefilter:
#                self.sel.nodefilterlist.append(nodefilter)
#            self._not_data = None
#        elif (name == 'res_param' and self.d.cur_ident == 'attr') or name == 'res_attr':
#            if not self.d.cur_vals:
#                raise IndexError('::attr() needs at least one attribute name')
#            self.sel.result += self.d.cur_vals
#        elif name == 'res_param':
#            assert self.d.cur_ident is not None
#            try:
#                self.sel.result.append(s_resSelectors[self.d.cur_ident])
#            except:
#                raise KeyError('Pseudo-elem (result param) "{}" is not supported'.format(self.d.cur_ident))
#
#    def terminal(self, name, parent, value):
#        cname = '.'.join((parent or '', name))
#        if DEBUG and __name__ == '__main__':
#            print('Token Value {!r} = {!r}  ({})'.format(name, value, cname))
#        if not name and value == '(':
#            self.d.cur_val, self.d.cur_vals = None, []
#        elif name == 'tag' or cname in ('tag.ident', 'tag.'):
#            self.sel.tag = value
#        elif name == 'opt_tag':
#            self.sel.optional = bool(value)
#        elif cname == 'id_sel.ident':
#            self.sel.attrs['id'].append(value)
#        elif cname == 'class_sel.ident':
#            self.sel.attrs['class'].append(aWord(value))
#        elif name == 'ident':
#            self.d.cur_ident, self.d.cur_attr_op = value.lower(), None
#            self.d.cur_val, self.d.cur_vals = None, []
#        elif cname == 'attr_sel.attr_op':
#            self.d.cur_attr_op = value
#        elif name == 'path_type':
#            self.d.path_type = value.strip()
#        elif cname == 'selector.' and value == ',':  # group selector separator
#            self.d.path_type = None
#        elif cname in ('oset_sel.', 'set_sel.') and value == ',':  # set selector separator
#            self.d.path_type = self.d.ss_path_type
#
#    def _pseudo_contains(self, value):
#        def nodefilter(n, arg=value):
#            return arg in n.text
#        return nodefilter
#
#    def _pseudo_content_contains(self, value):
#        def nodefilter(n, arg=value):
#            return arg in n.content
#        return nodefilter
#
#    def _pseudo_regex(self, value):
#        rx = regex(value)
#        def nodefilter(n, rx=rx):
#            return rx.search(n.outerHTML)
#        return nodefilter
#
#    def _pseudo_has(self, value):
#        # TODO:  Fix: :has(c) in "<b z="<c>">"
#        rx = regex(pats.melem(value, None, None))
#        def nodefilter(n, rx=rx):
#            return rx.search(n.content)
#        return nodefilter
#
#    def _pseudo_empty(self, value):
#        return lambda n: not n.content.strip()
#
#    def _pseudo_first_child(self, value):
#        if self.sel.item_source != ItemSource.Content:
#            return nodefilterFalse
#        if self.inside_pseudo_not:
#            # Can't use shortcut in :not()
#            rx = regex(pats.anyElem)
#            def nodefilter(n):
#                return not rx.search(n.item[:n.tag_start])
#            return nodefilter
#        self.sel.elem_pos = TagPosition.FirstOnly
#
#    def _pseudo_last_child(self, value):
#        rx = regex(pats.anyElem)
#        def nodefilter(n):
#            return not rx.search(n.item[n.tag_end:])
#        return nodefilter
#
#    def _pseudo_only_child(self, value):
#        nodefilter = self._pseudo_first_child(value)
#        return nodefilter or self._pseudo_last_child(value)
#
#    def _pseudo_first_of_type(self, value):
#        if self.sel.item_source != ItemSource.Content:
#            return nodefilterFalse
#        def nodefilter(n):
#            rx = regex(pats.melem(n.name, None, None))
#            return not rx.search(n.item[:n.tag_start])
#        return nodefilter
#
#    def _pseudo_last_of_type(self, value):
#        def nodefilter(n):
#            rx = regex(pats.melem(n.name, None, None))
#            return not rx.search(n.item[n.tag_end:])
#        return nodefilter
#
#    def _pseudo_only_of_type(self, value):
#        if self.sel.item_source != ItemSource.Content:
#            return nodefilterFalse
#        def nodefilter(n):
#            rx = regex(pats.melem(n.name, None, None))
#            return not rx.search(n.item[:n.tag_start]) and not rx.search(n.item[n.tag_end:])
#        return nodefilter
#
#    def _pseudo_enabled(self, value):
#        self.sel.attrs['disabled'].append(False)
#
#    def _pseudo_disabled(self, value):
#        self.sel.attrs['disabled'].append(True)
#
#    def _pseudo_not(self, value):
#        if not self.inside_pseudo_not:
#            raise ValueError(':not() can NOT be empty')
#        sel = self._not_data.sel
#        def nodefilter(node):
#            # compare found node `node' with selector from :not()
#            hit = dom_search(node.item[node.tag_start:node.tag_end], sel.tag, attrs=dict(sel.attrs),
#                             ret=ResultParam(Result.Node, position=TagPosition.FirstOnly))
#            for n in hit:
#                n.move_to_item(item=node.item, off=node.tag_start)
#                if all(f(n) for f in sel.nodefilterlist):
#                    return False   # hit, :not() is false
#            return True
#        return nodefilter
#
#
#
#def parse(sel):
#    r"""Parse selector `sel` and return structure for dom_select()."""
#    tree = parser.parse(sel)
#    #dump(tree)
#    #pprint(build(tree))
#    builder = SelectorBuilder(tree)
#    builder.build()
#    return builder.out


def set_debug_repr():
    tag_pos = {TagPosition.Any: '', TagPosition.RootLevel: '>', TagPosition.FirstOnly: '(^)'}
    tag_src = {ItemSource.Content: '', ItemSource.After: '+'}
    GroupSelector.__repr__ = lambda self: '\033[36mG\033[0m' + list.__repr__(self)
    SelectorPath.__repr__ = lambda self: '\033[36mP\033[0m' + list.__repr__(self)
    SetSelector.__repr__ = lambda self: '\033[36mA\033[0m' + list.__repr__(self)
    #Selector.__repr__ = lambda self: '\033[36mS\033[0;2m(\033[0;4m{}{},{},F#{},{}\033[0;2m)\033[0m'.format(
    Selector.__repr__ = lambda self: '\033[36ms\033[0m(\033[0;2m{ep}{es}{t}{o},{a},F#{nl},{r}\033[0m)\033[0m'.format(
        t=self.tag, o=self.optional and '?' or '', a=dict(self.attrs),
        nl=len(self.nodefilterlist), r=self.result,
        ep=tag_pos.get(self.elem_pos, '?'), es=tag_src.get(self.item_source, '?')
    )


if __name__ == '__main__':
    import os.path
    import sys
    import argparse
    import pprint
    pprint = pprint.PrettyPrinter(indent=2).pprint

    aparser = argparse.ArgumentParser()
    aparser.add_argument('selectors', metavar='SEL', nargs='+', help='selector to parse')
    aparser.add_argument('--debug', action='store_true', help='debug info')
    args = aparser.parse_args()
    #print(args)


    if args.debug:
        DEBUG = True
        set_debug_repr()

    # parse("a[x~='3']:x()::attr(q)")
    for sel in args.selectors:
        print("- - - - -")
        print(parse(sel))



