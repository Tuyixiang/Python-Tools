"""
随机生成密码
"""

import datetime
import os
import pickle
import random
from inspect import signature
from string import *
from typing import *

from styles import bold, green

_HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'history')


def _save(method: str, password: str):
    """
    保存一个记录，同时清除超过 7 天的记录
    """
    # 当前时间
    now = datetime.datetime.now()
    # 记录
    new = {
        'method': method,
        'password': password,
        'time': now,
    }
    # 加载已保存记录
    try:
        saved = pickle.load(open(_HISTORY_PATH, 'rb'))
    except (FileNotFoundError, pickle.UnpicklingError):
        saved = []
    # 过滤超过 7 天的记录
    saved = [
        entry for entry in saved
        if now - entry['time'] < datetime.timedelta(days=7)
    ]
    # 添加记录并保存
    pickle.dump(saved + [new], open(_HISTORY_PATH, 'wb'))


def _contain_all(password: str, charsets: Iterable[str]) -> bool:
    """
    判断密码是否包含所有字符集中的字符
    """
    return all(set(password) & set(charset) for charset in charsets)


def gen():
    """
    随机生成长度为 16，带有数字、小写、大写、符号的密码
    """
    chars = ''
    while not _contain_all(chars, [digits, ascii_lowercase, ascii_uppercase]):
        chars = ''.join(random.choices(
            digits + ascii_lowercase + ascii_uppercase,
            k=14
        ))
    password = '-'.join([chars[:5], chars[5:-5], chars[-5:]])
    print(password)
    _save('gen()', password)
    return password


def complex(length=32):
    """
    随机生成指定长度（默认为 32）的复杂密码
    """
    password = ''
    while not _contain_all(password, [digits, ascii_lowercase, ascii_uppercase, punctuation]):
        password = ''.join(random.choices(
            digits + ascii_lowercase + ascii_uppercase + punctuation,
            k=length
        ))
    print(password)
    _save('complex(%d)' % length, password)
    return password


def no_symbol(length=16):
    """
    随机生成指定长度（默认为 16），带有数字、小写、大写的密码
    """
    password = ''
    while not _contain_all(password, [digits, ascii_lowercase, ascii_uppercase]):
        password = ''.join(random.choices(
            digits + ascii_lowercase + ascii_uppercase,
            k=length
        ))
    print(password)
    _save('no_symbol(%d)' % length, password)
    return password


def show_history():
    """
    打印历史
    """
    # 加载已保存记录
    try:
        saved = pickle.load(open(_HISTORY_PATH, 'rb'))
    except (FileNotFoundError, pickle.UnpicklingError):
        saved = []
    for entry in sorted(saved, key=lambda e: e['time']):
        print(entry['time'].isoformat(), entry['method'], sep='\t')
        print(entry['password'])
        print()


def help():
    """
    打印模块说明
    """
    print((bold + green)('%s: %s' % (__loader__.name, __doc__[1:-1])))
    for func in [gen, complex, no_symbol, show_history]:
        print(bold(func.__name__ + str(signature(func))) + func.__doc__)


help()
