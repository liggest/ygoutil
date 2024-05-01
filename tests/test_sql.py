
import pytest

from ygoutil.sqlbuilder import SQLBuilder
from ygoutil.card.constant import CardType

@pytest.fixture
def builder():
    return SQLBuilder()

def test_sql_builder(builder: SQLBuilder):
    # assert not builder.params
    assert builder.name("混沌", "光", "战士族", "600", "5000").race("机械").cardType(CardType.Monster, CardType.Link,"魔法卡").attribute("炎属性").resolve()
    assert builder.sql

def test_sql_builder2(builder: SQLBuilder):
    # assert not builder.params
    assert builder.attack(3000,"6900","99999").defence("19.3","?","3000").id("40","10000",5000).level("0星","10星","L6",13).resolve()

def test_sql_builder3(builder: SQLBuilder):
    # assert not builder.params
    assert builder.name("异色眼","攻守和0").resolve()

def test_sql_builder4(builder: SQLBuilder):
    # assert not builder.params
    assert builder.name("魂", "炎").race("水").race().resolve()

def test_sql_builder5(builder: SQLBuilder):
    # assert not builder.params
    assert builder.cardType("永续陷阱").resolve()


