"""检查运行环境"""

def interactive() -> bool:
    """是否运行于 Python 交互环境"""
    import __main__ as main
    return hasattr(main, '__file__')
