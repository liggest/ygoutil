from __future__ import annotations

from typing import TYPE_CHECKING

from functools import cached_property

if TYPE_CHECKING:
    from typing import Literal
    from ygoutil.card.card import Card

from ygoutil.card.constant import (CardType, CardCategory, CardRace, CardAttribute, LinkMark, LinkMarkStyle, 
                                   CardOT, CardLF)
from ygoutil.card.misc import check_cached_property, line_or_not

class CardUnit:
    """ 卡片组成部分 """

    def __init__(self, owner: Card):
        self._owner = owner

    def info(self) -> str:
        return ""

class IDUnit(CardUnit):
    """ 卡号 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.id: int | str = 0

    def info(self):
        return str(self.id)

class AliasIDUnit(IDUnit):
    """ 同名卡卡号 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        # self.id: int | str = 0
        self.alias_id: int | str = 0

class RushDuelIDUnit(IDUnit):
    """ RD 卡无卡号 """

    def __init__(self, owner: Card):
        super(IDUnit, self).__init__(owner)
        self.id = "RUSH DUEL"

class NameUnit(CardUnit):
    """ 卡名 """
    
    def __init__(self, owner: Card):
        super().__init__(owner)
        self.name: str = ""

    def info(self):
        return self.name

class CnJpEnNameUnit(NameUnit):
    """ 中日英卡名 """

    show_ruby = False
    """ 是否在 info 中显示日文注音（默认不显示） """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.jp_name: str = ""
        self.jp_ruby: str = ""
        self.en_name: str = ""

    @property
    def cn_name(self):
        return self.name
    
    @cn_name.setter
    def cn_name(self, value: str):
        self.name = value

    def _jp_info(self):
        if self.show_ruby and self.jp_ruby and self.jp_ruby != self.jp_name:
            return f"{self.jp_name}（{self.jp_ruby}）"
        return self.jp_name

    def info(self):
        return f"{line_or_not(super().info())}{line_or_not(self._jp_info())}{line_or_not(self.en_name)}".rstrip()


class TextUnit(CardUnit):
    """ 卡片文本 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self._text: str = ""
    
    @property
    def text(self):
        """ 文本 """
        return self._text
    
    @text.setter
    def text(self, value: str):
        self._text = value

    def info(self):
        return self.text

class PTextUnit(TextUnit):
    """ 灵摆效果文本 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.p_text: str = ""

    @property
    def splitter(self):
        return "【怪兽效果】" if self._owner.is_effect else "【怪兽描述】"

    @property
    def text(self):
        return f"{self.p_text.rstrip()}\n{self.splitter}\n{self._text}"

    @text.setter
    def text(self, value: str):
        self.p_text, self._text = value.split(self.splitter, maxsplit=1) # 切分灵摆效果和怪兽效果
        self.p_text = self.p_text.rstrip()
        if self.p_text.startswith("←") and (idx := self.p_text.find("→")) > 0:
            self.p_text = self.p_text[idx + 1:].lstrip()    # 试着除去灵摆效果开头的 ← ...【灵摆】... →
        self._text = self._text.lstrip()

    @classmethod
    def from_base(cls, base_unit: TextUnit):
        unit = cls(base_unit._owner)
        unit._text = base_unit._text
        return unit

class LimitUnit(CardUnit):
    """ 卡片可用性 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.ot: str | CardOT = CardOT.Unknown
        self.limit: str | CardLF = CardLF.无限制

    def _ot_info(self):
        if isinstance(self.ot, CardOT):
            return { CardOT.OCG: "OCG", CardOT.TCG: "TCG", CardOT.Custom: "DIY", CardOT.SC: "简中" }.get(self.ot, "")
        return self.ot

    def _limit_info(self):
        if self.limit is CardLF.无限制:  # 无限制不显示
            return ""
        return str(self.limit)

    def info(self):
        if self.ot:
            return f"{self._limit_info()}  {self._ot_info()}"
        return self._limit_info()

class SetUnit(CardUnit):
    """ 卡片系列（字段） """

    @cached_property
    def sets(self) -> set[str]:
        return set()

    def info(self):
        return " ".join(self.sets)

class TypeUnit(CardUnit):
    """ 卡片类型 """

    @cached_property
    def types(self) -> set[CardType | str]:  # set[str] 兼容一些未定义的类型
        return set()

    @property
    def is_monster(self):
        """ 是怪兽 """
        return CardType.Monster in self.types

    @property
    def is_effect(self):
        """ 有效果 """
        return CardType.Effect in self.types

    @property
    def is_xyz(self):
        """ 是超量 """ 
        return CardType.Xyz in self.types

    @property
    def is_pendulum(self):
        """ 是灵摆 """ 
        return CardType.Pendulum in self.types

    @property
    def is_link(self):
        """ 是连接 """ 
        return CardType.Link in self.types
    
    def info(self):
        return " ".join(str(ct) for ct in self.types)

class CategoryUnit(CardUnit):
    """ 效果分类 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.categories: CardCategory = CardCategory.未知

