from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate

router = APIRouter()


@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts


@router.get("/{id}", response_model=PostResponse)
async def get_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
        author=user,
    )
    db.add(new_post)
    await db.commit()
    return new_post


@router.put("/{id}", response_model=PostResponse)
async def update_post(id: int, db: Annotated[AsyncSession, Depends(get_db)], update_request: PostCreate):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    if post.user_id != update_request.user_id:
        result = await db.execute(select(models.User).where(models.User.id == update_request.user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

        post.author = user

    post.title = update_request.title
    post.content = update_request.content
    post.user_id = update_request.user_id
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@router.patch("/{id}", response_model=PostResponse)
async def update_post_partial(id: int, db: Annotated[AsyncSession, Depends(get_db)], update_request: PostUpdate):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    update_data = update_request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    await db.delete(post)
    await db.commit()
