from sqlalchemy.orm import Session
from app.models.bid import IgunsulBid


def get_bid_list(db: Session, fdate: str, tdate: str, 공고번호: str,
                 공고명: str, isopen: int, famt: int, tamt: int,
                 page: int, page_size: int):

    query = db.query(IgunsulBid).filter(IgunsulBid.is_cancel == 0)

    if fdate:
        query = query.filter(IgunsulBid.공고일 >= fdate)
    if tdate:
        query = query.filter(IgunsulBid.공고일 <= tdate)
    if 공고번호:
        query = query.filter(IgunsulBid.공고번호.like(f"%{공고번호}%"))
    if 공고명:
        query = query.filter(IgunsulBid.공고명.like(f"%{공고명}%"))
    if isopen == 0:
        query = query.filter(IgunsulBid.is_open == 0)
    elif isopen == 1:
        query = query.filter(IgunsulBid.is_open == 1)
    if famt:
        query = query.filter(IgunsulBid.기초금액 >= famt)
    if tamt:
        query = query.filter(IgunsulBid.기초금액 <= tamt)

    total = query.count()
    items = query.order_by(IgunsulBid.id.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size).all()

    return {
        "data": [
            {
                "id":           i.id,
                "bbscode":      i.bbscode,
                "공고번호":     i.공고번호,
                "공고차수":     i.공고차수,
                "공고명":       i.공고명,
                "수요기관":     i.수요기관,
                "지역":         i.지역,
                "기초금액":     i.기초금액,
                "투찰률":       float(i.투찰률) if i.투찰률 else None,
                "A값":          i.A값,
                "순공사원가":   i.순공사원가,
                "예가범위":     i.예가범위,
                "공고일":       i.공고일,
                "개찰일":       i.개찰일.isoformat() if i.개찰일 else None,
                "is_open":      i.is_open,
                "is_cancel":    i.is_cancel,
            }
            for i in items
        ],
        "total":       total,
        "page":        page,
        "total_pages": -(-total // page_size),
    }