
from functools import cached_property

from ygoutil.card.constant import CardType, CardCategory
from ygoutil.card.unit import (IDUnit, NameUnit, TextUnit, LimitUnit, 
                               SetUnit, TypeUnit, CategoryUnit, MonsterUnit, URLUnit, CardUnit)
from ygoutil.card.misc import line_or_not

class Card:
    """ YGO 卡片 """

    @cached_property
    def _id_unit(self):
        return IDUnit(self)

    @cached_property
    def _name_unit(self):
        return NameUnit(self)

    @cached_property
    def _text_unit(self):
        return TextUnit(self)

    @cached_property
    def _limit_unit(self) -> LimitUnit | None:
        return None

    @cached_property
    def _set_unit(self) -> SetUnit | None:
        return None
    
    @cached_property
    def _type_unit(self):
        return TypeUnit(self)
    
    @cached_property
    def _category_unit(self) -> CategoryUnit | None:
        return None
    
    @cached_property
    def _monster_unit(self) -> MonsterUnit | None:
        return None
    
    @cached_property
    def _url_unit(self) -> URLUnit | None:
        return None

    @cached_property
    def _extra_unit(self) -> CardUnit | None:
        return None
    
    @property
    def ids(self):
        return self._id_unit
    
    @property
    def id(self):
        return self._id_unit.id
    
    @id.setter
    def id(self, value: int | str):
        self._id_unit.id = value

    @property
    def names(self):
        return self._name_unit

    @property
    def name(self):
        return self._name_unit.name
    
    @name.setter
    def name(self, value: str):
        self._name_unit.name = value
    
    @property
    def texts(self):
        return self._text_unit

    @property
    def text(self):
        return self._text_unit.text
    
    @text.setter
    def text(self, value: str):
        self._text_unit.text = value

    @property
    def limits(self):
        if self._limit_unit:
            return self._limit_unit
        raise AttributeError("Card does not have limitation data")

    @property
    def sets(self):
        if self._set_unit:
            return self._set_unit.sets
        raise AttributeError("Card does not have sets")

    @sets.setter
    def sets(self, value: set[str]):
        if not self._set_unit:
            self._set_unit = SetUnit(self)
        self._set_unit.sets = value

    @property
    def types(self):
        return self._type_unit.types

    @types.setter
    def types(self, value: set[CardType | str]):
        self._type_unit.types = value

    @property
    def categories(self):
        if self._category_unit:
            return self._category_unit.categories
        raise AttributeError("Card does not have categories")

    @categories.setter
    def categories(self, value: CardCategory):
        if not self._category_unit:
            self._category_unit = CategoryUnit(self)
        self._category_unit.categories = value

    @property
    def monster(self):
        if self._monster_unit:
            return self._monster_unit
        raise AttributeError("Card is not a monster")

    @property
    def urls(self):
        if self._url_unit:
            return self._url_unit
        raise AttributeError("Card does not have urls")

    @property
    def extras(self):
        if self._extra_unit:
            return self._extra_unit
        raise AttributeError("Card does not have extra data")

    @property
    def is_monster(self):
        """ 是怪兽 """
        return self._type_unit.is_monster

    @property
    def is_effect(self):
        """ 有效果 """
        return self._type_unit.is_effect

    @property
    def is_xyz(self):
        """ 是超量 """ 
        return self._type_unit.is_xyz

    @property
    def is_pendulum(self):
        """ 是灵摆 """ 
        return self._type_unit.is_pendulum

    @property
    def is_link(self):
        """ 是连接 """ 
        return self._type_unit.is_link

    @classmethod
    def from_types(cls, *types: CardType | str):
        """ 从 types 创建卡片 """
        card = Card()
        card._fill_types(*types)
        card._init_monster()
        return card

    def _fill_types(self, *types: CardType | str):
        for t in types:
            if isinstance(t, str) and (ct := CardType.from_str(t)):
                self.types.add(ct)
            else:
                self.types.add(t)

    def _init_monster(self):
        if self.is_monster:
            self._monster_unit = MonsterUnit(self)

    def _info_gen(self):
        yield line_or_not(self._name_unit.info())        # 卡名
        yield line_or_not(self._type_unit.info())        # 类型
        line = f"{self._id_unit.info()}"                 # 卡号、禁限、OT
        if self._limit_unit:
            line = f"{line}  {self._limit_unit.info()}"
        yield line_or_not(line)
        if self._set_unit:
            yield line_or_not(self._set_unit.info())     # 字段
        if self._monster_unit:
            yield line_or_not(self._monster_unit.info()) # 怪兽
        yield self._text_unit.info()                     # 卡片文本，不用再换行
        
    def info(self):
        """ 卡片信息 """
        return "".join(self._info_gen())
        
    def __str__(self):
        return self.info()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id!r}, {self.name!r}, {self.types!r})"
