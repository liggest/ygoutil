
def check_cached_property(obj: object, name: str, default = None):
    """ 在不触发 cached_property 的情况下检查其是否已存在 """
    return obj.__dict__.get(name, default)

def line_or_not(line: str):
    return f"{line}\n" if (line := line.rstrip()) else ""

