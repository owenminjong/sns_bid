from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from sqlalchemy.dialects.mysql import TINYINT
from app.database import Base
from datetime import datetime


class IgunsulBatch(Base):
    __tablename__ = "igunsul_batch"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_type  = Column(String(20), nullable=False)       # 'bid' | 'nbid'
    status      = Column(TINYINT,    nullable=False, default=0)  # 0:실행중 1:완료 2:오류
    started_at  = Column(DateTime,   nullable=False, default=datetime.now)
    ended_at    = Column(DateTime,   nullable=True)
    total_cnt   = Column(Integer,    nullable=False, default=0)
    ok_cnt      = Column(Integer,    nullable=False, default=0)
    recheck_cnt = Column(Integer,    nullable=False, default=0)
    skip_cnt    = Column(Integer,    nullable=False, default=0)
    error_cnt   = Column(Integer,    nullable=False, default=0)
    message     = Column(String(500), nullable=False, default='')