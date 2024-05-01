from enum import Enum
from typing import Iterable
from functools import partialmethod

from ygoutil.card.constant import CardType, CardRace, CardAttribute, LinkMark, LinkMarkStyle, CardCategory

class Card:
    """YGO 卡片"""

    def __init__(self, types: Iterable[CardType | str] = None):
        self.id = None  # 卡号
        self.name: str | None = None  # 卡名（中文）
        self.jpname: str | None = None  # 卡名（日文）
        self.enname: str | None = None  # 卡名（英文）
        self.effect: str | None = None  # 效果文本

        self.ot: str | None = None  # ot状态
        self.set = set()  # 系列
        self.cardType: set[CardType | str] = set()  # 卡片类型
        self.limit: str | None = None  # 禁限

        self.category: set[CardCategory] = set()  # 效果种类

        self.alias = None  # 作为同名卡在数据库中的实际卡号

        self.isRD = False  # RD卡

        if types:
            self.fillCardType(*types)
            self.initMonster()  # 根据卡片类型初始化怪兽信息
        # 一系列链接
        self.img: str | None = None  # 卡图链接
        self.url: str | None = None  # 卡片信息来源链接
        self.database: str | None = None
        self.QA: str | None = None
        self.wiki: str | None = None
        self.yugipedia: str | None = None
        # self.ygorg=None
        self.ourocg: str | None = None
        self.script: str | None = None  # 脚本链接
        self.ocgRule: str | None = None

    def __str__(self):
        return self.info()

    def __repr__(self):
        id = self._checkAndFill(self.id, "{}")
        name = self._checkAndFill(self.name, "{}," if id else "{}")
        content = self._checkAndFill(f"{name}{id}", "({})")
        return f"{self.__class__.__name__}{content}"

    @property
    def isMonster(self):
        """ 是怪兽卡 """
        return CardType.Monster in self.cardType

    @property
    def isXyz(self):
        """ 是超量 """ 
        return CardType.Xyz in self.cardType

    @property
    def isP(self):
        """ 是灵摆 """ 
        return CardType.Pendulum in self.cardType

    @property
    def isLink(self):
        """ 是连接 """
        return CardType.Link in self.cardType

    def fillCardType(self, *types: CardType | str):
        for t in types:
            if isinstance(t, str) and (ct := CardType.from_str(t)):
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
                self.rank = None  # 阶级
            if self.isP:
                self.Pmark = [None, None]  # 刻度
            if self.isLink:
                self.linknum = None  # link 数
                self.linkmark: set[LinkMark] = set()

    @staticmethod
    def _checkAndFill(text, filltext: str, default=""):
        if text is not None:
            return filltext.format(text)
        return default

    def _infoGen(self):
        yield self._checkAndFill(self.name, "卡名 {}\n")
        yield self._checkAndFill(self.jpname, "日文名 {}\n")
        yield self._checkAndFill(self.enname, "英文名 {}\n")
        if self.cardType:  # 卡片种类
            yield f"{' '.join(str(ct) for ct in self.cardType)}\n"
        if self.isRD:
            yield "RUSH DUEL  "
        else:
            yield self._checkAndFill(self.id, "{}  ")
        yield self._checkAndFill(self.limit, "{}")  # 禁限
        yield self._checkAndFill(self.ot, "  {}\n", "\n")  # O/T
        if self.set:  # 卡片字段
            yield f"{' '.join(self.set)}\n"
        if self.isMonster:
            yield self._checkAndFill(str(self.race), "{}族")
            yield self._checkAndFill(str(self.attribute), "  {}属性")
            if self.isXyz:
                yield self._checkAndFill(self.rank, "  {}阶\n")
            if self.isLink:
                yield self._checkAndFill(self.linknum, "  LINK-{}\n")
                # result+=self._checkAndFill(self.attack,"攻击力 {}\n")
                yield self._checkAndFill(self.attack, "{}/-\n")
                # middle = linkMark2str[len(linkMark2str) // 2]
                middle = LinkMarkStyle.middle()
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
                yield "".join(line for line in marklines if line.strip())
            else:
                if not self.isXyz:
                    yield self._checkAndFill(self.level, "  {}星\n")
                # result+=self._checkAndFill(self.attack,"攻击力 {}")
                # result+=self._checkAndFill(self.defence,"  守备力 {}\n")
                yield self._checkAndFill(self.attack, "{}/")
                yield self._checkAndFill(self.defence, "{}\n")
            if self.isP:
                if self.effect and not self.effect.startswith("←"):
                    yield f"←{self.Pmark[0]} 【灵摆】 {self.Pmark[1]}→\n"
        effecttext = self._checkAndFill(self.effect, "{}")
        yield effecttext.replace("・", "·")

    def info(self):
        """ 卡片信息 """
        return "".join(self._infoGen())

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
        r = None
        if any((r := x) for x in enum if x.value & bit != 0):
            return r
        return None

    # @staticmethod
    # def funcWithEnum(func,enum):
    #     def wrapper(bit):
    #         return func(bit,enum)
    #     return wrapper

    bit2CardTypes: partialmethod[set[CardType | str]] = partialmethod(bit2Set, enum=CardType)
    bit2Race: partialmethod[CardRace] = partialmethod(bit2Item, enum=CardRace)
    bit2Attribute: partialmethod[CardAttribute] = partialmethod(bit2Item, enum=CardAttribute)
    bit2LinkMark: partialmethod[set[LinkMark]] = partialmethod(bit2Set, enum=LinkMark)
    bit2Category: partialmethod[set[CardCategory]] = partialmethod(bit2Set, enum=CardCategory)
    # bit2CardTypes=funcWithEnum.__func__(bit2Set.__func__,CardType)
    # bit2Race=funcWithEnum.__func__(bit2Item.__func__,CardRace)
    # bit2Attribute=funcWithEnum.__func__(bit2Item.__func__,CardAttribute)
    # bit2Linkmark=funcWithEnum.__func__(bit2Set.__func__,LinkMark)
    # bit2Category=funcWithEnum.__func__(bit2Set.__func__,CardCategory)


# Card.bit2CardTypes=Card.funcWithEnum(Card.bit2Set,CardType)
