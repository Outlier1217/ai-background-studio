
import uuid
from pathlib import Path

import cv2
from PIL import Image
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.video_processor import video_processor
from services.database import (
    save_asset,
    get_asset,
    create_project,
    update_project,
    get_project,
    list_projects,
)

router = APIRouter(prefix="/api", tags=["Video Processing"])

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"

UPLOAD_DIR = STORAGE_DIR / "uploads"
BACKGROUND_DIR = STORAGE_DIR / "backgrounds"
PROCESSED_DIR = STORAGE_DIR / "processed"

for directory in [UPLOAD_DIR, BACKGROUND_DIR, PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 500 * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class ProcessRequest(BaseModel):
    video_id: str
    background_id: str


async def save_upload(upload: UploadFile, destination: Path):
    size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await upload.read(1024 * 1024)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds the 500 MB upload limit",
                    )

                output.write(chunk)

    except Exception:
        destination.unlink(missing_ok=True)
        raise

    finally:
        await upload.close()

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")


@router.post("/videos/upload")
async def upload_video(file: UploadFile = File(...)):
    filename = file.filename or "video"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video format")

    video_id = str(uuid.uuid4())
    destination = UPLOAD_DIR / f"{video_id}{extension}"

    await save_upload(file, destination)

    cap = cv2.VideoCapture(str(destination))

    try:
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Invalid video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0 or frame_count <= 0:
            raise HTTPException(status_code=400, detail="Invalid video metadata")

        duration = frame_count / fps

        if duration > 360:
            raise HTTPException(
                status_code=400,
                detail="Video cannot exceed 6 minutes",
            )

    except Exception:
        destination.unlink(missing_ok=True)
        raise

    finally:
        cap.release()

    save_asset(video_id, "video", filename, destination)

    return {
        "success": True,
        "video_id": video_id,
        "filename": filename,
        "width": width,
        "height": height,
        "fps": fps,
        "duration": round(duration, 2),
        "size_bytes": destination.stat().st_size,
    }


@router.post("/backgrounds/upload")
async def upload_background(file: UploadFile = File(...)):
    filename = file.filename or "background"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    background_id = str(uuid.uuid4())
    destination = BACKGROUND_DIR / f"{background_id}{extension}"

    await save_upload(file, destination)

    try:
        with Image.open(destination) as image:
            image.verify()

    except Exception:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    save_asset(background_id, "background", filename, destination)

    return {
        "success": True,
        "background_id": background_id,
        "filename": filename,
    }


def run_processing_job(job_id: str, video_path: Path, background_path: Path):
    output_path = PROCESSED_DIR / f"{job_id}.mp4"

    def update_progress(progress, processed, total):
        update_project(
            job_id,
            progress=progress,
            processed_frames=processed,
            total_frames=total,
        )

    update_project(job_id, status="processing")

    try:
        result = video_processor.process_video(
            input_path=video_path,
            background_path=background_path,
            output_path=output_path,
            progress_callback=update_progress,
        )

        update_project(
            job_id,
            status="completed",
            progress=100,
            processed_frames=result["processed_frames"],
            total_frames=result["total_frames"],
            output_path=str(output_path),
            error=None,
        )

    except Exception as error:
        output_path.unlink(missing_ok=True)

        update_project(
            job_id,
            status="failed",
            error=str(error),
        )

        print(f"Processing job {job_id} failed: {error}")


@router.post("/process")
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
):
    video = get_asset(request.video_id)
    background = get_asset(request.background_id)

    if not video or video["type"] != "video":
        raise HTTPException(status_code=404, detail="Video not found")

    if not background or background["type"] != "background":
        raise HTTPException(status_code=404, detail="Background image not found")

    video_path = Path(video["path"])
    background_path = Path(background["path"])

    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded video file not found")

    if not background_path.is_file():
        raise HTTPException(status_code=404, detail="Background image file not found")

    job_id = str(uuid.uuid4())
    output_path = PROCESSED_DIR / f"{job_id}.mp4"

    create_project({
        "id": job_id,
        "video_id": request.video_id,
        "background_id": request.background_id,
        "video_filename": video["filename"],
        "background_filename": background["filename"],
        "output_path": str(output_path),
    })

    background_tasks.add_task(
        run_processing_job,
        job_id,
        video_path,
        background_path,
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
    }


def format_project(project):
    project["download_url"] = (
        f"/api/download/{project['id']}"
        if project["status"] == "completed"
        else None
    )
    return project


@router.get("/projects")
async def get_projects():
    return {
        "success": True,
        "projects": [format_project(project) for project in list_projects()],
    }


@router.get("/process/{job_id}")
async def get_processing_status(job_id: str):
    project = get_project(job_id)

    if not project:
        raise HTTPException(status_code=404, detail="Job not found")

    return format_project(project)


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    project = get_project(job_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["status"] != "completed":
        raise HTTPException(status_code=409, detail="Video is not ready yet")

    output_path = Path(project["output_path"])

    if not output_path.is_file():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename="background-studio-output.mp4",
    )
