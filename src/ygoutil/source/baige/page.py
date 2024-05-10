# import json

from typing import TYPE_CHECKING, AsyncGenerator, Generator, Literal, overload
# from urllib import parse
import httpx
from bs4 import BeautifulSoup, Tag, ResultSet
# from bs4.element import PageElement, Tag
# try:
#     from bs4.element import TemplateString #新版bs4需要
# except:
#     TemplateString=NavigableString

from ygoutil.card import Card, CardAttribute, CardRace, LinkMark
from ygoutil.card.ids import CnJpEnIDCard
from ygoutil.card.unit import LinkUnit, PTextUnit  #, RankUnit
from ygoutil.source.base import CardSource, QueryInfo
from ygoutil.source.baige.misc import Site, BaiGeNameUnit, BaiGeURLUnit, BaiGeExtraUnit
from ygoutil.source.misc import get_html, deal_int


class BaiGePage(CardSource):
    """ 查百鸽网页 """

    @property
    def link(self):
        """ 网页链接 """
        return Site.base_url

    _link_mark = {
        "↙": LinkMark.BottomLeft,
        "↓": LinkMark.Bottom,
        "↘": LinkMark.BottomRight,
        "←": LinkMark.Left,
        "→": LinkMark.Right,
        "↖": LinkMark.TopLeft,
        "↑": LinkMark.Top,
        "↗": LinkMark.TopRight,
    }

    _link_name = {"数据库": "database", "db": "database", 
                "日文": "database_jp", "英文": "database_en", "简中": "database_cn",
                "q&a": "QA", "脚本": "script", "裁定": "ocg_rule"}

    @staticmethod
    def img_link(card_id: int | str):
        """ 卡图链接 """
        return Site.card_page_url(card_id)

    def _get_html(self, url, params=None):
        res = httpx.get(url, params=params, timeout=20)
        return res.text

    # async def asyncGetHTML(self, url):
    #     async with httpx.AsyncClient(timeout=20) as client:
    #         res = await client.get(url)
    #         return res.text

    def _html2Card(self, html, card_page=False) -> Generator[Card, None, None]:
        html = BeautifulSoup(html, "lxml")
        divs = self._html2divs(html, card_page)
        if not divs:
            return None
        # cards = []
        self.current_query.total = len(divs)
        for div in divs:
            div: Tag
            info = self._div_card_info(div)
            if card_page and len(info) == 2:  # 详情页少一个 div
                # info[2] = info[2].parent
                info.append(info[-1])
            types = None
            data = None
            desc = ""
            pdesc = ""
            state = "type"
            if TYPE_CHECKING:
                assert info[2].div
            for child in info[2].div.children:  # 效果文本
                if state == "type":
                    if isinstance(child, str):
                        child = child.strip()
                        if child:
                            types, *data = child.split()
                            types = types[1:-1].split("|")  # [魔法|永续]
                            state = "data"
                elif state == "data":
                    if isinstance(child, Tag):
                        if child.name == "hr":
                            state = "desc"
                    elif isinstance(child, str):
                        child = child.strip()
                        if child:
                            data = (data or []) + child.split()
                elif state == "desc":   # 描述文本
                    if isinstance(child, Tag):
                        if child.name == "br":
                            desc += "\n"
                        elif child.name == "hr" and types and "灵摆" in types:
                            pdesc = f"{desc.rstrip()}\n"    # 区分灵摆效果和怪兽效果
                            # desc += "\n{p}"
                            desc = ""
                        else:
                            child = child.text
                    if isinstance(child, str):
                        desc += child
            if not types:
                return None
            
            c = Card.from_types(*types)
            if TYPE_CHECKING:
                assert info[1].h2
            names = c._name_unit = BaiGeNameUnit(c)
            c._extra_unit = BaiGeExtraUnit(c)
            (c.id, c._extra_unit.c_id, names.cn_name, names.jp_name, names.en_name, names.jp_ruby) = self._div_id_names(info)
            # c.database,c.QA,c.wiki,c.yugipedia,c.ygorg,c.ourocg,c.script,c.ocgRule=[
            #     a.get("href") for a in info[1].find_all("a")]
            # links={ a.text.strip().lower() : a.get("href") for a in info[1].find_all("a")}
            c._url_unit = BaiGeURLUnit(c)
            for atag in info[1].find_all("a"):
                atag: Tag
                aname: str = atag.text.strip().lower()  # 链接对应的名称都变成小写了
                alink = atag.get("href")
                if TYPE_CHECKING:
                    assert isinstance(alink, str)
                if aname in self._link_name:
                    setattr(c._url_unit, self._link_name[aname], alink)
                elif hasattr(c._url_unit, aname):
                    setattr(c._url_unit, aname, alink)
                elif aname.startswith("详情"):
                    if alink.endswith("#faq"):  # /card/xxxx#faq
                        alink = alink[:-4]
                    c.urls.url = f"{self.link[:-1]}{alink}"  # https://ygocdb.com/card/xxxx

            # c.database=links.get("数据库")
            # c.QA=links.get("q&a")
            # c.wiki=links.get("wiki")
            # c.yugipedia=links.get("yugipedia")
            # # c.ygorg=links.get("ygorg") # 好像不再提供这个链接了
            # c.ourocg=links.get("ourocg")
            # c.script=links.get("脚本")
            # c.ocgRule=links.get("裁定")
            # print(links)
            if TYPE_CHECKING:
                assert info[0].img
            img = info[0].img.get("data-original")  # 卡图链接
            if TYPE_CHECKING:
                assert isinstance(img, str)
            c._url_unit.pic = img
            if isinstance(img, str) and img.endswith("!half"):
                c._url_unit.pic = img[:-5]
            if c.is_monster:
                if TYPE_CHECKING:
                    assert data
                race, attribute = data.pop(0).split("/")  # 恐龙/地
                race = CardRace.from_str(race)
                attribute = CardAttribute.from_str(attribute)
                if TYPE_CHECKING:
                    assert race
                    assert attribute
                c.monster.race = race
                c.monster.attribute = attribute
                lv = ""
                for char in data.pop(0):  # [★2] [☆4] [LINK-3]
                    if char.isdigit():
                        lv += char
                lv = deal_int(lv)
                if TYPE_CHECKING:
                    assert isinstance(lv, int)
                c.monster.level = lv
                attack, defence = data.pop(0).split("/")  # 1400/1200
                attack = deal_int(attack)
                defence = deal_int(defence)
                if TYPE_CHECKING:
                    assert isinstance(attack, int)
                    assert isinstance(defence, int)
                c.monster.attack = attack
                c.monster.defence = defence
                # if isinstance(c.monster.levels, RankUnit):
                #     c.monster.levels.rank = lv
                if isinstance(c.monster.levels, LinkUnit):
                    # c.monster.levels.link = lv
                    c.monster.defence = None
                    marks = data.pop(0).split("]")  # [↑][←][→][↙][↓][↘]
                    for m in marks:
                        m = m.strip("[")
                        if m:
                            c.monster.levels.marks |= self._link_mark[m]
                if c.monster._pmark_unit:
                    if data:
                        marks = data.pop(0).split("/")  # 4/4
                    else:
                        # 刻度是 0/0 时好像不会展示在网页上
                        marks = ("0", "0")
                    marks = tuple(deal_int(m) for m in marks)
                    if TYPE_CHECKING:
                        marks = int(marks[0]), int(marks[1])
                    c.monster._pmark_unit.mark = marks
                    # pdesc = f"←{marks[0]} 【灵摆】 {marks[1]}→" + pdesc
                    # if c.is_effect:
                    #     desc = desc.format(p="【怪兽效果】")
                    # else:
                    #     desc = desc.format(p="【怪兽描述】")
                    c._text_unit = PTextUnit(c)
                    c._text_unit.p_text = pdesc.strip()
            c._text_unit._text = desc.strip()
            # cards.append(c)
            yield c

            # return c  # 先只找一张卡

    def _search(self, text: str | int, by_id=False):
        text = str(text)
        url, params = self._request_url_params(text, by_id)
        html = self._get_html(url, params)
        self.current_query = QueryInfo(text)
        if card := next(self._html2Card(html, card_page=by_id), None):
            self.current_query.current += 1
        return card

    if TYPE_CHECKING:
        @overload
        async def async_search_gen(self, text: str | int, by_id=False, ids_only : Literal[False] = False) -> AsyncGenerator[Card, None]:
            ...

        @overload
        async def async_search_gen(self, text: str | int, by_id=False, ids_only : Literal[True] = True) -> AsyncGenerator[CnJpEnIDCard, None]:
            ...

    async def async_search_gen(self, text: str | int, by_id=False, ids_only=False):
        text = str(text)
        url, params = self._request_url_params(text, by_id)
        html = await get_html(url, params=params, timeout=20)
        self.current_query = QueryInfo(text)   # 在这里初始化 QueryInfo，这样能覆盖所有 CardSource 要求的方法
        gen = self._html2Card(html, card_page=by_id) if not ids_only else self._html2IDCard(html)
        for card in gen:
            self.current_query.current += 1
            yield card

    async def async_search(self, text: str | int, by_id=False):
        return await anext(self.async_search_gen(text, by_id), None)

    asyncSearch = async_search

    # ↑ 之前的老代码 ↑

    @staticmethod
    def _request_url_params(text: str, by_id=False):
        if by_id:
            url = Site.card_page_url(text)  # text是卡号
            params = None
        else:
            url = Site.base_url
            params = Site.query_params(text)
        return url, params

    @staticmethod
    def _html2divs(html: BeautifulSoup, card_page=False) -> ResultSet[Tag]:
        if card_page:
            return html.find_all("div", {"class": "row card detail"})
        else:
            return html.find_all("div", {"class": "row card result"})

    @staticmethod
    def _div_card_info(div: Tag) -> ResultSet[Tag]:
        return div.find_all("div", limit=3, recursive=False)

    @staticmethod
    def _div_id_names(info: ResultSet[Tag]):
        if TYPE_CHECKING:
            assert info[1].h2
        cn_name = info[1].h2.text  # 卡名
        jp_name = jp_ruby = en_name = ""
        extras: ResultSet[Tag] = info[1].find_all("h3")
        id_tags: ResultSet[Tag] = extras.pop().find_all("span")
        id = int(id_tags[0].text)  # 卡号
        c_id = int(id_tags[-1].text)  # 数据库编号
        # en jp 卡名
        if len(extras) < 2:  # 缺 jp 或 en
            if extras[-1].text.isascii():
                en_name = extras.pop().text
            else:
                jp_name = extras.pop().text
        else:
            en_name = extras.pop().text
            jp_name = extras.pop().text
        if info[1].h4:
            jp_ruby = info[1].h4.text
        return id, c_id, cn_name, jp_name, en_name, jp_ruby

    async def from_id(self, card_id: int):
        return await self.async_search(card_id, by_id=True)
    
    async def from_name(self, card_name: str):
        return await self.async_search(card_name)

    async def gen_from_query(self, query: str) -> AsyncGenerator[Card, None]:
        async for card in self.async_search_gen(query):
            yield card

    def _html2IDCard(self, html) -> Generator[CnJpEnIDCard, None, None]:
        html = BeautifulSoup(html, "lxml")
        divs = self._html2divs(html)
        if not divs:
            return None
        self.current_query.total = len(divs)
        for div in divs:
            info = self._div_card_info(div)
            id, c_id, cn_name, jp_name, en_name, jp_ruby = self._div_id_names(info)
            yield CnJpEnIDCard(id, cn_name, jp_name, en_name)

    async def gen_ids_from_query(self, query: str) -> AsyncGenerator[CnJpEnIDCard, None]:
        async for card in self.async_search_gen(query, ids_only=True):
            yield card

if __name__ == "__main__":

    async def main():
        text = input()
        a = BaiGePage()
        print(await a.async_search(text))

    import asyncio

    asyncio.run(main())
