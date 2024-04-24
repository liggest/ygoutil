from enum import Enum
from typing import Iterable
from functools import partialmethod

from ygoutil.constant import CardType, CardRace, CardAttribute, LinkMark, linkMark2str, CardCategory

class Card:
    """YGO 卡片"""

    def __init__(self, types: Iterable[CardType | str] = None):
        self.id = None  # 卡号
        self.name: str = None  # 卡名（中文）
        self.jpname: str = None  # 卡名（日文）
        self.enname: str = None  # 卡名（英文）
        self.effect: str = None  # 效果文本

        self.ot: str = None  # ot状态
        self.set = set()  # 系列
        self.cardType = set()  # 卡片类型
        self.limit: str = None  # 禁限

        self.category = set()  # 效果种类

        self.alias = None  # 作为同名卡在数据库中的实际卡号

        self.isRD = False  # RD卡

        if types:
            self.fillCardType(*types)
            self.initMonster()  # 根据卡片类型初始化怪兽信息
        # 一系列链接
        self.img = None  # 卡图链接
        self.url = None  # 卡片信息来源链接
        self.database = None
        self.QA = None
        self.wiki = None
        self.yugipedia = None
        # self.ygorg=None
        self.ourocg = None
        self.script = None  # 脚本链接
        self.ocgRule = None

    def __str__(self):
        return self.info()

    def __repr__(self):
        id = self._checkAndFill(self.id, "{}")
        name = self._checkAndFill(self.name, "{}," if id else "{}")
        content = self._checkAndFill(f"{name}{id}", "({})")
        return f"{self.__class__.__name__}{content}"

    @property
    def isMonster(self):
        return CardType.Monster in self.cardType

    @property
    def isXyz(self):
        return CardType.Xyz in self.cardType

    @property
    def isP(self):
        return CardType.Pendulum in self.cardType

    @property
    def isLink(self):
        return CardType.Link in self.cardType

    def fillCardType(self, *types: CardType | str):
        for t in types:
            if isinstance(t, str) and (ct := CardType.fromStr(t)):
                self.cardType.add(ct)
            else:
                self.cardType.add(t)

    def initMonster(self):
        if self.isMonster:
            self.attack = None  # 攻击力
            self.defence = None  # 守备力
            self.level = None  # 等级
            self.race = None  # 种族
            self.attribute = None  # 属性
            if self.isXyz:
                self.rank = None
            if self.isP:
                self.Pmark = [None, None]
            if self.isLink:
                self.linknum = None
                self.linkmark = set()

    @staticmethod
    def _checkAndFill(text, filltext: str, default=""):
        if text is not None:
            return filltext.format(text)
        return default

    def info(self):
        result = ""
        result += self._checkAndFill(self.name, "卡名 {}\n")
        result += self._checkAndFill(self.jpname, "日文名 {}\n")
        result += self._checkAndFill(self.enname, "英文名 {}\n")
        if self.cardType:  # 卡片种类
            result += f"{' '.join(str(ct) for ct in self.cardType)}\n"
        if self.isRD:
            result += "RUSH DUEL  "
        else:
            # result+=self._checkAndFill(self.id,"密码 {}  ")
            result += self._checkAndFill(self.id, "{}  ")
        result += self._checkAndFill(self.limit, "{}")  # 禁限
        result += self._checkAndFill(self.ot, "  {}\n", "\n")  # O/T
        if self.set:  # 卡片字段
            result += f"系列 {' '.join(self.set)}\n"
        if self.isMonster:
            result += self._checkAndFill(str(self.race), "{}族")
            result += self._checkAndFill(str(self.attribute), "  {}属性")
            if self.isXyz:
                result += self._checkAndFill(self.rank, "  {}阶\n")
            if self.isLink:
                result += self._checkAndFill(self.linknum, "  LINK-{}\n")
                # result+=self._checkAndFill(self.attack,"攻击力 {}\n")
                result += self._checkAndFill(self.attack, "{}/-\n")
                middle = linkMark2str[len(linkMark2str) // 2]
                # marklist=["   "]*8
                # marklist=[middle]*8
                marklist = [
                    str(lm) if lm in self.linkmark else middle for lm in LinkMark
                ]
                marklines = [
                    f"{marklist[5]}{marklist[6]}{marklist[7]}\n",
                    f"{marklist[3]}{middle}{marklist[4]}\n",
                    f"{marklist[0]}{marklist[1]}{marklist[2]}\n",
                ]
                result += "".join(line for line in marklines if line.strip())
            else:
                if not self.isXyz:
                    result += self._checkAndFill(self.level, "  {}星\n")
                # result+=self._checkAndFill(self.attack,"攻击力 {}")
                # result+=self._checkAndFill(self.defence,"  守备力 {}\n")
                result += self._checkAndFill(self.attack, "{}/")
                result += self._checkAndFill(self.defence, "{}\n")
            if self.isP:
                if self.effect and not self.effect.startswith("←"):
                    result += f"←{self.Pmark[0]} 【灵摆】 {self.Pmark[1]}→\n"
        effecttext = self._checkAndFill(self.effect, "{}")
        result += effecttext.replace("・", "·")
        return result

    def fromCDBTuple(self, t, setdict: dict = None, lfdict: dict = None):
        self.name = t[0]
        self.effect = t[1]
        self.id = t[2]
        if t[3] == 1:
            self.ot = "OCG专有卡"
        elif t[3] == 2:
            self.ot = "TCG专有卡"
        if t[4] != 0:
            self.alias = self.id
            self.id = t[4]
        if setdict:
            setval = t[5]
            while setval != 0:
                setname = setdict.get(setval & 0xFFFF, None)
                if setname:
                    self.set.add(setname)
                setval = setval >> 16
        if lfdict:
            lfname = ["禁止", "限制", "准限制", "无限制"]
            lfnum = lfdict.get(self.id, 3)
            self.limit = lfname[lfnum]
        self.cardType = Card.bit2CardTypes(t[6])
        if self.isMonster:
            self.attack = Card.dealAtkDef(t[7])
            self.level = Card.dealLevel(t[9])
            if self.isLink:
                self.linkmark = Card.bit2LinkMark(t[8])
                self.linknum = self.level
            else:
                self.defence = Card.dealAtkDef(t[8])
            if self.isXyz:
                self.rank = self.level
            if self.isP:
                self.Pmark = Card.getPmark(t[9])
            self.race = Card.bit2Race(t[10])
            self.attribute = Card.bit2Attribute(t[11])
            self.category = Card.bit2Category(t[12])

    @staticmethod
    def dealAtkDef(val):
        return val if val >= 0 else "?"

    @staticmethod
    def dealLevel(val):
        return val & 0b1111

    @staticmethod
    def getPmark(val):
        pl = (val & 0xF000000) >> 24
        pr = (val & 0x00F0000) >> 16
        return [pl, pr]

    @staticmethod
    def bit2Set(bit, enum: type[Enum]):
        return {x for x in enum if x.value & bit != 0}

    @staticmethod
    def bit2Item(bit, enum: type[Enum]):
        if any((r := x) for x in enum if x.value & bit != 0):
            return r
        return None

    # @staticmethod
    # def funcWithEnum(func,enum):
    #     def wrapper(bit):
    #         return func(bit,enum)
    #     return wrapper

    bit2CardTypes = partialmethod(bit2Set, enum=CardType)
    bit2Race = partialmethod(bit2Item, enum=CardRace)
    bit2Attribute = partialmethod(bit2Item, enum=CardAttribute)
    bit2LinkMark = partialmethod(bit2Set, enum=LinkMark)
    bit2Category = partialmethod(bit2Set, enum=CardCategory)
    # bit2CardTypes=funcWithEnum.__func__(bit2Set.__func__,CardType)
    # bit2Race=funcWithEnum.__func__(bit2Item.__func__,CardRace)
    # bit2Attribute=funcWithEnum.__func__(bit2Item.__func__,CardAttribute)
    # bit2Linkmark=funcWithEnum.__func__(bit2Set.__func__,LinkMark)
    # bit2Category=funcWithEnum.__func__(bit2Set.__func__,CardCategory)


# Card.bit2CardTypes=Card.funcWithEnum(Card.bit2Set,CardType)
