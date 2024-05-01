from dataclasses import dataclass

@dataclass
class IDCard:
    """ 卡片基础标识 """
    id: int | str = 0
    name: str = ""

    def __bool__(self):
        return bool(self.id or self.name)

@dataclass
class CnJpEnIDCard(IDCard):
    """ 多语言卡片基础标识 """
    jp_name: str = ""
    en_name: str = ""

    def __bool__(self):
        return super().__bool__() or bool(self.jp_name or self.en_name)
