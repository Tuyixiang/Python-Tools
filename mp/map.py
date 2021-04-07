"""多线程处理，基于 multiprocess，带进度条"""

import math
import inspect
import time
from ctypes import c_int
from typing import Any, Callable, Iterable, List, Optional, Tuple, TypeVar

from multiprocess import Pool, Value, cpu_count
from pb import ProgressBar, pb

# 数据类型
DT = TypeVar('DT')
# 结果类型
RT = TypeVar('RT')


class _WrappedFunction:
    """封装后的多线程执行函数，每处理 interval 个数据则执行 callback"""

    def __init__(self, function: Callable[[DT], RT], interval: int, label: str, callback: Callable[[None], None]) -> None:
        self.function = function
        self.interval = interval
        self.label = label
        self.callback = callback
        self.counter = 0

    def __call__(self, data: DT) -> RT:
        result = self.function(data)
        self.counter += 1
        if self.counter == self.interval:
            self.callback()
            self.counter = 0
        return result


def _adapt(iterable: Iterable[DT], size: int, chunk_size: int, jobs: int) -> Tuple[Iterable[DT], int, int, int]:
    # 获取数据长度。仅当数据没有长度，且指定了 chunk_size 时忽略长度
    if not size:
        if hasattr(iterable, '__len__'):
            size = len(iterable)
        elif chunk_size is None:
            iterable = list(iterable)
            size = len(iterable)
        else:
            size = None

    if size == 0:
        return

    # 适配 chunk_size 和 jobs
    if chunk_size:
        if size:
            jobs = min(jobs, math.ceil(size / chunk_size))
    else:
        if size < jobs:
            jobs = size
            chunk_size = 1
        else:
            chunk_size = max(1, size // jobs // 4)

    return iterable, chunk_size, jobs, size


def _execute(
    method: str,
    function: Callable[[DT], RT],
    iterable: Iterable[DT],
    size: int,
    chunk_size: int,
    jobs: int,
    label: str,
    customize_callback: Callable[[int, Optional[int]], None],
) -> Iterable[RT]:
    iterable, chunk_size, jobs, size = _adapt(iterable, size, chunk_size, jobs)

    # 进度条
    progress = ProgressBar(label)
    # 已完成的数量
    completed = Value(c_int, 0)
    # 更新进度条的区间
    update_interval = max(1, chunk_size // 32)

    # 更新进度条回调
    def callback() -> None:
        # 从运行栈全局变量找到 _completed
        globals = inspect.stack()[-1].frame.f_globals
        _completed = globals['_completed']

        with _completed.get_lock():
            _completed.value += update_interval

    # 传入共享对象
    def initialize(completed: Value) -> None:
        # hack：把变量挂在进程运行栈最底层
        globals = inspect.stack()[-1].frame.f_globals
        globals['_completed'] = completed

    pool = Pool(jobs, initializer=initialize, initargs=(completed,))
    func = _WrappedFunction(function, update_interval, label, callback)
    method = getattr(pool, method + '_async')
    result = method(func, iterable)

    update = customize_callback or progress.update
    while not result.ready():
        if size:
            update(min(completed.value, size - 1), size)
        else:
            update(completed.value)

    if size:
        progress.update(size, size)

    return result.get()


def map(
    function: Callable[[DT], RT],
    iterable: Iterable[DT],
    size: int = None,
    chunk_size: int = None,
    jobs: int = cpu_count(),
    silent: bool = False,
    label: str = 'Map',
    customize_callback: Callable[[int, Optional[int]], None] = None,
) -> List[RT]:
    if silent:
        return Pool(jobs).map(function, iterable, chunk_size)
    return _execute('map', function, iterable, size, chunk_size, jobs, label, customize_callback)


def imap(
    function: Callable[[DT], RT],
    iterable: Iterable[DT],
    size: int = None,
    chunk_size: int = None,
    jobs: int = cpu_count(),
    silent: bool = False,
    label: str = 'IMap',
) -> Iterable[RT]:
    iterable, chunk_size, jobs, size = _adapt(iterable, size, chunk_size, jobs)
    result = Pool(jobs).imap(function, iterable, chunk_size)
    if silent:
        return result
    return pb(result, size=size, label=label)


def imap_unordered(
    function: Callable[[DT], RT],
    iterable: Iterable[DT],
    size: int = None,
    chunk_size: int = None,
    jobs: int = cpu_count(),
    silent: bool = False,
    label: str = 'IMap Unordered',
) -> Iterable[RT]:
    iterable, chunk_size, jobs, size = _adapt(iterable, size, chunk_size, jobs)
    result = Pool(jobs).imap_unordered(function, iterable, chunk_size)
    if silent:
        return result
    return pb(result, size=size, label=label)


def starmap(
    function: Callable[[Any], RT],
    iterable: Iterable[Iterable[Any]],
    size: int = None,
    chunk_size: int = None,
    jobs: int = cpu_count(),
    silent: bool = False,
    label: str = 'StarMap',
) -> List[RT]:
    if silent:
        return Pool(jobs).starmap(function, iterable, chunk_size)
    return _execute('starmap', function, iterable, size, chunk_size, jobs, label)
