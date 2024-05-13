
def check_cached_property(obj: object, name: str, default = None):
    """ 在不触发 cached_property 的情况下检查其是否已存在 """
    return obj.__dict__.get(name, default)

def line_or_not(line: str):
    """ 若 line 非空，则在尾部添加换行 """
    return f"{line}\n" if (line := line.rstrip()) else ""

def join_values(*values: str, sep=" "):
    """ 用 sep 间隔符串连 values 中所有非空值 """
    return sep.join(filter(None, values))
