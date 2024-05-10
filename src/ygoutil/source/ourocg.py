# coding:utf-8
# import sqlite3
# import configparser
import json
from typing import TYPE_CHECKING, AsyncGenerator, overload, Literal
from urllib import parse
from enum import Enum
from dataclasses import dataclass
from functools import cached_property

import httpx
from bs4 import BeautifulSoup, NavigableString, CData, Tag, ResultSet
# from bs4.element import NavigableString, CData, Tag

try:
    from bs4.element import TemplateString  # 新版bs4需要
except ImportError:
    TemplateString = NavigableString

from ygoutil.card import Card, CardAttribute, CardRace, LinkMark, CardLF
from ygoutil.card.ids import CnJpEnIDCard
from ygoutil.card.unit import CnJpEnNameUnit, RushDuelIDUnit, URLUnit, LimitUnit
from ygoutil.source.base import CardSource, QueryInfo
from ygoutil.source.misc import get_html, deal_int

class Site:
    base_url = r"https://www.ourocg.cn/"
    wiki_url = r"https://yugioh-wiki.net/"

    @classmethod
    def search_url(cls, query: str, page: int = 0):
        if page:
            return f"{cls.base_url}search/{query}/{page}"
        return f"{cls.base_url}search/{query}"

@dataclass
class OurOcgIDCard(CnJpEnIDCard):
    nw_name: str = ""

@dataclass
class OurOcgQueryInfo(QueryInfo):
    total_page: int = 0
    current_page: int = 0

class Translate(Enum):
    """ 译文偏好 """
    CN = 0
    NW = 1
    DEFAULT = 2

