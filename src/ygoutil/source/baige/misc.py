
from typing import TypedDict
from typing_extensions import NotRequired

from ygoutil.card.card import Card
from ygoutil.card.unit import CnJpEnNameUnit, CardUnit, URLUnit

class Site:
    base_url = "https://ygocdb.com/"
    pics_url = "https://cdn.233.momobako.com/ygopro/pics/"

    @classmethod
    def card_pic_url(cls, card_id: int | str):
        return f"{cls.pics_url}{card_id}.jpg"

    @classmethod
    def card_page_url(cls, card_id: int | str):
        return f"{cls.base_url}card/{card_id}"
    
    @classmethod
    def faq_url(cls, faq_id: int):
        return f"{cls.base_url}faq/{faq_id}"

    @staticmethod
    def query_params(query: str):
        return {"search": query}

class CardText(TypedDict):
    types: str  # 例：[怪兽|效果] 种族/属性\n[★3] 1300/400
    pdesc: str
    desc: str

CardData = TypedDict("CardData", {
    "ot": int, 
    "setcode": int, 
    "type": int,
    "atk": int,
    "def": int,     # def 是关键字，所以 CardData 只能用这种形式定义
    "level": int,
    "race": int,
    "attribute": int
})

class CardHTML(TypedDict):
    pdesc: str
    desc: str
    refer: dict[str, bool]

class BaiGeCard(TypedDict):
    cid: int
    id: int

    cn_name: NotRequired[str]
    sc_name: NotRequired[str]
    md_name: NotRequired[str]
    nwbbs_n: NotRequired[str]
    cnocg_n: NotRequired[str]
    jp_ruby: NotRequired[str]
    jp_name: NotRequired[str]
    en_name: NotRequired[str]

    text: CardText
    data: CardData
    html: CardHTML

    weight: int
    faqs: list[str]
    artid: int

class BaiGeResult(TypedDict):
    result: list[BaiGeCard]
    next: int

class BaiGeNameUnit(CnJpEnNameUnit):
    """ 百鸽卡名 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.sc_name: str = ""
        self.md_name: str = ""
        self.nwbbs_name: str = ""
        self.cnocg_name: str = ""

    def update_from(self, card: BaiGeCard):
        self.cn_name = card.get("cn_name", "")
        self.sc_name = card.get("sc_name", "")
        self.md_name = card.get("md_name", "")
        self.nwbbs_name = card.get("nwbbs_n", "")
        self.cnocg_name = card.get("cnocg_n", "")
        self.jp_name = card.get("jp_name", "")
        self.jp_ruby = card.get("jp_ruby", "")
        self.en_name = card.get("en_name", "")
        return self

class BaiGeExtraUnit(CardUnit):
    """ 百鸽额外信息 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.c_id: int = 0                    # 百鸽数据库编号
        self.weight: int = 0
        self.art_id: int = 0
        self.refers: list[int] | None = None  # 效果中关联到的卡的卡号
        self.faqs: list[int] | None = None    # FAQ 号

    def update_from(self, card: BaiGeCard):
        self.c_id = card["cid"]
        self.weight = card["weight"]
        self.art_id = card["artid"]
        self.refers = [int(id) for id in card["html"]["refer"]]
        self.faqs = [int(fid) for fid in card["faqs"]]
        return self

class BaiGeURLUnit(URLUnit):
    """ 百鸽链接 """

    def __init__(self, owner: Card):
        super().__init__(owner)
        self.database_jp: str = ""
        self.database_en: str = ""
        self.database_cn: str = ""
        self.QA: str = ""
        self.wiki: str = ""
        self.yugipedia: str = ""
        self.ourocg: str = ""
        self.script: str = ""
        self.ocg_rule: str = ""

    @property
    def database(self):
        return self.database_jp
    
    @database.setter
    def database(self, value: str):
        self.database_jp = value
