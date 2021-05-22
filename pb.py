"""打印进度条"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Generator, Iterable
import unicodedata
from multipledispatch import dispatch

from styles import bggreen, bgwhite, black, inverse

# 在 IPython 中使用白底黑字代替 inverse
try:
    _ = get_ipython()
    inverse = bgwhite + black
except NameError:
    pass


class _UnicodeStr(str):
    """中文字符计两倍宽度"""

    def __init__(self, string: str) -> None:
        self.char_widths = [
            2 if unicodedata.east_asian_width(c) == 'W' else 1
            for c in string
        ]
        self.len = sum(self.char_widths)

    def __len__(self) -> int:
        return self.len

    def __getitem__(self, key: slice) -> _UnicodeStr:
        result = []
        cumulate = 0
        key = slice(
            key.start or 0,
            self.len if key.stop is None else key.stop,
        )
        for i, (c, w) in enumerate(zip(self, self.char_widths)):
            if key.start <= cumulate < key.stop:
                result.append(c)
            cumulate += w
        return _UnicodeStr(''.join(result))


def bar(text: str, progress: float) -> None:
    # 打印进度条
    progress = min(1, max(0, progress))
    line = ProgressBar._pad_with_space(text)
    step = int(progress * ProgressBar._terminal_width() + .5)
    print(inverse(line[:step]) + line[step:])


def _format_int(value: int) -> str:
    """用 K,M,G 等形式呈现整数"""
    if value < 10 ** 3:
        return str(value)
    for lower, upper, symbol in [
        (10 ** 3, 10 ** 6, 'K'),
        (10 ** 6, 10 ** 9, 'M'),
        (10 ** 9, 10 ** 12, 'G'),
        (10 ** 12, 10 ** 15, 'T'),
    ]:
        if value < upper:
            return '%.2f%s' % (value / lower, symbol)


def _format_duration(time: timedelta) -> str:
    """用 s,min,h 等形式呈现时长"""
    s = time.total_seconds()
    if s < 60:
        return '%.3fs' % s
    elif s <= 3600:
        return '%dmin %ds' % (s // 60, s % 60)
    elif s <= 86400:
        return '%dh %dmin %ds' % (s // 3600, (s // 60) % 60, s % 60)
    else:
        s = time.seconds
        return '%dd %dh %dmin %ds' % (time.days, s // 3600, (s // 60) % 60, s % 60)


class ProgressBar:
    """进度条"""
    # 无法获取控制台宽度时，默认进度条长度
    DEFAULT_TERMINAL_WIDTH = 40
    # 动画间隔
    ANIMATION_INTERVAL = timedelta(seconds=0.04)
    # 动画宽度
    ANIMATION_WIDTH = 6

    def __init__(self, label):
        self.label = label
        self.reset()

    def reset(self, now: datetime = None):
        if now is None:
            now = datetime.now()
        self.last_progress = 0
        self.total = None
        self.start_time = now

    @staticmethod
    def _terminal_width() -> int:
        """获取控制台宽度"""
        try:
            return os.get_terminal_size()[0]
        except OSError:
            return ProgressBar.DEFAULT_TERMINAL_WIDTH

    @staticmethod
    def _pad_with_space(text: str, append_text: str = None) -> _UnicodeStr:
        """将字符串填充空格以达到控制台宽度"""
        text = _UnicodeStr(text)
        if append_text is not None:
            append_text = _UnicodeStr(append_text)
            return _UnicodeStr(text + ' ' * (ProgressBar._terminal_width() - len(text) - len(append_text)) + append_text)
        else:
            return _UnicodeStr(text + ' ' * (ProgressBar._terminal_width() - len(text)))

    def _print(self, progress: float, text: str) -> None:
        now = datetime.now()
        append_text = _format_duration(now - self.start_time)

        # 显示 label
        if self.label:
            text = '%s: %s' % (self.label, text)
        # 打印进度条
        if progress == 1:
            # 已经完成，打印绿色的 done
            text += ' done'
            print((bggreen + black)(ProgressBar._pad_with_space(text, append_text)))
            self.reset(now)
        else:
            # 打印进度
            line = ProgressBar._pad_with_space(text, append_text)
            progress_step = int(progress * ProgressBar._terminal_width() + .5)

            animation_step = (
                now - self.start_time - timedelta(seconds=3)
            ) // ProgressBar.ANIMATION_INTERVAL
            if animation_step > len(line) * 3 // 2:
                animation_step = animation_step % (len(line) * 3 // 2) \
                    - ProgressBar.ANIMATION_WIDTH
            anchors = [
                max(0, min(animation_step, progress_step)),
                max(0, animation_step + ProgressBar.ANIMATION_WIDTH),
                progress_step,
            ]
            if progress_step <= animation_step + ProgressBar.ANIMATION_WIDTH:
                print(
                    inverse(line[:anchors[0]]),
                    line[anchors[0]:],
                    sep='', end='\r',
                )
            else:
                print(
                    inverse(line[:anchors[0]]),
                    line[anchors[0]: anchors[1]],
                    inverse(line[anchors[1]:anchors[2]]),
                    line[anchors[2]:],
                    sep='', end='\r'
                )

    @dispatch()
    def update(self) -> None:
        """计数器自增"""
        self.last_progress += 1
        if self.total:
            self.update(self.last_progress, self.total)
        else:
            self.update(self.last_progress)

    @dispatch(float)
    def update(self, progress: float) -> None:
        """更新完成度（0 至 1）"""
        if progress == 0 or progress < self.last_progress:
            self.reset()
        self.last_progress = progress

        text = '%s%%' % (str(progress * 100)[:4])
        self._print(progress, text)

    @dispatch(int)
    def update(self, completed: int) -> None:
        """更新完成数量，总数量未知"""
        if completed == 0 or completed < self.last_progress:
            self.reset()
        self.last_progress = completed

        text = str(completed)
        self._print(1 - 1e-10, text)

    @dispatch(int, int)
    def update(self, completed: int, total: int) -> None:
        """更新完成数量，已知总数量"""
        if completed == 0 or completed < self.last_progress:
            self.reset()
        self.last_progress = completed

        text = '%s/%s' % (_format_int(completed), _format_int(total))
        progress = completed / total
        text = '%s%% (%s)' % (str(progress * 100)[:4], text)
        self._print(progress, text)

    def __enter__(self) -> ProgressBar:
        total = self.total
        self.reset()
        self.total = total
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type or exc_value or traceback:
            return
        if self.total and self.last_progress >= self.total:
            return
        self._print(1, str(self.last_progress))

    @dispatch(object)
    def __call__(
        self,
        iterable: Iterable,
        size: int = None,
        label: str = None,
        interval: int = None,
    ) -> Generator[Any, None, None]:
        """
        封装一个集合或迭代器，返回一个迭代器，在每次取出物件时更新进度条

        Arguments:
            iterable: Iterable
                要被封装的数据

            size: int = None
                如果 iterable 是迭代器，size 应为迭代器长度
                此时如果 size 为 None，则进度条无法显示完成比例
                如果 size <= 0，则自动将迭代器转为列表

            label: str = None
                进度条显示的标签

            interval: int = None
                显示更新的间隔。如果数据长度确定，则间隔不会小于数据长度的万分之一
        """
        self.reset()
        self.label = label or self.label or type(iterable).__qualname__
        interval = interval or 1

        if hasattr(iterable, '__len__'):
            size = len(iterable)
        elif size is not None and size <= 0:
            iterable = list(iterable)
            size = len(iterable)

        if size is None:
            for i, item in enumerate(iterable):
                yield item
                if i % interval == 0:
                    self.update(i, 0)
        else:
            interval = max(interval, size // 1000)
            for i, item in enumerate(iterable):
                yield item
                if i % interval == 0:
                    self.update(i, size)
            self.update(size, size)

    @dispatch(int)
    def __call__(self, total: int):
        """指定总数，用于 with 语句"""
        self.total = total
        return self


pb = ProgressBar('')
