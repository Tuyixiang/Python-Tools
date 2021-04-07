"""
日志记录
"""

import datetime
import os
import sys

from styles import *

_print = print

# 日志级别
LEVELS = [
    'DEBUG    ', # 0
    'INFO     ', # 1
    'WARNING  ', # 2
    'ERROR    ', # 3
    'CRITICAL ', # 4
]
# 对应颜色
COLORS = [dim, lambda x: x, yellow, red, bgred + white]

# 文件输出路径
CWD = os.getcwd()
# 已完成初始化
INITIALIZED = False

# 配置
CONFIG = {
    'trivial': {
        'enabled': True,
        'filename': 'debug.log',
        'level': 0,
        'colored': False,
        'file': None,
    },
    'warning': {
        'enabled': True,
        'filename': 'warning.log',
        'level': 2,
        'colored': False,
        'file': None,
    },
    'stdout': {
        'enabled': True,
        'level': 1,
        'colored': True,
        'file': sys.stdout,
    },
    'stderr': {
        'enabled': True,
        'level': 3,
        'colored': True,
        'file': sys.stderr,
    },
}


def init(path=None, **kwargs):
    """
    进行配置。调用时会在所有输出打印分割线
    """
    # 应用输出配置
    for name, value in kwargs.items():
        outfile, attribute = name.split('_')
        CONFIG[outfile][attribute] = value
    # 配置输出路径
    global CWD
    if path:
        if os.path.isabs(path):
            CWD = path
        else:
            CWD = os.path.join(CWD, path)
        if not os.path.exists(CWD):
            _print('目录"%s"不存在，是否创建？(Y/n)' % bold(CWD))
            if input() in ['', 'y', 'Y']:
                os.makedirs(CWD)
            else:
                _print('退出程序，请重设日志目录')
                sys.exit()
    # 打印分割线
    if not INITIALIZED:
        width = max(os.get_terminal_size()[0], 10)
        line = '[%s] 程序启动' % time_string()
        print('-' * width)
        print((width - len(line)) // 2 * ' ' + line)
        print('-' * width)


def stdout_only():
    """
    只使用标准输出
    """
    _maybe_initialize()
    init(trivial_enabled=False, warning_enabled=False, stderr_enabled=False, stdout_level=0)


def _maybe_initialize():
    """
    若未初始化则进行初始化
    """
    global INITIALIZED
    if not INITIALIZED:
        if CONFIG['trivial']['enabled'] and not CONFIG['trivial']['file']:
            CONFIG['trivial']['file'] = open(os.path.join(
                CWD, CONFIG['trivial']['filename']), 'a', encoding='utf-8')
        if CONFIG['warning']['enabled'] and not CONFIG['warning']['file']:
            CONFIG['warning']['file'] = open(os.path.join(
                CWD, CONFIG['warning']['filename']), 'a', encoding='utf-8')
        INITIALIZED = True


def print(*args, **kwargs):
    """
    在每个文件打印字符，接口等同于内置 print
    """
    _maybe_initialize()
    if CONFIG['trivial']['enabled']:
        _print(*args, **kwargs, file=CONFIG['trivial']['file'])
    if CONFIG['warning']['enabled']:
        _print(*args, **kwargs, file=CONFIG['warning']['file'])
    if CONFIG['stdout']['enabled']:
        _print(*args, **kwargs, file=CONFIG['stdout']['file'])
    elif CONFIG['stderr']['enabled']:
        _print(*args, **kwargs, file=CONFIG['stderr']['file'])


def _log(msg, level):
    """
    输出指定级别的日志
    """
    _maybe_initialize()
    message = '[%s] %s: %s' % (time_string(), LEVELS[level], msg)
    color = [lambda x: x, COLORS[level]]
    if CONFIG['trivial']['enabled'] and level >= CONFIG['trivial']['level']:
        _print(color[CONFIG['trivial']['colored']](
            message), file=CONFIG['trivial']['file'])
    if CONFIG['warning']['enabled'] and level >= CONFIG['warning']['level']:
        _print(color[CONFIG['warning']['colored']](
            message), file=CONFIG['warning']['file'])
    if CONFIG['stderr']['enabled'] and level >= CONFIG['stderr']['level']:
        _print(color[CONFIG['stderr']['colored']](
            message), file=CONFIG['stderr']['file'])
    elif CONFIG['stdout']['enabled'] and level >= CONFIG['stdout']['level']:
        _print(color[CONFIG['stdout']['colored']](
            message), file=CONFIG['stdout']['file'])


def time_string():
    return str(datetime.datetime.now())[:-3]


def debug(msg): return _log(msg, 0)
def info(msg): return _log(msg, 1)
def warning(msg): return _log(msg, 2)
def error(msg): return _log(msg, 3)
def critical(msg): return _log(msg, 4)
