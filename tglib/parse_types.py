#!/bin/python3

from logging import DEBUG, INFO
from typing import Optional, Any

LOGGER_LEVEL = INFO
#LOGGER_LEVEL = DEBUG

import sys
sys.path.append('../')

import re
import json
import tglib.types
from tglib.logger import get_logger

with open('types.py') as r:
    LINES = r.readlines()

TYPES = {}
TG_TYPES = []

LINE_N = 0

logger = get_logger('TypeChecker')
logger.setLevel(LOGGER_LEVEL)

JSON_LITERALS = {
    'True': True,
    'False': False,
    'None': None
}

def raise_err(__file_line: int, *args: Any):
    assert isinstance(__file_line, int)
    raise ValueError(f'at line {__file_line}:', *args)

def get_subclass_return(func_name: str) -> str:
    'Return hinting of the dese functions for subclasses.'
    dese_subclass = re.compile(
        r'^def\s*' + func_name + r'\s*\(.*\)\s*->\s*(.*?)\s*:',
    )
    ln = 0
    while ln != len(LINES):
        if dese_subclass.match(LINES[ln]):
            hinting = dese_subclass.match(LINES[ln]).group(1)
            is_optional = re.match(r'Optional\s*\[\s*(.*)\s*\]', hinting)
            if is_optional:
                hinting = is_optional.group(1)
            return hinting
        ln += 1
    else:
        raise_err(55, f'_dese func {func_name}() not found.')


def get_multiline_hinting(__type: str, __arg: str, __start_hinting: str, ) -> dict[str, Any]:
    global LINE_N
    open_brackets = LINES[LINE_N].count('[')
    closed_brackets = LINES[LINE_N].count(']')
    brackets = '{0,%s}' % (open_brackets - closed_brackets)
    LINE_N += 1
    logger.debug(f'Diff of brackets at first line is {brackets}')
    result = __start_hinting
    while LINE_N != len(LINES):
        end_of_hinting =         re.match(r'\s*(\]\s*)' + brackets + r'\s*,*\s*\n', LINES[LINE_N])
        end_of_hinting_default = re.match(r'\s*(\]\s*)' + brackets + r'\s*=\s*(.*?),*\s*\n', LINES[LINE_N])
    
        if end_of_hinting_default:
            group = end_of_hinting_default.group(1, 2)
            result += group[0]
            return {'hinting': result, 'default': group[1]}

        elif end_of_hinting:
            result += end_of_hinting.group(1)
            return {'hinting': result}
        else:
            match_line = re.match(r'\s*(.*?\s*,*\s*)\n', LINES[LINE_N]).group(1)
            match_line = re.sub(r'(.*?),\s*', r'\1, ', match_line)
            result += match_line

        LINE_N += 1
    else:
        raise_err(85, f'no multiline hinting found for {__arg}')


