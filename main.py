from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import Base, engine, get_db

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) # Idempotent : we can multiple times, won't have any side-effects if the tables already exist
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# first argument is the url path where the static files will be accessible
# the second one is an instance of Staticfiles pointing to the static directory
# name that is used to reference in templates
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


# ----------------------------------- HTML ENDPOINTS -----------------------------------

# Request represents the entire incoming HTTP request — everything the client (browser, API call, etc.) sent to your server.
# So it's basically your handle to the outside world.
# It is required by TemplateResponse to provide context to the HTML template
# (e.g., URL generation, accessing request data inside the template)


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})

@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id)) # not using eager loading (selectinload)
    # because in the template we don't access the posts through the user object (not using the relation), hence in order to 
    # understand when we need eager, depends on the relationship between tables and the query we are making, for instance in 
    # our it's the template
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )

# ----------------------------------- API ENDPOINTS -----------------------------------

# users endpoints

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already exists.",
        )
    
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already exists.",
        )
    
    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user  # Pydantic acts as a filter — it only serializes the fields defined in UserResponse, 
                     # regardless of how many fields the SQLAlchemy model has.

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if user:
        return user
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

# Note:
# user here is a SQLAlchemy object, not a dictionary. Setting
# model_config = ConfigDict(from_attributes=True) in schemas.UserResponse
# allows FastAPI and Pydantic to automatically serialize the ORM object into the JSON response.


## delete_user
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()


# users posts endpoints
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_update.username is not None and user_update.username != user.username:
        result = await db.execute(select(models.User).where(models.User.username == user_update.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
        
    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(select(models.User).where(models.User.email == user_update.email))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Note: the below is different from how its done for post patch endpoint, just a different way of implementation
    # if user_update.username is not None:
    #     user.username = user_update.username
    # if user_update.email is not None:
    #     user.email = user_update.email
    # if user_update.image_file is not None:
    #     user.image_file = user_update.image_file

    update_data = user_update.model_dump(exclude_unset=True)
    for field,value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

# posts endpoints

@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    await db.commit()
    # Reload the object from the database after commit to fetch any
    # database-generated values (e.g., auto-increment IDs, timestamps, defaults).
    await db.refresh(new_post, attribute_names=["author"])
    return new_post

@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts     # fastapi automatically converts the (list of dictionary)/python-object into a json array
                     # Also in pydantic the author relationship is automatically serialized as a UserResponse
                     # The connection for serialization is made in the pydantic schema of PostResponse

@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post_data.user_id != post.user_id:
        result = await db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@app.patch("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # if I were to use the below line just like in the put method above, the IDE would throw an error,
    # because there would be a type mismatch between the input request data and database model
    # the database model has a type hint of, lets say for post.title, mapped[str], but post_data.title coming
    # from PostUpdate has a type of str | None
    # post.title = post_data.title
    
    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
        
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    await db.delete(post)
    await db.commit()
    

# ----------------------------------- Exception Handlers -----------------------------------

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,   # if this not passed then the status code would be 200.
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )