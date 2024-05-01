from __future__ import annotations

from typing import AsyncGenerator, TypeVar, TYPE_CHECKING

from httpx import AsyncClient, USE_CLIENT_DEFAULT
if TYPE_CHECKING:
    from httpx._types import TimeoutTypes, QueryParamTypes
    from httpx._client import UseClientDefault

YieldT = TypeVar("YieldT")
SendT = TypeVar("SendT")

async def gen_limit(gen: AsyncGenerator[YieldT, SendT], limit: int) -> AsyncGenerator[YieldT, SendT]:
    """ 限制生成器的长度 """
    count = 0
    if count >= limit:
        return
    async for item in gen:
        yield item
        count += 1
        if count >= limit:
            break

async def get_json(url: str, params: QueryParamTypes = None, timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT, *args, **kw):
    async with AsyncClient() as client:
        response = await client.get(url, params=params, timeout=timeout, *args, **kw)
        return response.json()
    
async def get_html(url: str, params: QueryParamTypes = None, timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT, *args, **kw):
    async with AsyncClient() as client:
        response = await client.get(url, params=params, timeout=timeout, *args, **kw)
        return response.text

def deal_int(text: str):
    return int(text) if text.isdigit() else text

def deal_web_text(text: str):
    return text.replace("\r\n", '\n').strip()
