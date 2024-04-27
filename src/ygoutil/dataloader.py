# import functools
import sqlite3

from enum import Enum
from typing import Iterable, TYPE_CHECKING
from typing_extensions import Self
from pathlib import Path

from ygoutil.sqlbuilder import SQLBuilder


class ShrinkLevel(str, Enum):
    # TODO flag
    S0 = ""
    S1 = "type & 0x4000=0"
    S2 = "alias=0"
    S3 = "type & 0x48060C0=0"
    S4 = "type & 0x4802040!=0"

    No = S0
    NoToken = S1
    NoAlias = S2
    NoExtra = S3
    NoMain = S4

    @classmethod
    def fromInt(cls, i: int | Self | Iterable[int]) -> Self | str:
        if isinstance(i, cls):
            return i
        if TYPE_CHECKING:
            assert not isinstance(i, ShrinkLevel)
        if isinstance(i, Iterable):
            return " AND ".join([cls.fromInt(x) for x in i if x])  # x!=0 and x!=S0
        return getattr(cls, f"S{i}")

    # @property
    # def WHERE(self):
    #     if self:
    #         return f"WHERE {self}"
    #     return self


def WHERE(s: str):
    if s:
        return f"WHERE {s}"
    return s


class CDBReader:
    def __init__(self, path=None):
        self.cdbpath = path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        # print("连上啦")
        return self

    def __exit__(self, etype, eval, traceback):
        # print("关掉啦")
        self.close()

    def connect(self, path=None):
        if path:
            self.conn = sqlite3.connect(path)
        elif self.cdbpath:
            self.conn = sqlite3.connect(self.cdbpath)
        else:
            raise Exception("no cdb path")
        if self.conn:
            self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
        else:
            raise Exception("no cdb connection")

    @staticmethod
    def listOfSQL(num: int):  # lens=3 -> (?,?,?)
        return "(" + ",".join(["?"] * num) + ")"

    @staticmethod
    def unique(lst):  # [111,111,222] -> [111,222]
        return list(set(lst))

    def getCardByID(self, id: int):  # id是整数
        assert self.cursor
        self.cursor.execute(
            "SELECT t.name,t.DESC,d.* FROM texts t INNER JOIN datas d ON t.id=d.id WHERE t.id=?",
            (id,),
        )
        # return self.cursor.fetchall()[0]
        return self.cursor.fetchone()

    def getCardsByIDs(self, *ids):  # ids是元祖、列表之类的
        assert self.cursor
        sql = f"SELECT t.name,t.DESC,d.* FROM texts t INNER JOIN datas d ON t.id=d.id WHERE t.id IN {CDBReader.listOfSQL(len(ids))}"
        # print(sql)
        # print(ids)
        self.cursor.execute(sql, tuple(ids))
        return self.cursor.fetchall()

    def getIDsByName(self, name):  # name是字符串 完全匹配
        assert self.cursor
        self.cursor.execute("SELECT id FROM texts WHERE name=?", (name,))
        ids = self.cursor.fetchall()
        return [x[0] for x in ids]

    def getCardsByName(self, name):
        ids = self.getIDsByName(name)
        if ids:
            return self.getCardsByIDs(*ids)

    def getCardCount(self, shrink=0):  # full 0 全部 1 无衍生物 2 无同名卡无衍生物
        assert self.cursor
        level = ShrinkLevel.fromInt(shrink)
        self.cursor.execute(f"SELECT COUNT(*) FROM datas {WHERE(level)}")
        return self.cursor.fetchall()[0]

    def getRandomIDs(self, count=1, shrink=0):
        assert self.cursor
        level = ShrinkLevel.fromInt(shrink)
        self.cursor.execute(
            f"SELECT id FROM datas {WHERE(level)} ORDER BY RANDOM() limit ?", (count,)
        )
        ids = self.cursor.fetchall()
        return [x[0] for x in ids]

    def getRandomNames(self, count=1, shrink=0):
        assert self.cursor
        ids = self.getRandomIDs(count, shrink)
        self.cursor.execute(
            f"SELECT name FROM texts WHERE id IN {CDBReader.listOfSQL(len(ids))}",
            tuple(ids),
        )
        names = self.cursor.fetchall()
        return [x[0] for x in names]

    def getIDsByInput(self, ipt, expect=()):
        pass

    def getCardsByInput(self, ipt):
        pass

    def getCardsByBuilder(self, builder: SQLBuilder, num=50):
        assert self.cursor
        tail = f"ORDER BY d.level & 15 DESC,d.type LIMIT {num}"  # 15=>0b1111
        sql = builder.resolve()
        sql = f"{sql} {tail}"
        # print(sql)
        # print(builder.params)
        if builder.params:
            self.cursor.execute(sql, tuple(builder.params))
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchall()

    def getYDCards(self):
        assert self.cursor
        self.cursor.execute(
            "SELECT id FROM datas WHERE type & 0x48060C0=0 ORDER BY RANDOM() limit 60"
        )
        main = self.cursor.fetchall()
        main = [x[0] for x in main]
        self.cursor.execute(
            "SELECT id FROM datas WHERE type & 0x4802040!=0 ORDER BY RANDOM() limit 30"
        )
        extra = self.cursor.fetchall()
        extra = [x[0] for x in extra]
        return [main, extra]

class ConfReader:
    def __init__(self, path: str | Path = None):
        self.filepath = Path(path) if path else path

    def loadLFlist(self, path: str | Path = None):
        if path:
            self.filepath = Path(path)
        if TYPE_CHECKING:
            assert isinstance(self.filepath, Path)
        self.lfdict = {}
        start = False
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if start:
                    if line.startswith("!"):
                        break
                    if line[:1].isdigit():
                        temp = line.split()
                        self.lfdict[int(temp[0])] = int(temp[1])
                else:
                    if line.startswith("!"):
                        self.lfname = line[1:]
                        start = True

    def loadSets(self, path: str | Path = None):
        if path:
            self.filepath = Path(path)
        if TYPE_CHECKING:
            assert isinstance(self.filepath, Path)
        self.setdict = {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("!setname"):
                    temp = line.split()
                    self.setdict[int(temp[1], base=16)] = temp[2].split("\t")[0]


if __name__ == "__main__":
    conf = ConfReader()
    conf.loadLFlist("./ygo/lflist.conf")
    conf.loadSets("./ygo/strings.conf")
    # print(conf.lfname)
    # print(conf.lfdict)
    # print(conf.setdict)
    cdb = CDBReader()
    cdb.connect("./ygo/cards.cdb")
    ipt = ""
    # result=cdb.getCardsByIDs([1861629, 1861630])
    # print(result)
    """
    while ipt!="exit":
        ipt=input()
        print( cdb.getIDsByName(ipt) )
        #try:
        #    
        #except:
        #    print("不好使")
    """
    ct = cdb.getCardByID(9999)
    print(ct)
    # ids=cdb.getRandomIDs()
    # cts=cdb.getCardsByIDs(*ids)
    # c=Card()
    # c.fromCDBTuple(cts[0],conf.setdict,conf.lfdict)
    # print( c )
    cdb.close()
