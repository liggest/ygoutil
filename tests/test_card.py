
from ygoutil.card.constant import CardType

def test_constant():
    assert CardType.Token
    assert list(CardType)
    assert CardType.Xyz | CardType.Pendulum
