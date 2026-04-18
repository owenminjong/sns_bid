from sqlalchemy import Column, BigInteger, String, DECIMAL, DateTime, Date, Integer
from app.database import Base
from datetime import datetime


class IgunsulNbid(Base):
    __tablename__ = "igunsul_nbid"

    id              = Column(BigInteger, primary_key=True, autoincrement=True)
    nbbscode        = Column(String(20), nullable=False, unique=True)
    bbscode         = Column(String(20), nullable=True)

    공고번호        = Column("공고번호", String(20),  nullable=False, default='')
    공고차수        = Column("공고차수", String(3),   nullable=False, default='000')
    공고명          = Column("공고명",   String(200), nullable=False, default='')
    태그            = Column("태그",     String(200), nullable=False, default='')
    종목            = Column("종목",     String(100), nullable=False, default='')
    대업종          = Column("대업종",   String(50),  nullable=False, default='')
    수요기관        = Column("수요기관", String(100), nullable=False, default='')
    지역            = Column("지역",     String(50),  nullable=False, default='')

    기초금액        = Column("기초금액",   BigInteger,   nullable=True)
    추정가격        = Column("추정가격",   BigInteger,   nullable=True)
    투찰률          = Column("투찰률",     DECIMAL(6,3), nullable=True)
    A값             = Column("A값",        BigInteger,   nullable=True)
    순공사원가      = Column("순공사원가", BigInteger,   nullable=True)
    예정가격        = Column("예정가격",   BigInteger,   nullable=True)
    사정률          = Column("사정률",     DECIMAL(10,6),nullable=True)

    낙찰하한가        = Column("낙찰하한가",       BigInteger, nullable=True)
    낙찰하한가_순공사 = Column("낙찰하한가_순공사", BigInteger, nullable=True)
    낙찰하한가_실제   = Column("낙찰하한가_실제",   BigInteger, nullable=True)

    낙찰금액          = Column("낙찰금액",   BigInteger,    nullable=True)
    낙찰율            = Column("낙찰율",     DECIMAL(8,3),  nullable=True)
    낙찰업체          = Column("낙찰업체",   String(100),   nullable=False, default='')
    낙찰업체_추첨번호 = Column("낙찰업체_추첨번호", String(10), nullable=False, default='')
    가격점수          = Column("가격점수",   DECIMAL(6,3),  nullable=True)
    참여업체수        = Column("참여업체수", Integer,       nullable=False, default=0)

    선택복수예가    = Column("선택복수예가",    String(50),   nullable=False, default='')
    복수예가_평균율 = Column("복수예가_평균율", DECIMAL(8,5), nullable=True)

    예가1  = Column("예가1",  BigInteger, nullable=True)
    예가2  = Column("예가2",  BigInteger, nullable=True)
    예가3  = Column("예가3",  BigInteger, nullable=True)
    예가4  = Column("예가4",  BigInteger, nullable=True)
    예가5  = Column("예가5",  BigInteger, nullable=True)
    예가6  = Column("예가6",  BigInteger, nullable=True)
    예가7  = Column("예가7",  BigInteger, nullable=True)
    예가8  = Column("예가8",  BigInteger, nullable=True)
    예가9  = Column("예가9",  BigInteger, nullable=True)
    예가10 = Column("예가10", BigInteger, nullable=True)
    예가11 = Column("예가11", BigInteger, nullable=True)
    예가12 = Column("예가12", BigInteger, nullable=True)
    예가13 = Column("예가13", BigInteger, nullable=True)
    예가14 = Column("예가14", BigInteger, nullable=True)
    예가15 = Column("예가15", BigInteger, nullable=True)

    추첨1  = Column("추첨1",  Integer, nullable=True)
    추첨2  = Column("추첨2",  Integer, nullable=True)
    추첨3  = Column("추첨3",  Integer, nullable=True)
    추첨4  = Column("추첨4",  Integer, nullable=True)
    추첨5  = Column("추첨5",  Integer, nullable=True)
    추첨6  = Column("추첨6",  Integer, nullable=True)
    추첨7  = Column("추첨7",  Integer, nullable=True)
    추첨8  = Column("추첨8",  Integer, nullable=True)
    추첨9  = Column("추첨9",  Integer, nullable=True)
    추첨10 = Column("추첨10", Integer, nullable=True)
    추첨11 = Column("추첨11", Integer, nullable=True)
    추첨12 = Column("추첨12", Integer, nullable=True)
    추첨13 = Column("추첨13", Integer, nullable=True)
    추첨14 = Column("추첨14", Integer, nullable=True)
    추첨15 = Column("추첨15", Integer, nullable=True)

    개찰일   = Column("개찰일",  DateTime, nullable=True)
    수집일자 = Column("수집일자", Date,    nullable=False)
    regdate  = Column(DateTime, nullable=False, default=datetime.now)