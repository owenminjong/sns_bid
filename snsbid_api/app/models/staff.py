from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from app.database import Base

class Staff(Base):
    __tablename__ = "staff"

    sfcode  = Column(Integer, primary_key=True, autoincrement=True)
    regdate = Column(DateTime)
    sfname  = Column(String(50))
    tel     = Column(String(50))
    sfid    = Column(String(20))    # 로그인 아이디
    sfpw    = Column(String(255))   # 비밀번호 해시
    issvr   = Column(SmallInteger, default=0)  # 서버권한 여부
    isuse   = Column(SmallInteger, default=0)  # 사용여부
    isdel   = Column(SmallInteger, default=0)  # 삭제여부
    ddate   = Column(DateTime)                 # 삭제일시