class OurOcg(CardSource):
    """ 查 OurOcg 网页 """
    def __init__(self):
        self._edition = Translate.DEFAULT
        self.name_search_limit = 10
        """ 
            from_name 中精确比对卡名时，最多比对卡片数量\n
            默认最多 10 张（即 1 页），为 0 时表示无限制
        """

    def set_translate_edition(self, ed: str):
        """ 设置译文偏好为 'NW' 或 'CN' """
        trans = Translate.DEFAULT
        if any(trans := t for t in Translate if t.name == ed.upper()):
            self._edition = trans

    SetTranslateEdition = set_translate_edition  # 兼容

    @property
    def link(self):
        """ 网页链接 """
        return Site.base_url

    def _getHTML(self, url):
        res = httpx.get(url, follow_redirects=True)
        return res.text

    def _getCardHTMLWithJ(self, searchtext: str, url: str, searchHTML: str):
        targeturl: str = ""
        cardJson = None
        # Pmark=[None,None]
        html = BeautifulSoup(searchHTML, "lxml")
        if html.find_all("title")[0].string.startswith("搜索"):  # 搜索结果页
            scripts = html.find_all("script")
            for s in scripts:
                if str(s.string).strip().startswith("window.__STORE__"):
                    targets = str(s.string[s.string.find("{") :]).strip()[:-1]  # json
                    carddata = json.loads(targets)
                    sts = searchtext.strip()
                    for tar in carddata["cards"]:
                        if (
                            tar["name"] == sts
                            or tar["name_nw"] == sts
                            or tar["name_ja"] == sts
                            or tar["name_en"] == sts
                        ):
                            targeturl = tar["href"].replace("\\", "")
                            cardJson = tar
                            # Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                            # print(Pmark)
                    if targeturl == "" and len(carddata["cards"]) != 0:
                        tar = carddata["cards"][0]
                        targeturl = tar["href"].replace("\\", "")
                        cardJson = tar
                        # Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                    # print(targeturl)
                    break
        else:
            targeturl = url  # 直接是卡片详情页
        return targeturl, cardJson

    def _getCardFromHTML(self, cardHTML, cardJson) -> Card:
        if cardJson is None:
            cardJson = {}
        # print(cardJson)
        html = BeautifulSoup(cardHTML, "lxml")
        is_RD = self._is_RD(html)
        # div = html.find_all("div", {"class": "val"})
        # divr=[[y for y in x.stripped_strings] for x in div]
        divr = self._div_data(html)
        # 类似 stripped_strings，但新版本需要纳入 TemplateString 才能效果一致
        # print(divr)
        cardtypes = divr[3]
        c = Card.from_types(*cardtypes)
        if c.is_link:
            linkmark = html.find("div", {"class": "linkMark"})
            if TYPE_CHECKING:
                assert isinstance(linkmark, Tag)
            for mark in linkmark.find_all("i"):
                temp = mark["class"][1].split("_")
                if temp[2] == "on":
                    c.monster.link.marks |= LinkMark.from_number(int(temp[1]), with_mid=True)
        c._name_unit = CnJpEnNameUnit(c)
        cn_name, nw_name, c._name_unit.jp_name, c._name_unit.en_name = self._names_from_div(divr)
        c._name_unit.name = cn_name if self._edition is Translate.CN else nw_name  # 默认是 nw
        # c.isRD = isRD
        if is_RD:
            c._id_unit = RushDuelIDUnit(c)
        else:
            id = divr[4][0]
            id = int(id) if id and id != "-" else 0  # id 可能为 -
            c.id = id
        c._url_unit = URLUnit(c)
        c._url_unit.url = cardJson.get("href", "")    # 如果直接是卡片详情页，就没有
        c._url_unit.pic = cardJson.get("img_url", "")
        if TYPE_CHECKING:
            assert html.head and html.body
        if not c._url_unit.url:  # 试着从详情页直接获取连接
            if link_tag := html.head.find("link", {"rel": "canonical"}):
                if TYPE_CHECKING:
                    assert isinstance(link_tag, Tag)
                c._url_unit.url = str(link_tag.get("href", ""))
        if not c._url_unit.pic:
            if img_parent := html.body.find("div", {"class": "img"}):
                if TYPE_CHECKING:
                    assert isinstance(img_parent, Tag)
                if img_tag := img_parent.img:
                    c._url_unit.url = str(img_tag.get("src", ""))
        limitnum = 5
        if is_RD:
            limitnum = 4
        c._limit_unit = LimitUnit(c)
        limit = str(divr[limitnum][0])
        c._limit_unit.limit = CardLF.from_str(limit.removesuffix("卡")) or limit
        otnum = limitnum + 1
        if divr[otnum]:  # 如果是OCG/TCG专有
            c._limit_unit.ot = str(divr[otnum][0])
        effectnum = -1
        if c.is_monster:
            monster = c.monster
            monster.race = CardRace.from_str(divr[otnum + 1][0]) or CardRace.Unknown
            monster.attribute = CardAttribute.from_str(divr[otnum + 2][0]) or CardAttribute.Unknown
            # if c.isXyz:
            #     c.rank = OurOCG.dealInt(divr[otnum + 3][0])
            #     c.level = c.rank
            if monster._pmark_unit:
                # c.Pmark=Pmark
                monster._pmark_unit.mark = (cardJson.get("pend_l", None), cardJson.get("pend_r", None))
            if c.is_link:
                link = deal_int(divr[otnum + 5][0])
                attack = deal_int(divr[otnum + 4][0])
                if TYPE_CHECKING:
                    assert isinstance(link, int)
                    assert isinstance(attack, int)
                monster.link.link = link
                monster.attack = attack
            else:
                level = deal_int(divr[otnum + 3][0])
                attack = deal_int(divr[otnum + 4][0])
                defence = deal_int(divr[otnum + 5][0])
                if TYPE_CHECKING:
                    assert isinstance(level, int)
                    assert isinstance(attack, int)
                    assert isinstance(defence, int)
                monster.level = level
                monster.attack = attack
                monster.defence = defence
        L = len(divr[effectnum])
        tempString = divr[effectnum][-1]
        effectlist = [0]
        for x in range(-2, -1 * (L + 1), -1):
            if divr[effectnum][x] == tempString:
                tempnum = -1 - x
                effectlist.append(L - 2 * tempnum)
                effectlist.append(effectlist[1] + tempnum)
                effectlist.append(effectlist[2] + tempnum)
        effects = divr[effectnum][
            effectlist[self._edition.value] : effectlist[self._edition.value + 1]
        ]
        effectText = "\n".join(effects)
        c.text = self._beautifyText(effectText)
        return c

    def _findCardByName(self, searchtext):
        url = Site.search_url(searchtext)
        searchHTML = self._getHTML(url)
        targeturl, cardJson = self._getCardHTMLWithJ(searchtext, url, searchHTML)
        if targeturl:
            self.current_query = OurOcgQueryInfo(searchtext)
            cardHTML = self._getHTML(targeturl)
            self.current_query.current += 1
            return self._getCardFromHTML(cardHTML, cardJson)
        return None

    # async def AsyncGetHTML(self, url):
    #     async with httpx.AsyncClient() as client:
    #         res = await client.get(url)
    #         return res.text

    # async def AsyncSearchByName(self, searchtext: str):
    #     url = Site.search_url(searchtext)
    #     searchHTML = await get_html(url)
    #     targeturl, cardJson = self.GetCardHTMLWithJ(searchtext, url, searchHTML)
    #     if targeturl:
    #         cardHTML = await get_html(targeturl)
    #         return self.GetCardFromHTML(cardHTML, cardJson)
    #     return None

    _wiki_link = Site.wiki_url

    def _get_wiki_link(self, card: Card):
        """ 试着从 card 的卡名中得出 wiki 链接 """
        if TYPE_CHECKING:
            assert isinstance(card.names, CnJpEnNameUnit)
        if card.names.jp_name:
            pageword = f"《{self._to_wiki_str(card.names.jp_name)}》"
        elif card.names.en_name:
            pageword = f"《{card.names.en_name}》"
        else:
            return None
        pageword = parse.quote(pageword, encoding="euc-jp")
        return f"{self._wiki_link}index.php?cmd=read&page={pageword}"

    @staticmethod
    def _to_wiki_str(text: str):
        """ 半角转全角，以及一些特殊符号的转换 """
        transDict = {
            #' ':chr(12288), #半角空格直接转化
            "·": "・",
            "－": "−",
            "Ⅰ": "Ｉ",
            "Ⅱ": "ＩＩ",
            "Ⅲ": "ＩＩＩ",
            "Ⅳ": "ＩＶ",
            "Ⅴ": "Ｖ",
            "Ⅵ": "ＶＩ",
            "Ⅶ": "ＶＩＩ",
            "Ⅷ": "ＶＩＩＩ",
            "Ⅸ": "ＩＸ",
            "Ⅹ": "Ｘ",
            "Ⅺ": "ＸＩ",
            "Ⅻ": "ＸＩＩ",
        }
        r = ""
        for c in text:
            trans = transDict.get(c, None)
            if trans:
                c = trans
            else:
                oc = ord(c)
                if oc > 32 and oc <= 126:  # 半角字符（除空格）根据关系转化
                    c = chr(oc + 65248)
            r += c
        return r

    @staticmethod
    def _beautifyText(text: str):
        """ 试着给效果文本加换行，好看一点 """
        nums = set("①②③④⑤⑥⑦⑧⑨⑩●")
        transDict = {"・": "·"}
        r = ""
        length = len(text)
        for i, c in enumerate(text):
            trans = transDict.get(c, None)
            if trans:
                c = trans
            elif c in nums:
                if 1 < i < length - 1 and text[i - 1] != "\n" and text[i + 1] == "：":
                    c = "\n" + c
            r += c
        return r

    # ↑ 之前的老代码 ↑
    @staticmethod
    def _div_data(html: BeautifulSoup):
        div = html.find_all("div", {"class": "val"})
        # divr=[[y for y in x.stripped_strings] for x in div]
        return [
            [ y for y in x._all_strings(True, types=(NavigableString, CData, TemplateString)) ]
            for x in div
        ]

    @staticmethod
    def _is_RD(html: BeautifulSoup):
        return bool(html.find("div", {"class": "rd-mark"}))

    def _names_from_div(self, divr: list[list]):
        cn_name = divr[0][Translate.CN.value]
        nw_name = divr[0][Translate.NW.value]
        jp_name = divr[1][0]
        en_name = divr[2][0]
        if TYPE_CHECKING:
            assert isinstance(cn_name, str) and isinstance(nw_name, str) and isinstance(jp_name, str) and isinstance(en_name, str)
        jp_name = jp_name if jp_name != "-" else ""
        en_name = en_name if en_name != "-" else ""
        jp_name = jp_name.replace("・", "·")
        return cn_name, nw_name, jp_name, en_name

    def _card_url_json_gen(self, url: str, html: str):
        root = BeautifulSoup(html, "lxml")
        if TYPE_CHECKING:
            assert root.head
            assert root.body
        title = root.head.find("title")
        if TYPE_CHECKING:
            assert isinstance(title, Tag)
        if not (title and title.string and title.string.startswith("搜索")):  # 不是搜索结果页，直接是卡片详情页
            yield url, None                                                   # 或者是卡名以“搜索”开头的卡（
            return
        scripts: ResultSet[Tag] = root.body.find_all("script")
        script_text = ""
        # 试着拿到 json 所在的脚本
        if not any(script_text := s.string
                   for s in scripts 
                   if s.string and s.string.strip().startswith("window.__STORE__")):
            return
        card_jsons = script_text[script_text.find("{"):].strip()[:-1]  # 去掉 { 之前的部分和尾部分号
        card_data: dict[str, dict] = json.loads(card_jsons)
        if meta := card_data.get("meta"):   # {keyword, count, total_page, cur_page}  试着更新查询信息
            self.current_query.query = meta.get("keyword", self.current_query.query)  # 也更新 query
            self.current_query.total = meta.get("count", self.current_query.total)
            self.current_query.total_page = meta.get("total_page", self.current_query.total_page)
            self.current_query.current_page = meta.get("cur_page", self.current_query.current_page)
        for one in card_data["cards"]:
            if TYPE_CHECKING:
                assert isinstance(one, dict)
            target_url = str(one["href"]).replace("\\", "")
            yield target_url, one

    def _ids_from_json(self, card_json: dict | None) -> OurOcgIDCard | None:
        if card_json:
            id = int(card_json.get("password") or 0)
            cn_name = card_json.get("name") or ""
            nw_name = card_json.get("name_nw") or ""
            jp_name = card_json.get("name_ja") or ""
            en_name = card_json.get("name_en") or ""  # 名称可能为 None
            return OurOcgIDCard(id, cn_name, jp_name, en_name, nw_name)

    def _ids_from_html(self, card_html) -> OurOcgIDCard:
        html = BeautifulSoup(card_html, "lxml")
        is_RD = self._is_RD(html)
        divr = self._div_data(html)
        cn_name, nw_name, jp_name, en_name = self._names_from_div(divr)
        id = 0 if is_RD else int(divr[4][0])
        return OurOcgIDCard(id, cn_name, jp_name, en_name, nw_name)

    @cached_property
    def current_query(self):
        return OurOcgQueryInfo()

    if TYPE_CHECKING:
        @overload   # 用 overload 和字面量来区分返回值
        async def search_gen(self, query: str, ids_only: Literal[False] = False) -> AsyncGenerator[Card, None]:
            ...

        @overload
        async def search_gen(self, query: str, ids_only: Literal[True] = True) -> AsyncGenerator[OurOcgIDCard, None]:
            ...

    async def search_gen(self, query: str, ids_only = False):
        self.current_query = query_info = OurOcgQueryInfo(query)
        while query_info.current_page <= query_info.total_page:
            url = Site.search_url(query, query_info.current_page)  # 默认最初 current_page = 0
            html = await get_html(url, follow_redirects=True)      # OurOcg 有页面重定向
            for card_url, card_json in self._card_url_json_gen(url, html):
                if ids_only and (ids := self._ids_from_json(card_json)):
                    query_info.current += 1
                    yield ids
                    continue
                if card_url:
                    card_html = await get_html(card_url, follow_redirects=True)
                    query_info.current += 1
                    if ids_only:
                        yield self._ids_from_html(card_html)
                    else:
                        yield self._getCardFromHTML(card_html, card_json)
            query_info.current_page += 1

    async def from_id(self, card_id: int) -> Card | None:
        return await self.from_query(str(card_id))

    async def from_name(self, card_name: str) -> Card | None:
        result = None
        async for card in self.search_gen(card_name, ids_only=True):
            # print(card)
            # print(self.current_query)
            if result is None:
                result = card  # 第一张卡
            if card_name in (card.name, card.nw_name, card.jp_name, card.en_name):
                result = card
                break
            if self.name_search_limit and self.current_query.current >= self.name_search_limit:    
                # 超过比对上限而没找到卡名完全匹配的，返回第一张卡
                break
        if result:
            # 相当于第二次 search_gen，会覆盖 current_query
            return await self.from_query(str(result.id or result.name or result.jp_name or result.en_name))
    
    AsyncSearchByName = from_name  # 兼容

    async def gen_from_query(self, query: str) -> AsyncGenerator[Card, None]:
        async for card in self.search_gen(query):
            yield card

    async def gen_ids_from_query(self, query: str) -> AsyncGenerator[OurOcgIDCard, None]:
        async for card in self.search_gen(query, ids_only=True):
            yield card

if __name__ == "__main__":
    # text=input()
    # a=ourocg()
    # print(a.FindCardByName(text))

    async def main():
        text = input()
        a = OurOcg()
        print(await a.AsyncSearchByName(text))

    import asyncio

    asyncio.run(main())
