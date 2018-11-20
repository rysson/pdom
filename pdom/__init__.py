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


from .base import type_str, type_bytes, Enum
from .base import AttrDict, RoAttrDictView
from .base import NoResult, Result, MissingAttr, ResultParam
from .base import regex, pats, remove_tags_re
from .base import _tostr, _make_html_list, find_node
from .base import Node, DomMatch
from .base import aWord, aWordStarts, aStarts, aEnds, aContains


from .msearch import dom_search as search
from .mselect import dom_select as select
from .backward import parseDOM, parse_dom


