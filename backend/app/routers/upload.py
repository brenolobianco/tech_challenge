import asyncio
import json
import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.middleware.rate_limit import upload_rate_limiter
from app.models import Upload, User
from app.schemas.upload import RowError, UploadResponse, UploadStatus
from app.services.campaign_service import generate_campaigns
from app.services.csv_validator import parse_csv
from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()


def run_campaign_generation(upload_id: str):
    db = SessionLocal()
    try:
        generate_campaigns(db, upload_id)
    finally:
        db.close()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a CSV file",
    description="Upload a CSV file with user data (id, name, age, city, income). "
    "The file is validated row-by-row and campaigns are generated in the background. "
    "Rate limited to 5 uploads per minute per IP.",
)
async def upload_csv(request: Request, file: UploadFile, db: Session = Depends(get_db)):
    await upload_rate_limiter(request)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail={
            "error": "invalid_file",
            "message": "File must be a .csv file",
            "details": None,
        })

    try:
        raw = await file.read()
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_encoding",
            "message": "File must be UTF-8 encoded",
            "details": None,
        })

    if not content.strip():
        raise HTTPException(status_code=422, detail={
            "error": "empty_file",
            "message": "CSV file is empty",
            "details": None,
        })

    try:
        valid_rows, errors, total = parse_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={
            "error": "malformed_csv",
            "message": str(e),
            "details": None,
        })

    upload = Upload(
        filename=file.filename,
        status="pending",
        total_rows=total,
        valid_rows=len(valid_rows),
        invalid_rows=total - len(valid_rows),
    )
    db.add(upload)
    db.flush()

    logger.info("Upload received: filename=%s total_rows=%d upload_id=%s", file.filename, total, upload.id)

    for row_data in valid_rows:
        user = User(upload_id=upload.id, **row_data)
        db.add(user)

    db.commit()

    logger.info("Background job started for upload_id=%s", upload.id)
    thread = threading.Thread(target=run_campaign_generation, args=(upload.id,))
    thread.start()

    return UploadResponse(
        upload_id=upload.id,
        status="processing",
        total_rows=total,
        valid_rows=len(valid_rows),
        invalid_rows=total - len(valid_rows),
        errors=[RowError(**e) for e in errors],
    )


@router.get(
    "/upload/{upload_id}/status",
    response_model=UploadStatus,
    summary="Get upload processing status",
    description="Returns the current processing status of an upload.",
)
def get_upload_status(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail={
            "error": "not_found",
            "message": f"Upload with id {upload_id} was not found",
            "details": None,
        })
    return UploadStatus(
        upload_id=upload.id,
        status=upload.status,
        total_rows=upload.total_rows,
        valid_rows=upload.valid_rows,
        invalid_rows=upload.invalid_rows,
        created_at=upload.created_at,
        processed_at=upload.processed_at,
    )


@router.get(
    "/upload/{upload_id}/stream",
    summary="SSE stream for upload status",
    description="Server-Sent Events stream that pushes real-time status updates "
    "for an upload. The stream closes automatically when processing completes or fails.",
)
async def stream_upload_status(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail={
            "error": "not_found",
            "message": f"Upload with id {upload_id} was not found",
            "details": None,
        })

    if upload.status in ("completed", "failed"):
        async def already_done():
            data = json.dumps({
                "status": upload.status,
                "upload_id": upload.id,
                "total_rows": upload.total_rows,
                "valid_rows": upload.valid_rows,
                "invalid_rows": upload.invalid_rows,
                "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
            })
            yield f"data: {data}\n\n"

        return StreamingResponse(already_done(), media_type="text/event-stream")

    queue = sse_manager.subscribe(upload_id)

    async def event_generator():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"

                    parsed = json.loads(message)
                    if parsed.get("status") in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            sse_manager.unsubscribe(upload_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