def get_dese_kwargs(__type: str) -> dict[str, Any]:
    global LINE_N
    dese_kwargs = {}
    while True:

        if re.match(r'\s*return\s*cls\s*\(\s*\*\*obj\s*\)\s*\n', LINES[LINE_N]):
            return dese_kwargs
 
        elif re.match(r'\s*obj\s*=\s*\{\s*\}\n', LINES[LINE_N]):
            LINE_N += 1
            continue

        dese_default_if = re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=.*res\s*\.get\s*\(\s*'(.*?)'\s*\).*if\s*'(.*?)'\s*in\s*res\s*else\s*None\s*\n", LINES[LINE_N])
        dese_default =    re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=.*res\s*\.get\s*\(\s*'(.*?)'\s*\)", LINES[LINE_N])

        if dese_default_if:
            group = dese_default_if.group(1, 2, 3)

            if (group[0] == group[1] == group[2]):
                dese_kwargs.update({group[0]: {'tg_type': None, 'optional': True}})
            else:
                raise_err(109, LINE_N, LINES[LINE_N])

        elif dese_default:
            group = dese_default.group(1, 2)

            if (group[0] == group[1]):
                dese_kwargs.update({group[0]: {'tg_type': None, 'optional': False}})
            else:
                raise_err(117, LINE_N, LINES[LINE_N])

        else:
            raise_err(120, LINE_N, LINES[LINE_N])

        dese_nested_subclass = re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*\[\s*\[\s*(_dese_.*?)\s*\(", LINES[LINE_N])
        dese_list_subclass =   re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*\[\s*(_dese_.*?)\s*\(", LINES[LINE_N])
        dese_subclass =        re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*(_dese_.*?)\s*\(", LINES[LINE_N])
        dese_nested_tg_type =  re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*\[\s*\[\s*(.*?)\s*\._dese", LINES[LINE_N])
        dese_list_tg_type =    re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*\[\s*(.*?)\s*\._dese", LINES[LINE_N])
        dese_tg_type =         re.match(r"\s*obj\s*\[\s*'(.*?)'\s*\]\s*=\s*(.*?)\s*\._dese", LINES[LINE_N])

        if dese_nested_subclass:
            group = dese_nested_subclass.group(1, 2)
            hinting = get_subclass_return(group[1])
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[list[list[{hinting}]]]'
            else:
                dese_kwargs[group[0]]['tg_type'] = f'list[list[{hinting}]]'

        elif dese_list_subclass:
            group = dese_list_subclass.group(1, 2)
            hinting = get_subclass_return(group[1])
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[list[{hinting}]]'
            else:
                dese_kwargs[group[0]]['tg_type'] = f'list[{hinting}]'

        elif dese_subclass:
            group = dese_subclass.group(1, 2)
            hinting = get_subclass_return(group[1])
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[{hinting}]'
            else:
                dese_kwargs[group[0]]['tg_type'] = hinting

        elif dese_nested_tg_type:
            group = dese_nested_tg_type.group(1, 2)
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[list[list[{group[1]}]]]'
            else:
                dese_kwargs[group[0]]['tg_type'] = f'list[list[{group[1]}]]'

        elif dese_list_tg_type:
            group = dese_list_tg_type.group(1, 2)
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[list[{group[1]}]]'
            else:
                dese_kwargs[group[0]]['tg_type'] = f'list[{group[1]}]'

        elif dese_tg_type:
            group = dese_tg_type.group(1, 2)
            if dese_kwargs[group[0]]['optional']:
                dese_kwargs[group[0]]['tg_type'] = f'Optional[{group[1]}]'
            else:
                dese_kwargs[group[0]]['tg_type'] = group[1]

        dese_kwargs[group[0]] = dese_kwargs[group[0]]['tg_type']

        LINE_N += 1


def get_init_kwargs(__type: str) -> dict[str, Any]:
    self_found = False
    global LINE_N
    init_kwargs = {}
    while True:

        if re.match(r'\s*def\s*__init__\s*\(\s*self\s*\)\s*:\s*\n', LINES[LINE_N]):
            return init_kwargs

        elif re.match(r'\s*def\s*__init__\s*\(\s*\n', LINES[LINE_N]):
            LINE_N += 1
            continue

        elif re.match(r'\s*self\s*,\s*\n', LINES[LINE_N]):
            self_found = True
            LINE_N += 1
            continue

        elif re.match(r'\s*\)\s*:\s*\n', LINES[LINE_N]):
            if self_found:
                return init_kwargs
            else:
                raise_err(201, f'self not found in {__type}.__init__()', LINE_N, LINES[LINE_N])

        match_multiline_hinting = re.match(r"\s*(.*?)\s*:\s*(.*?\[[^\]]*)\s*\n", LINES[LINE_N])
        match_hinting_default = re.match(r'\s*(.*?)\s*:\s*(.*?)\s*=\s*(.*?)\s*,*\s*\n', LINES[LINE_N])
        match_hinting_no_default = re.match(r"\s*(.*?)\s*:\s*(.*?)\s*,*\s*\n", LINES[LINE_N])
        match_no_hinting_default = re.match(r"\s*(.*?)\s*=\s*(.*?)\s*,*\n", LINES[LINE_N])
        match_no_hinting_no_default = re.match(r"\s*(.*?)\s*,*\s*\n", LINES[LINE_N])

        if match_multiline_hinting:
            group = match_multiline_hinting.group(1, 2)
            init_kwargs[group[0]] = get_multiline_hinting(__type, group[0], group[1])
            LINE_N += 1
            continue

        elif match_hinting_default:
            group = match_hinting_default.group(1, 2, 3)

            arg = group[0]
            hinting = group[1]
            default_value = JSON_LITERALS[group[2]] if group[2] in JSON_LITERALS else group[2]

            if 'dese_kwargs' in TYPES[__type]:
                dese_hinting: Optional[str] = TYPES[__type]['dese_kwargs'][arg]

                if dese_hinting is not None and dese_hinting.startswith('Optional'):

                    if default_value is not None:
                        raise_err(228, 'Default value should be None',  LINE_N, LINES[LINE_N])
                    else:
                        ...

                    if dese_hinting != hinting:
                        raise_err(233, f'{dese_hinting} != {hinting}', LINE_N, LINES[LINE_N])
                    else:
                        ...

            init_kwargs[arg] = {'hinting': hinting, 'default': default_value}
            LINE_N += 1
            continue

        elif match_hinting_no_default:
            group = match_hinting_no_default.group(1, 2)
            arg = group[0]
            hinting = group[1]
            init_kwargs[arg] = {'hinting': hinting}
            LINE_N += 1
            continue

        elif match_no_hinting_default:
            group = match_no_hinting_default.group(1, 2)
            arg = group[0]
            default_value = int(group[1]) if group[1].isdigit() else group[1]
            init_kwargs[arg] = {'default': default_value}
            LINE_N += 1
            continue

        elif match_no_hinting_no_default:
            arg = match_no_hinting_no_default.group(1)
            init_kwargs[arg] = None
            LINE_N += 1
            continue

        else:
            raise_err(264, LINE_N, LINES[LINE_N])


while LINE_N != len(LINES):

    class_matched = re.match(r'class\s*(.*?)\s*\(\s*(.*?)\s*\)\s*:', LINES[LINE_N])

    if class_matched:
        group = class_matched.group(1, 2)

        type = group[0]
        inheritance = group[1]

        TYPES[type] = {'has_dese': False}

        if inheritance == 'TelegramType':
            TG_TYPES.append(type)

    if re.match(r'\s*def\s*_dese\s*\(', LINES[LINE_N]):

        if not re.match(r'\s*@_parse_result\s*\n', LINES[LINE_N - 1]):
            raise_err(285, LINE_N - 1, LINES[LINE_N - 1])

        if not re.match(r'\s*@classmethod\s*\n', LINES[LINE_N - 2]):
            raise_err(288, LINE_N - 2, LINES[LINE_N - 2])

        TYPES[type]['has_dese'] = True
        LINE_N += 1
        TYPES[type]['dese_kwargs'] = get_dese_kwargs(type)

    if re.match(r'\s*def\s*__init__\s*\(', LINES[LINE_N]):
        # Not add a line to check
        # def __init__(self): ...
        TYPES[type]['init_kwargs'] = get_init_kwargs(type)

    LINE_N += 1


NOT_IN_ALL = []
NOT_IN_TYPES = []
TYPES_WITH_DESE = []
TYPES_WITHOUT_DESE = []

for type in tglib.types.__all__:
    if type not in TYPES:
        NOT_IN_TYPES.append(type)

for type in TYPES:
    if type not in tglib.types.__all__:
        NOT_IN_ALL.append(type)

    if TYPES[type]['has_dese']:
        TYPES_WITH_DESE.append(type)
    else:
        TYPES_WITHOUT_DESE.append(type)

logger.info('Length of __all__ is: %s', len(tglib.types.__all__))
logger.info('Length of types is: %s', len(TYPES))
logger.info('TelegramTypes are: %s', len(TG_TYPES))
logger.info('Missing types are: %s', len(NOT_IN_ALL) or len(NOT_IN_TYPES))
logger.info('Types with _dese(): %s', len(TYPES_WITH_DESE))
logger.info('Types without _dese(): %s', len(TYPES_WITHOUT_DESE))


with open('test_types.json', 'w') as w:
    w.write(json.dumps(TYPES, indent = 4))

with open('test_types.json', 'r') as r:
    lines = r.readlines()

f = '''\
import sys
sys.path.append('../')

from inspect import isclass
from typing import (
    Union,
    Optional,
    Literal
)
from tglib.types import *
from tglib.types import (
    TelegramType,
    ChatMember,
    MessageOrigin,
    ReactionType,
    ChatBoostSource,
    InputMessageContent,
    MaybeInaccessibleMessage
)

TYPES = '''

for line in lines:
    line = re.sub(r'(\s*)"([A-Z].*)"(\s*:\s*\{)', r'\1\2\3', line)
    line = re.sub(r'(\s*".*"\s*)(:\s*)"(.*)"', r'\1\2\3', line)
    line = re.sub(r'(\s*)null(\s*)', r'\1None\2', line)
    line = re.sub(r'(\s*)true(\s*)', r'\1True\2', line)
    line = re.sub(r'(\s*)false(\s*)', r'\1False\2', line)
    f += line

f += '''

for k in TYPES:
    if not isclass(k):
        raise TypeError(
            f'Invalid key {k!r}: expected a type, got {k.__class__.__name__}.'
        )
    if not issubclass(k, TelegramType):
        raise TypeError(
            f'{k.__name__} is not a subclass of TelegramType.'
        )
print('All the types are subclass of TelegramType.')
'''

with open('test_types.py', 'w') as w:
    w.write(f)

#"""
