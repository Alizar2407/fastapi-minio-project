from icecream import ic
from typing import Annotated, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Response, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from jose import jwt, JWTError
from starlette import status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.models import UsersORM, Token
from app.data.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/frontend/templates")


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")


ALGORITHM = "HS256"
SECRET_KEY = "fastapi_minio_project"

bcrypt_context = CryptContext(schemes=["bcrypt"])
ouath2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(UsersORM).filter(UsersORM.username == username).first()

    if user is None:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False

    return user


def create_access_token(
    username: str,
    user_id: int,
    expires_delta: timedelta,
):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):

    try:
        token = request.cookies.get("access_token")

        if token is None:
            return None

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username: str | None = payload.get("sub")
        user_id: int | None = payload.get("id")

        ic(username, user_id)

        if username is None or user_id is None:
            logout(request)

        return {
            "username": username,
            "id": int(user_id),
        }

    except JWTError as e:
        return None
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail=f"Could not validate user: {e}",
        # )


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


@router.post("/", response_class=HTMLResponse)
async def login(db: Annotated[Session, Depends(get_db)], request: Request):
    try:

        form = LoginForm(request)
        await form.create_oauth_form()

        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(
            response=response,
            form_data=form,
            db=db,
        )

        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"msg": msg, "success_flag": False},
            )

        return response

    except Exception as e:
        msg = f"Unknown error: {e}"
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"msg": msg, "success_flag": False},
        )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )


@router.post("/register", response_class=HTMLResponse)
async def create_user(
    db: Annotated[Session, Depends(get_db)],
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
):
    username_exists = db.query(UsersORM).filter(UsersORM.username == username).first()
    email_exists = db.query(UsersORM).filter(UsersORM.email == email).first()

    if password != password2:
        msg = "Passwords do not match"
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"msg": msg},
        )

    if username_exists or email_exists:
        msg = "Username or email already exists"
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"msg": msg},
        )

    user_model = UsersORM(
        email=email,
        username=username,
        hashed_password=bcrypt_context.hash(password),
    )

    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"msg": msg, "success_flag": True},
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    msg = "Logout successful"
    response = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"msg": msg, "success_flag": True},
    )
    response.delete_cookie(key="access_token")
    return response


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    response: Response,
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        return False

    token = create_access_token(
        username=user.username,
        user_id=user.id,
        expires_delta=timedelta(minutes=20),
    )

    response.set_cookie(key="access_token", value=token, httponly=True)

    return True
