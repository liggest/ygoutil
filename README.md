# ygoutil

[![PyPI - Version](https://img.shields.io/pypi/v/ygoutil?style=flat&color=blue&link=https%3A%2F%2Fpypi.org%2Fproject%2Fygoutil%2F)](https://pypi.org/project/ygoutil/)

一个 ygo 工具集

## 安装

```bash
pip install ygoutil
```

## 使用

### 卡片源

通过 `ygoutil.source` 中的类来获取 `Card` 对象

- [x] 百鸽 API `BaiGe`
- [x] 百鸽网页  `BaiGePage`
- [x] OurOcg 网页 `OurOcg`
- [ ] 卡片数据库 `CDB`

一个简单的例子如下：

<details>
<summary>从百鸽获取卡片</summary>

```python
from ygoutil.source import BaiGe

source = BaiGe()
card = await source.from_query("解码语者")
cards = await source.list_from_query("解码语者")
print(source.current_query.total)

print(card)
print(card.id, card.name, card.types, card.text)
print(card.monster.attack, card.monster.link.marks)
```

其它卡片源接口近似，不同源获取到的卡片数据有细节上的区别

> 目前勉强能跑（
更多用法请参考测试逻辑或直接询问开发者

</details>

更多功能开发中，欢迎 [Issue](https://github.com/liggest/ygoutil/issues) 和 [PR](https://github.com/liggest/ygoutil/pulls)