class MonsterUnit(CardUnit):
    """ 怪兽卡 """

    @cached_property
    def levels(self):
        return LevelUnit(self._owner)
    
    @cached_property
    def _pmark_unit(self) -> PMarkUnit | None:
        return None

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.attribute: CardAttribute = CardAttribute.Unknown
        self.race: CardRace = CardRace.Unknown
        self.attack: int | Literal["?"] | None = None
        self.defence: int | Literal["?"] | None = None
        self._init_units()

    def _init_units(self):
        if self._owner.is_xyz:
            self.levels = RankUnit(self._owner)
        if self._owner.is_pendulum:
            self._pmark_unit = PMarkUnit(self._owner)
        if self._owner.is_link:
            self.levels = LinkUnit(self._owner)

    @property
    def level(self):
        return self.levels.level

    @level.setter
    def level(self, value: int):
        self.levels.level = value

    @property
    def xyz(self):
        if isinstance(self.levels, RankUnit):
            return self.levels
        raise AttributeError("Not an xyz monster")

    @property
    def pendulum(self):
        if self._pmark_unit:
            return self._pmark_unit
        raise AttributeError("Not a pendulum monster")

    @property
    def link(self):
        if isinstance(self.levels, LinkUnit):
            return self.levels
        raise AttributeError("Not a link monster")

    def _atk_def_info(self):
        attack = str(self.attack) if self.attack is not None else "-"
        defence = str(self.defence) if self.defence is not None else "-"  # defence 不存在时为 None
        return f"{attack} / {defence}" if attack and defence else ""

    def _info_gen(self):
        line = ""
        if self.race:
            line = f"{self.race}族"
        if self.attribute:
            line = f"{line}  {self.attribute}属性"
        if level_info := self.levels.info():
            line = f"{line}  {level_info}"
        yield line_or_not(line)
        yield line_or_not(self._atk_def_info())
        if isinstance(self.levels, LinkUnit):
            yield line_or_not(self.levels._mark_info())  # 连接标识
        if self._pmark_unit:
            yield line_or_not(self._pmark_unit.info())

    def info(self):
        return "".join(self._info_gen())

class LevelUnit(CardUnit):
    """ 怪兽等级 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self._level: int | None = None
    
    @property
    def level(self):
        """ 怪兽等级 """
        return self._level
    
    @level.setter
    def level(self, value: int):
        self._level = value

    def info(self):
        return f"{self._level}星" if self._level else ""

class RankUnit(LevelUnit):
    """ 超量怪兽阶级 """

    def __init__(self, owner: Card):
        super(LevelUnit, self).__init__(owner)
        self.rank: int | None = None

    @property
    def level(self):
        """ 超量怪兽阶级 """
        return self.rank
    
    @level.setter
    def level(self, value: int):
        self.rank = value

    def info(self):
        return f"{self.rank}阶" if self.rank else ""
    
class LinkUnit(LevelUnit):
    """ 链接怪兽 LINK 数 """

    def __init__(self, owner: Card):
        super(LevelUnit, self).__init__(owner)
        self.link: int | None = None
        self.marks: LinkMark = LinkMark.Unknown

    @property
    def level(self):
        """ 链接怪兽 LINK 数 """
        return self.link
    
    @level.setter
    def level(self, value: int):
        self.link = value

    def info(self):
        return f"LINK-{self.link}" if self.link else ""
    
    def _mark_info(self):
        empty = LinkMarkStyle.middle()
        marks_str = [
            str(mark) if mark in self.marks else empty 
            for mark in LinkMark if mark  # ignore LinkMark(0x00)
        ]
        lines: list[tuple[str, str, str]] = [
            (marks_str[5], marks_str[6], marks_str[7]),
            (marks_str[3], empty       , marks_str[4]),
            (marks_str[0], marks_str[1], marks_str[2])
        ]
        return "\n".join(  # join all line
            ''.join(line) for line in lines  # join one line
            if any(mark is not empty for mark in line)  # if line is not empty
        )


class PMarkUnit(CardUnit):
    """ 灵摆刻度 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.left: int | None = None
        self.right: int | None = None
        # self._init_p_text()  # 默认不用 PTextUnit，只有当效果文本能区分怪效和灵摆效果时才用

    @property
    def mark(self):
        """ 灵摆刻度 """
        return self.left, self.right

    @mark.setter
    def mark(self, value: tuple[int, int]):
        self.left, self.right = value

    def _init_p_text(self):
        if base_unit := check_cached_property(self._owner, "texts"):
            self._owner._text_unit = PTextUnit.from_base(base_unit)
        else:
            self._owner._text_unit = PTextUnit(self._owner)

    def info(self):
        return f"←{self.left} 【灵摆】 {self.right}→" if self.left and self.right else ""

class URLUnit(CardUnit):
    """ 相关链接 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.url: str = ""
        """ 卡片数据来源链接 """
        self.pic: str = ""
        """ 卡图链接 """
