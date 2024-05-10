
import pytest

from ygoutil.card import CardType
from ygoutil.source import OurOcg
from ygoutil.source.ourocg import CnJpEnNameUnit, RushDuelIDUnit, Translate, OurOcgIDCard

@pytest.fixture
def ourocg():
    return OurOcg()

@pytest.mark.asyncio
async def test_ourocg(ourocg: OurOcg):
    card = await ourocg.from_id(23512906)
    assert card
    assert isinstance(card.names, CnJpEnNameUnit)
    assert card.names.en_name == "Gold Pride - Leon"
    assert ourocg.current_query.current == 1

@pytest.mark.asyncio
async def test_ourocg_rd(ourocg: OurOcg):
    card = await ourocg.from_query("七道魔导士")
    assert card
    assert isinstance(card.ids, RushDuelIDUnit)
    assert card.id == "RUSH DUEL"
    assert ourocg.current_query.total_page > 1

@pytest.mark.asyncio
async def test_ourocg_from_name(ourocg: OurOcg):
    ourocg.name_search_limit = 0
    ourocg.set_translate_edition(Translate.CN.name)
    card = await ourocg.from_name("元素英雄 新宇侠")
    assert card
    assert card.name == "E·HERO 新生人"

@pytest.mark.asyncio
async def test_ourocg_multiple(ourocg: OurOcg):
    cards = await ourocg.list_from_query("宝札", limit=6)
    assert cards
    assert len(cards) == 6
    assert all(CardType.Spell in card.types for card in cards)
    assert ourocg.current_query.query == "宝札"
    assert ourocg.current_query.current == 6
    assert ourocg.current_query.total_page > 1

@pytest.mark.asyncio
async def test_ourocg_ids(ourocg: OurOcg):
    ids = await ourocg.list_ids_from_query("迪安·凯特", limit=20)
    assert ids
    assert len(ids) < 20
    assert all(isinstance(card, OurOcgIDCard) for card in ids)
    assert any(card.id == 0 for card in ids)  # RD
    
