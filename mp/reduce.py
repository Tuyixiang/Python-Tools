"""Reduce 操作"""

# TO BE UPDATED

from functools import partial
from typing import Any, Callable, Generator, Iterable, Iterator

from more_itertools import chunked, first, take
from multiprocess import Process, Queue, cpu_count
from pb import ProgressBar

from .map import map


def reduce(
    func: Callable[[Any, Any], Any],
    data: Iterable,
    size: int = -1,
    chunk_size: int = 16,
    batch_size: int = 8192,
    jobs: int = cpu_count(),
    silent: bool = False,
    label: str = 'reduce',
) -> Generator[list, None, None]:
    """并行处理一个列表或迭代器，返回乱序的 chunk 迭代器

    Arguments:
        func: Callable[[Any, Any], Any],
            Reduce 函数，第一个参数是累积结果，第二个参数是新元素

        data: Iterable
            待处理的数据

        size: int = -1
            待处理数据的长度，-1 则需要将 iterator 转换为列表并求长度
            如果禁用长度，可以使用 size=None

        chunk_size: int = 16
            每个线程单次处理的数据数量

        batch_size: int = 8192
            每次迭代之多使用的元素数量，不会小于 chunk_size * jobs

        jobs: int = cpu_count()
            开启线程数量，默认为核心数量

        silent: bool = False
            关闭进度输出

        label: str = 'reduce'
            进度条显示名称
    """
    batch_size = max(batch_size, chunk_size * jobs)
    completed = 0
    progress_bar = ProgressBar(label)
    progress_bar.reset()

    def _reduce_chunk(chunk: Iterable) -> Any:
        """将一个 chunk reduce 成单个结果"""
        chunk = iter(chunk)
        result = first(chunk)
        for item in chunk:
            result = func(result, item)
        return result

    # 可能需要计算 size
    if size is not None and size == -1:
        try:
            size = len(data)
        except TypeError:
            data = list(data)
            size = len(data)
    iterator = iter(data)

    # 分层计算，每一层达到上限后计算下一层
    output = [take(batch_size, iterator)]

    def reduce_layer(index: int):
        nonlocal completed
        if index + 1 >= len(output):
            output.append([])
        result = map(
            _reduce_chunk,
            chunked(output[index], chunk_size),
            chunk_size=1,
            jobs=jobs,
            silent=silent,
            customize_callback=lambda current, _=None: progress_bar.update(
                current * 15 + completed, size),
        )
        completed += len(output[index]) - len(result)
        output[index + 1] += result
        output[index] = []

    while output[0]:
        reduce_layer(0)
        for i in range(1, len(output)):
            if len(output[i]) >= batch_size:
                reduce_layer(i)
        output[0] = take(batch_size, iterator)

    for i in range(len(output)):
        if i + 1 >= len(output):
            chunk = output[i]
            while len(chunk) > max(chunk_size, 2 * jobs):
                new_chunk_size = min(chunk_size, len(chunk) // jobs + 1)
                new_chunk = map(
                    _reduce_chunk,
                    chunked(chunk, new_chunk_size),
                    chunk_size=1,
                    jobs=jobs,
                    silent=silent,
                    customize_callback=lambda current, _=None: progress_bar.update(
                        current * (new_chunk_size - 1) + completed, size),
                )
                completed += len(chunk) - len(new_chunk)
                chunk = new_chunk
            result = _reduce_chunk(chunk)
            completed += len(chunk)
            progress_bar.update(completed, size)
            return result
        if len(output[i]) > batch_size:
            reduce_layer(i)
        else:
            output[i + 1] += output[i]
