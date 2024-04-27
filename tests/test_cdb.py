
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from ygoutil.dataloader import CDBReader, ConfReader

class Links:
    cdb = r"https://cdn01.moecube.com/koishipro/ygopro-database/zh-CN/cards.cdb"
    strings = r"https://cdn01.moecube.com/koishipro/ygopro-database/zh-CN/strings.conf"
    lflist = r"https://cdn01.moecube.com/koishipro/ygopro-database/zh-CN/lflist.conf"

async def download(url: str, file: Path):
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            print(f"Downloading to {file.as_posix()}...({url})")
            with file.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    return file

@pytest_asyncio.fixture(scope="module")
async def cdb_file(tmp_path: Path):
    return await download(Links.cdb, tmp_path / "cards.cdb")

@pytest_asyncio.fixture(scope="module")
async def strings_file(tmp_path: Path):
    return await download(Links.strings, tmp_path / "strings.conf")

@pytest_asyncio.fixture(scope="module")
async def lflist_file(tmp_path: Path):
    return await download(Links.lflist, tmp_path / "lflist.conf")

@pytest.fixture
def conf_reader(strings_file, lflist_file):
    reader = ConfReader()
    reader.loadLFlist(lflist_file)
    reader.loadSets(strings_file)
    return reader

@pytest.fixture
def cdb_reader(cdb_file):
    with CDBReader(cdb_file) as reader:
        yield reader
    
def test_cdb(cdb_reader: CDBReader):
    assert cdb_reader.getCardByID(10000)  # 万物创世龙
    assert cdb_reader.getCardByID(9999) is None
    assert cdb_reader.getIDsByName("解码语者")

def test_conf(conf_reader: ConfReader):
    assert conf_reader.lfname
    assert conf_reader.lfdict
    assert conf_reader.setdict
