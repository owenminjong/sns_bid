from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from app.database import Base

class SvrBatch(Base):
    __tablename__ = "svr_batch"

    ssn      = Column(Integer, primary_key=True, autoincrement=True)
    bkind    = Column(SmallInteger, default=0)   # 배치 종류 (0:공고수집, 1:개찰결과)
    sdate    = Column(DateTime)                  # 시작일시
    edate    = Column(DateTime)                  # 종료일시
    bdate    = Column(String(10))                # 작업 기준일자
    bcontent = Column(String(200))               # 결과 메시지