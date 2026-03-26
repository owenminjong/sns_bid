from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.types import Numeric
from app.database import Base

class BidPredict(Base):
    __tablename__ = "bid_predict"

    psn        = Column(BigInteger, primary_key=True, autoincrement=True)
    bsn        = Column(BigInteger, default=0)
    bidNtceNo  = Column(String(20))
    bidNtceNm  = Column(String(200))
    bssamt     = Column(BigInteger, default=0)
    Aamt       = Column(BigInteger, default=0)
    realAmt    = Column(BigInteger, default=0)
    urate      = Column(Numeric(10, 3), default=0)
    preamt     = Column(BigInteger, default=0)
    preRate    = Column(Numeric(10, 3), default=0)
    preRate2   = Column(Numeric(10, 4), default=0)
    confidence = Column(Numeric(5, 3), default=0)
    model_used = Column(String(20))
    betc       = Column(String(100))
    sfcode     = Column(Integer)
    regdate    = Column(DateTime)