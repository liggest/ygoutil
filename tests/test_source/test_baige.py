
import pytest

from ygoutil.card import CardType, LinkMark
from ygoutil.card.ids import CnJpEnIDCard
from ygoutil.source import BaiGe
from ygoutil.source.baige import BaiGePage, BaiGeNameUnit, BaiGeExtraUnit, BaiGeURLUnit

@pytest.fixture(scope="module")
def baige():
    return BaiGe()

@pytest.fixture(scope="module")
def baige_page():
    return BaiGePage()

@pytest.mark.asyncio
async def test_baige(baige: BaiGe):
    card = await baige.from_id(84536654)
    assert card
    assert isinstance(card.names, BaiGeNameUnit)
    assert card.name == "形态变化" and card.names.jp_name == "フォーム・チェンジ"
    assert card._url_unit
    assert card._url_unit.url
    assert card._url_unit.pic
    assert isinstance(card.extras, BaiGeExtraUnit)
    assert card.extras.c_id == 9068
    assert card.extras.faqs

@pytest.mark.asyncio
async def test_baige_multiple(baige: BaiGe):
    cards = await baige.list_from_query("被封印者的", limit=3)
    assert cards
    assert len(cards) == 3
    assert all("被封印者的" in card.name for card in cards)
    assert all(card.monster for card in cards)
    assert baige.current_query.query == "被封印者的"
    assert baige.current_query.current == 3

@pytest.mark.asyncio
async def test_baige_ids(baige: BaiGe):
    ids = await baige.list_ids_from_query("波塞冬", limit=10)
    assert ids
    assert len(ids) < 10
    assert all(isinstance(card, CnJpEnIDCard) for card in ids)

@pytest.mark.asyncio
async def test_baige_page(baige_page: BaiGePage):
    card = await baige_page.from_name("解码语者")
    assert card
    assert card.name == "解码语者"
    assert card.monster
    assert card.monster.defence is None
    assert card.monster.link.link == 3
    assert card.monster.link.marks == LinkMark.BottomLeft | LinkMark.BottomRight | LinkMark.Top
    assert isinstance(card.urls, BaiGeURLUnit)
    assert card.urls.database_cn
    assert card.urls.database_en
    assert card.urls.database_jp
    assert card.urls.QA
    assert card.urls.wiki
    assert card.urls.yugipedia
    assert card.urls.ourocg
    assert card.urls.script
    assert card.urls.ocg_rule

@pytest.mark.asyncio
async def test_baige_page_multiple(baige_page: BaiGePage):
    cards = await baige_page.list_from_query("竹光", limit=6)
    assert cards
    assert len(cards) == 6
    assert all(CardType.Spell in card.types for card in cards)
    assert baige_page.current_query.query == "竹光"
    assert baige_page.current_query.current == 6

@pytest.mark.asyncio
async def test_baige_page_ids(baige_page: BaiGePage):
    ids = await baige_page.list_ids_from_query("5回合后", limit=10)
    assert ids
    assert len(ids) < 10
    assert all(isinstance(card.id, int) for card in ids)
    assert any(86100785 == card.id for card in ids)  # 区域吞噬者
    assert any(isinstance(card, CnJpEnIDCard) and "異国の剣士" == card.jp_name for card in ids)  # 异国的剑士
