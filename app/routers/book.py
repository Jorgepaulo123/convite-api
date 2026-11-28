from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BookStats
from app.schemas import BookStatsOut

router = APIRouter(prefix="/book", tags=["book"])


def _get_stats(db: Session) -> BookStats:
    stats = db.query(BookStats).filter(BookStats.id == 1).first()
    if stats is None:
        raise HTTPException(status_code=503, detail="Contadores do livro ainda não foram inicializados.")
    return stats


@router.post("/read", response_model=BookStatsOut)
def record_book_read(db: Session = Depends(get_db)) -> BookStatsOut:
    db.query(BookStats).filter(BookStats.id == 1).update(
        {BookStats.reads: BookStats.reads + 1},
        synchronize_session=False,
    )
    db.commit()
    stats = _get_stats(db)
    return BookStatsOut(reads=stats.reads, downloads=stats.downloads)


@router.post("/download", response_model=BookStatsOut)
def record_book_download(db: Session = Depends(get_db)) -> BookStatsOut:
    db.query(BookStats).filter(BookStats.id == 1).update(
        {BookStats.downloads: BookStats.downloads + 1},
        synchronize_session=False,
    )
    db.commit()
    stats = _get_stats(db)
    return BookStatsOut(reads=stats.reads, downloads=stats.downloads)


@router.get("/stats", response_model=BookStatsOut)
def get_book_stats(db: Session = Depends(get_db)) -> BookStatsOut:
    stats = _get_stats(db)
    return BookStatsOut(reads=stats.reads, downloads=stats.downloads)
