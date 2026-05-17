# app/models/nara_nbid.py

# 실제로 사용하는 것만
from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, Integer, text
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from app.database import Base


class NaraNbid(Base):
    __tablename__ = "nara_nbid"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="시퀀스")
    bidNtceNo = Column(String(20), nullable=False, comment="입찰공고번호")
    bidNtceOrd = Column(String(3), nullable=False, default="000", comment="공고차수")
    bidNtceNm = Column(String(200), nullable=False, default="", comment="공고명")
    dminsttNm = Column(String(200), nullable=False, default="", comment="수요기관명")
    cnstrtsiteRgnNm = Column(
        String(100), nullable=True, comment="공사현장 지역명 (지역 피처)"
    )  # ← 추가
    opengDt = Column(DateTime, nullable=True, comment="개찰일시")
    bdgtAmt = Column(BigInteger, nullable=True, default=0, comment="추정가격")
    sucsfbidLwltRate = Column(Numeric(10, 3), nullable=True, comment="낙찰하한율")
    daeupcong = Column(String(50), nullable=True, comment="대업종 (mainCnsttyNm 원본)")

    # 기초금액/예가범위
    bssamt = Column(BigInteger, nullable=True, default=0, comment="기초금액")
    bssAmtPurcnstcst = Column(BigInteger, nullable=True, comment="순공사원가")
    rsrvtnPrceRngBgnRate = Column(
        String(5), nullable=True, comment="예가범위 시작률 (-2 또는 -3)"
    )
    rsrvtnPrceRngEndRate = Column(
        String(5), nullable=True, comment="예가범위 종료율 (+2 또는 +3)"
    )

    # 낙찰결과
    bidwinnrNm = Column(String(100), nullable=False, default="", comment="낙찰업체명")
    bidwinnrBizrno = Column(
        String(20), nullable=False, default="", comment="낙찰업체 사업자번호"
    )
    sucsfbidAmt = Column(BigInteger, nullable=True, comment="낙찰금액")
    sucsfbidRate = Column(Numeric(8, 3), nullable=True, comment="낙찰율 (AI 타겟)")
    prtcptCnum = Column(Integer, nullable=False, default=0, comment="참여업체수")
    progrsDivCdNm = Column(
        String(20), nullable=False, default="", comment="진행상태 (개찰완료/유찰 등)"
    )

    # 복수예가
    plnprc = Column(BigInteger, nullable=True, comment="예정가격")
    totRsrvtnPrceNum = Column(
        TINYINT(unsigned=True), nullable=True, comment="총예가수 (최대 15)"
    )
    rsrvtnPrce1 = Column(BigInteger, nullable=True, comment="예가1 금액")
    drwtNum1 = Column(SMALLINT, nullable=True, comment="예가1 추첨번호")
    rsrvtnPrce2 = Column(BigInteger, nullable=True, comment="예가2 금액")
    drwtNum2 = Column(SMALLINT, nullable=True, comment="예가2 추첨번호")
    rsrvtnPrce3 = Column(BigInteger, nullable=True, comment="예가3 금액")
    drwtNum3 = Column(SMALLINT, nullable=True, comment="예가3 추첨번호")
    rsrvtnPrce4 = Column(BigInteger, nullable=True, comment="예가4 금액")
    drwtNum4 = Column(SMALLINT, nullable=True, comment="예가4 추첨번호")
    rsrvtnPrce5 = Column(BigInteger, nullable=True, comment="예가5 금액")
    drwtNum5 = Column(SMALLINT, nullable=True, comment="예가5 추첨번호")
    rsrvtnPrce6 = Column(BigInteger, nullable=True, comment="예가6 금액")
    drwtNum6 = Column(SMALLINT, nullable=True, comment="예가6 추첨번호")
    rsrvtnPrce7 = Column(BigInteger, nullable=True, comment="예가7 금액")
    drwtNum7 = Column(SMALLINT, nullable=True, comment="예가7 추첨번호")
    rsrvtnPrce8 = Column(BigInteger, nullable=True, comment="예가8 금액")
    drwtNum8 = Column(SMALLINT, nullable=True, comment="예가8 추첨번호")
    rsrvtnPrce9 = Column(BigInteger, nullable=True, comment="예가9 금액")
    drwtNum9 = Column(SMALLINT, nullable=True, comment="예가9 추첨번호")
    rsrvtnPrce10 = Column(BigInteger, nullable=True, comment="예가10 금액")
    drwtNum10 = Column(SMALLINT, nullable=True, comment="예가10 추첨번호")
    rsrvtnPrce11 = Column(BigInteger, nullable=True, comment="예가11 금액")
    drwtNum11 = Column(SMALLINT, nullable=True, comment="예가11 추첨번호")
    rsrvtnPrce12 = Column(BigInteger, nullable=True, comment="예가12 금액")
    drwtNum12 = Column(SMALLINT, nullable=True, comment="예가12 추첨번호")
    rsrvtnPrce13 = Column(BigInteger, nullable=True, comment="예가13 금액")
    drwtNum13 = Column(SMALLINT, nullable=True, comment="예가13 추첨번호")
    rsrvtnPrce14 = Column(BigInteger, nullable=True, comment="예가14 금액")
    drwtNum14 = Column(SMALLINT, nullable=True, comment="예가14 추첨번호")
    rsrvtnPrce15 = Column(BigInteger, nullable=True, comment="예가15 금액")
    drwtNum15 = Column(SMALLINT, nullable=True, comment="예가15 추첨번호")
    # 상태 플래그
    is_collected = Column(
        TINYINT,
        nullable=False,
        default=0,
        comment="기초금액 수집여부 (0:미수집 1:완료)",
    )
    is_open = Column(
        TINYINT,
        nullable=False,
        default=0,
        comment="낙찰결과 수집여부 (0:미수집 1:완료)",
    )
    is_plnprc = Column(
        TINYINT,
        nullable=False,
        default=0,
        comment="복수예가 수집여부 (0:미수집 1:완료)",
    )
    regdate = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="등록일시",
    )

    def __repr__(self):
        return f"<NaraNbid {self.bidNtceNo}-{self.bidNtceOrd} {self.bidNtceNm[:20]}>"
