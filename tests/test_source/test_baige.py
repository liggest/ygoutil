
import pytest

from ygoutil.source import BaiGe

@pytest.mark.asyncio
async def test_baige():
    source = BaiGe()
    card = await source.asyncSearch("解码语者")
    assert card
    assert card.name == "解码语者"
