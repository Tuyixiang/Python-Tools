"""ANSI 字符格式"""

from __future__ import annotations
from typing import Union, Iterable


class _Style:
    def __init__(self, name: str, on: int, off: int = 0):
        self.name = name
        self.on = on
        self.off = off

    @property
    def enter(self) -> str:
        return '\x1b[%dm' % self.on
        
    @property
    def exit(self) -> str:
        return '\x1b[%dm' % self.off

    def __str__(self) -> str:
        return '%s style (%d, %d)' % (self(self.name), self.on, self.off)

    def __call__(self, string: str) -> str:
        return self.enter + string + self.exit

    def __add__(self, other: Union[_Style, _CombinedStyle]) -> _CombinedStyle:
        if isinstance(other, _Style):
            return _CombinedStyle([self, other])
        elif isinstance(other, _CombinedStyle):
            return _CombinedStyle([self] + other.styles)
        else:
            raise TypeError('Incompatible types: %s + %s', type(self).__name__, type(other).__name__)


class _CombinedStyle:
    def __init__(self, styles: Iterable[_Style]):
        self.styles = styles

    def __str__(self) -> str:
        return self(' + '.join(style.name for style in self.styles)) + ' styles'
    
    def __call__(self, string: str) -> str:
        for style in self.styles:
            string = style(string)
        return string

    def __add__(self, other: Union[_Style, _CombinedStyle]) -> _CombinedStyle:
        if isinstance(other, _Style):
            return _CombinedStyle(self.styles + [other])
        elif isinstance(other, _CombinedStyle):
            return _CombinedStyle(self.styles + other.styles)
        else:
            raise TypeError('Incompatible types: %s + %s', type(self).__name__, type(other).__name__)


bold            = _Style('bold',          1,  22)
dim             = _Style('dim',           2,  22)
italics         = _Style('italics',       3,  23)
underline       = _Style('underline',     4,  24)
inverse         = _Style('inverse',       7,  27)
strikethrough   = _Style('strikethrough', 9,  29)
black           = _Style('black',         30, 39)
red             = _Style('red',           31, 39)
green           = _Style('green',         32, 39)
yellow          = _Style('yellow',        33, 39)
blue            = _Style('blue',          34, 39)
magenta         = _Style('magenta',       35, 39)
cyan            = _Style('cyan',          36, 39)
white           = _Style('white',         37, 39)
bgblack         = _Style('bgblack',       40, 49)
bgred           = _Style('bgred',         41, 49)
bggreen         = _Style('bggreen',       42, 49)
bgyellow        = _Style('bgyellow',      43, 49)
bgblue          = _Style('bgblue',        44, 49)
bgmagenta       = _Style('bgmagenta',     45, 49)
bgcyan          = _Style('bgcyan',        46, 49)
bgwhite         = _Style('bgwhite',       47, 49)

_styles = [
    bold, dim, italics, underline, inverse, strikethrough, 
    black, red, green, yellow, blue, magenta, cyan, white, 
    bgblack, bgred, bggreen, bgyellow, bgblue, bgmagenta, bgcyan, bgwhite,
]


def help():
    print((bold + green)('%s: %s' % (__loader__.name, __doc__)))
    print(', '.join(style(style.name) for style in _styles))
    print('使用 style(string) 来格式化字符串')
