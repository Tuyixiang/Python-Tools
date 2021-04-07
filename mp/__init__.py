"""带有友好接口和规整输出的多线程处理库"""

__all__ = ['map', 'reduce', 'map_reduce']

from .reduce import reduce
from .map_reduce import map_reduce
from .map import map, imap, imap_unordered, starmap