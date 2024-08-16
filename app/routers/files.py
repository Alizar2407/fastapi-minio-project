import datetime
from icecream import ic
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import (
    APIRouter,
    Query,
    Request,
    Depends,
    Path,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from minio import Minio
from minio.error import S3Error

from .auth import get_current_user
from app.data.dependencies import get_s3_client, get_db
from app.models.models import FilesORM


FILES_BUCKET_NAME = "files-bucket"

router = APIRouter(prefix="/files", tags=["files"])
templates = Jinja2Templates(directory="app/frontend/templates")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict | None, Depends(get_current_user)]
s3_client_dependency = Annotated[Minio, Depends(get_s3_client)]


@router.get("/", response_class=HTMLResponse)
async def list_files(
    request: Request,
    db: db_dependency,
    user: user_dependency,
):
    if user is None:
        return RedirectResponse(
            url="/auth",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        files = db.query(FilesORM).filter_by(user_id=user.get("id")).all()
        files.sort(key=lambda file: file.id)

        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={"files": files, "user": user},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/download/{file_id}")
async def download_file(
    request: Request,
    db: db_dependency,
    user: user_dependency,
    s3_client: s3_client_dependency,
    file_id: int = Path(gt=0),
):
    if user is None:
        return RedirectResponse(
            url="/auth",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        file = (
            db.query(FilesORM)
            .filter(FilesORM.id == file_id)
            .filter(FilesORM.user_id == user.get("id"))
            .first()
        )

        if file is None:
            raise HTTPException(
                status_code=404,
                detail="File not found",
            )

        download_link = s3_client.presigned_get_object(
            FILES_BUCKET_NAME,
            file.file_name,
            expires=datetime.timedelta(days=1),
        )

        return RedirectResponse(download_link)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/upload/", response_class=HTMLResponse)
async def get_upload_link(
    request: Request,
    db: db_dependency,
    user: user_dependency,
    s3_client: s3_client_dependency,
    filename: str = Query(),
):
    if user is None:
        return RedirectResponse(
            url="/auth",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        file = FilesORM(
            file_name=filename,
            user_id=user.get("id"),
            upload_date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        db.add(file)
        db.commit()
        db.refresh(file)

        new_file_name = f"{user.get('username')}-{file.id}-{filename}"
        file.file_name = new_file_name
        db.add(file)
        db.commit()

        upload_link = s3_client.presigned_put_object(
            FILES_BUCKET_NAME,
            new_file_name,
            expires=datetime.timedelta(days=1),
        )
        ic(upload_link)

        return templates.TemplateResponse(
            request=request,
            name="generated_link.html",
            context={"user": user, "upload_link": upload_link},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/delete/{file_id}", response_class=HTMLResponse)
async def delete_file(
    request: Request,
    db: db_dependency,
    user: user_dependency,
    s3_client: s3_client_dependency,
    file_id: int = Path(gt=0),
):
    if user is None:
        return RedirectResponse(
            url="/auth",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        file = (
            db.query(FilesORM)
            .filter(FilesORM.id == file_id)
            .filter(FilesORM.user_id == user.get("id"))
            .first()
        )

        if file is not None:

            try:
                s3_client.remove_object(FILES_BUCKET_NAME, file.file_name)
                ic(f"file {file.file_name} removed")

            except S3Error as e:
                ic(f"Error deleting file from MinIO: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error deleting file from MinIO: {e}",
                )

            except Exception as e:
                ic(f"Error deleting file from MinIO: {e}")

            db.delete(file)
            db.commit()

        return RedirectResponse(
            url="/",
            status_code=status.HTTP_302_FOUND,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )
