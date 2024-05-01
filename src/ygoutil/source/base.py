
from abc import ABCMeta, abstractmethod
from typing import AsyncGenerator
from dataclasses import dataclass
from functools import cached_property

from ygoutil.card import Card
from ygoutil.card.ids import IDCard
from ygoutil.source.misc import gen_limit

@dataclass
class QueryInfo:
    """ 查询信息 """
    query: str = ""
    total: int = 0
    current: int = 0

    def __bool__(self):
        return bool(self.query or self.total or self.current)

class CardSource(metaclass=ABCMeta):
    """ 卡片源 """

    @cached_property
    def current_query(self) -> QueryInfo:
        """ 当前查询信息 """
        return QueryInfo("")

    @abstractmethod
    async def from_id(self, card_id: int) -> Card | None:
        """ 由卡号获取一张卡 """
        raise NotImplementedError

    @abstractmethod
    async def from_name(self, card_name: str) -> Card | None:
        """ 由卡名获取一张卡 """
        raise NotImplementedError

    @abstractmethod
    async def gen_from_query(self, query: str) -> AsyncGenerator[Card, None]:
        """ 由 query 获取一组卡片 """
        raise NotImplementedError
        yield

    @abstractmethod
    async def gen_ids_from_query(self, query: str) -> AsyncGenerator[IDCard, None]:
        """ 由 query 获取一组卡片标识（卡号、卡名） """
        raise NotImplementedError
        yield

    async def from_query(self, query: str):
        """ 由 query 获取一张卡 """
        return await anext(self.gen_from_query(query), None)

    async def list_from_query(self, query: str, limit: int = 100):
        """ 由 query 获取一组卡片 """
        return [card async for card in gen_limit(self.gen_from_query(query), limit)]

    async def list_ids_from_query(self, query: str, limit: int = 100):
        """ 由 query 获取一组卡片标识（卡号、卡名） """
        return [card async for card in gen_limit(self.gen_ids_from_query(query), limit)]
