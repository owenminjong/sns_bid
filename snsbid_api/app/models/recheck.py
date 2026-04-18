from sqlalchemy import Column, BigInteger, String, Date, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from app.database import Base
from datetime import datetime


class IgunsulRecheck(Base):
    __tablename__ = "igunsul_recheck"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    nbbscode    = Column(String(20), nullable=False, default='')
    bbscode     = Column(String(20), nullable=False, default='')
    공고명      = Column("공고명",   String(200), nullable=False, default='')
    수집일자    = Column("수집일자", Date,        nullable=False)
    이슈내용    = Column("이슈내용", String(500), nullable=False, default='')
    확인여부    = Column(TINYINT,    nullable=False, default=0)
    확인메모    = Column("확인메모", String(500), nullable=False, default='')
    확인일시    = Column("확인일시", DateTime,    nullable=True)
    regdate     = Column(DateTime,  nullable=False, default=datetime.now)