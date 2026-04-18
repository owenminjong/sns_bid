from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, Date
from sqlalchemy.dialects.mysql import TINYINT
from app.database import Base
from datetime import datetime


class IgunsulBid(Base):
    __tablename__ = "igunsul_bid"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    bbscode       = Column(String(20), nullable=False, unique=True)

    공고번호      = Column("공고번호",      String(20),  nullable=False, default='')
    공고차수      = Column("공고차수",      String(3),   nullable=False, default='000')
    공고명        = Column("공고명",        String(200), nullable=False, default='')
    태그          = Column("태그",          String(200), nullable=False, default='')
    종목          = Column("종목",          String(100), nullable=False, default='')
    대업종        = Column("대업종",        String(50),  nullable=False, default='')
    수요기관      = Column("수요기관",      String(100), nullable=False, default='')
    지역          = Column("지역",          String(50),  nullable=False, default='')
    지역제한_상세 = Column("지역제한_상세", String(100), nullable=False, default='')
    계약방법      = Column("계약방법",      String(50),  nullable=False, default='')
    낙찰방법      = Column("낙찰방법",      String(200), nullable=False, default='')
    예가범위      = Column("예가범위",      String(10),  nullable=False, default='')

    기초금액      = Column("기초금액",  BigInteger,    nullable=True)
    추정가격      = Column("추정가격",  BigInteger,    nullable=True)
    투찰률        = Column("투찰률",    DECIMAL(6,3),  nullable=False, default=0)
    A값           = Column("A값",       BigInteger,    nullable=True)
    순공사원가    = Column("순공사원가", BigInteger,   nullable=True)

    공고일        = Column("공고일",      String(20), nullable=False, default='')
    등록마감일    = Column("등록마감일",  String(20), nullable=False, default='')
    투찰시작일    = Column("투찰시작일",  String(20), nullable=False, default='')
    투찰마감일    = Column("투찰마감일",  String(20), nullable=False, default='')
    개찰일        = Column("개찰일",      DateTime,   nullable=True)
    개찰일_원본   = Column("개찰일_원본", String(30), nullable=False, default='')

    is_open       = Column(TINYINT, nullable=False, default=0)
    is_cancel     = Column(TINYINT, nullable=False, default=0)
    담당자        = Column("담당자", String(100), nullable=False, default='')

    수집일자      = Column("수집일자", Date,     nullable=False)
    regdate       = Column(DateTime,  nullable=False, default=datetime.now)
    flag          = Column(TINYINT,   nullable=False, default=0)