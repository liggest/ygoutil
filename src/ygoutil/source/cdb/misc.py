from typing import TypeVar
from enum import IntFlag
from functools import partial

from ygoutil.card import Card
from ygoutil.card.unit import AliasIDUnit, LimitUnit, SetUnit, LinkUnit, CategoryUnit, PTextUnit
from ygoutil.card.constant import CardType, CardRace, CardAttribute, CardCategory, LinkMark, CardOT, CardLF

def deal_atk_def(val: int):
    return val if val >= 0 else "?"

def deal_level(val: int):
    return val & 0b1111

def deal_p_mark(val: int):
    pl = (val & 0xF000000) >> 24
    pr = (val & 0x00F0000) >> 16
    return pl, pr

FlagVar = TypeVar("FlagVar", bound=IntFlag)

def bits2set(bits: int, flags: type[FlagVar]) -> set[FlagVar]:
    return {x for x in flags if x & bits != 0}

def bits2item(bits: int, flags: type[FlagVar]) -> FlagVar:
    r = flags(0)
    any((r := x) for x in flags if x & bits != 0)
    return r

bits2CardTypes = partial(bits2set, flags=CardType)
bits2Race = partial(bits2item, flags=CardRace)
bits2Attribute = partial(bits2item, flags=CardAttribute)
bits2LinkMark = partial(bits2item, flags=LinkMark)
bits2Category = partial(bits2item, flags=CardCategory)

def card_from_types(types: int):
    return Card.from_types(*bits2CardTypes(types))

def card_from_cdb_text(card: Card, name: str, text: str) -> Card:
    card.name = name
    card.text = text
    return card

def card_from_cdb_data(card: Card, id: int, ot: int, alias: int, sets: int, types: int, 
                      attack: int, defence: int, level: int, race: int, attribute: int, category: int,
                      set_map: dict[int, str] = None, lf_map: dict[int, int] = None) -> Card:
    if alias:
        id, alias = alias, id  # alias 里面才是真的卡号，id 里面是替身卡号
        card._id_unit = AliasIDUnit(card)
        card._id_unit.alias_id = alias
    card.id = id
    card._limit_unit = LimitUnit(card)  # 有 LimitUnit
    card.limits.ot = CardOT(ot)
    if lf_map:
        card.limits.limit = CardLF(lf_map.get(card.id, CardLF.无限制))
    if set_map:
        card._set_unit = SetUnit(card)  # 传入 set_map 的话，即使没有字段，也保证 SetUnit 存在
        while sets != 0:
            if set_name := set_map.get(sets & 0xFFFF):
                card.sets.add(set_name)
            sets = sets >> 16
    if card.is_monster:
        monster = card.monster
        monster.attack = deal_atk_def(attack)
        monster.level = deal_level(level)
        if isinstance(monster.levels, LinkUnit):
            monster.levels.marks = LinkMark(defence)  # 连接怪用防御记录连接标记
        else:
            monster.defence = deal_atk_def(defence)
        if monster._pmark_unit:
            monster._pmark_unit.mark = deal_p_mark(level)
            card._text_unit = PTextUnit(card)  # 灵摆怪兽试用 PTextUnit
        monster.race = CardRace(race)
        monster.attribute = CardAttribute(attribute)
    card._category_unit = CategoryUnit(card)  # 有 CategoryUnit
    card.categories = CardCategory(category)
    return card

def card_from_cdb(name: str, text: str, 
                      id: int, ot: int, alias: int, sets: int, types: int, 
                      attack: int, defence: int, level: int, race: int, attribute: int, category: int,
                      set_map: dict[int, str] = None, lf_map: dict[int, int] = None) -> Card:
    card = card_from_types(types)
    card = card_from_cdb_data(card, id, ot, alias, sets, types, 
                              attack, defence, level, race, attribute, category, set_map, lf_map)
    card = card_from_cdb_text(card, name, text)
    return card
