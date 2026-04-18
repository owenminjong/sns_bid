from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.deps import get_current_staff
from app.models.batch import IgunsulBatch

router = APIRouter()


@router.get("/logs")
def batch_logs(
        limit: int = Query(default=20),
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_staff)
):
    logs = db.query(IgunsulBatch).order_by(IgunsulBatch.id.desc()).limit(limit).all()
    return {"status": "success", "data": [
        {
            "id":          l.id,
            "batch_type":  l.batch_type,
            "status":      l.status,
            "started_at":  str(l.started_at) if l.started_at else None,
            "ended_at":    str(l.ended_at)   if l.ended_at   else None,
            "total_cnt":   l.total_cnt,
            "ok_cnt":      l.ok_cnt,
            "recheck_cnt": l.recheck_cnt,
            "skip_cnt":    l.skip_cnt,
            "error_cnt":   l.error_cnt,
            "message":     l.message,
        } for l in logs
    ]}