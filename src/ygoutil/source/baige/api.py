
from typing import AsyncGenerator, TYPE_CHECKING, Literal, overload

from ygoutil.card import Card
from ygoutil.card.ids import CnJpEnIDCard
from ygoutil.card.unit import PTextUnit, URLUnit
from ygoutil.source.base import CardSource, QueryInfo
from ygoutil.source.baige.misc import Site, BaiGeResult, BaiGeCard, BaiGeNameUnit, BaiGeExtraUnit
from ygoutil.source.misc import get_json, USE_CLIENT_DEFAULT, deal_web_text
from ygoutil.source.cdb.misc import card_from_types, card_from_cdb_data

class BaiGe(CardSource):
    """ 查百鸽 """

    _api_url = f"{Site.base_url}api/v0/"
    timeout = USE_CLIENT_DEFAULT
    """ HTTP 请求的超时时间 """

    def _json2card(self, json: BaiGeCard) -> Card:
        data = json["data"]
        types = data["type"]
        card = card_from_types(types)
        card = card_from_cdb_data(card, json["id"], data["ot"], 0, data["setcode"], types, 
                                  data["atk"], data["def"], data["level"], data["race"], data["attribute"], 0)
        card._name_unit = BaiGeNameUnit(card).update_from(json)
        if isinstance(card._text_unit, PTextUnit):
            card._text_unit.p_text = deal_web_text(json["text"]["pdesc"])
        card._text_unit._text = deal_web_text(json["text"]["desc"])
        card._url_unit = URLUnit(card)
        card_id = card.id
        card._url_unit.url = Site.card_page_url(card_id)
        card._url_unit.pic = Site.card_pic_url(card_id)  # 卡图有极小概率不存在
        card._extra_unit = BaiGeExtraUnit(card).update_from(json)
        return card

    def _json2ids(self, json: BaiGeCard) -> CnJpEnIDCard:
        return CnJpEnIDCard(json["id"], json.get("cn_name", ""), json.get("jp_name", ""), json.get("en_name", ""))

    async def from_id(self, card_id: int) -> Card | None:
        return await self.from_query(str(card_id))
    
    async def from_name(self, card_name: str) -> Card | None:
        return await self.from_query(card_name)

    if TYPE_CHECKING:
        @overload   # 用 overload 和字面量来区分返回值
        async def _gen_from_query(self, query: str, ids_only: Literal[False] = False) -> AsyncGenerator[Card, None]:
            ...

        @overload
        async def _gen_from_query(self, query: str, ids_only: Literal[True] = True) -> AsyncGenerator[CnJpEnIDCard, None]:
            ...

    async def _gen_from_query(self, query: str, ids_only = False):
        result: BaiGeResult = await get_json(self._api_url, params=Site.query_params(query), timeout=self.timeout)
        self.current_query = QueryInfo(query, len(result["result"]))
        for card in result["result"]:
            self.current_query.current += 1
            if ids_only:
                yield self._json2ids(card)
            else:
                yield self._json2card(card)

    async def gen_from_query(self, query: str) -> AsyncGenerator[Card, None]:
        async for card in self._gen_from_query(query):
            yield card

    async def gen_ids_from_query(self, query: str) -> AsyncGenerator[CnJpEnIDCard, None]:
        async for card in self._gen_from_query(query, ids_only=True):
            yield card
