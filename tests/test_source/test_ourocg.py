
import pytest

from ygoutil.source import OurOCG

@pytest.mark.asyncio
async def test_baige():
    source = OurOCG()
    card = await source.AsyncSearchByName("解码语者")
    assert card
    assert card.name == "解码语者"
