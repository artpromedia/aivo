from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from ..database import get_db
from ..models import (
    KnowledgeBaseArticle,
    KBArticleCreate, KBArticleUpdate, KBArticleResponse
)

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

@router.get("/", response_model=List[KBArticleResponse])
async def get_kb_articles(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get knowledge base articles with filtering options"""

    query = select(KnowledgeBaseArticle)

    if category:
        query = query.where(KnowledgeBaseArticle.category == category)

    if is_public is not None:
        query = query.where(KnowledgeBaseArticle.is_public == is_public)

    if search:
        search_filter = or_(
            KnowledgeBaseArticle.title.contains(search),
            KnowledgeBaseArticle.content.contains(search),
            KnowledgeBaseArticle.tags.contains(search)
        )
        query = query.where(search_filter)

    query = query.offset(offset).limit(limit).order_by(
        KnowledgeBaseArticle.view_count.desc(),
        KnowledgeBaseArticle.updated_at.desc()
    )

    result = await db.execute(query)
    articles = result.scalars().all()

    return articles

@router.get("/{article_id}", response_model=KBArticleResponse)
async def get_kb_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific knowledge base article by ID"""

    result = await db.execute(
        select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    article.view_count += 1
    await db.commit()

    return article

@router.post("/", response_model=KBArticleResponse)
async def create_kb_article(article_data: KBArticleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new knowledge base article"""

    article = KnowledgeBaseArticle(
        title=article_data.title,
        content=article_data.content,
        category=article_data.category,
        tags=article_data.tags,
        url=article_data.url,
        is_public=article_data.is_public,
        created_by=article_data.created_by
    )

    db.add(article)
    await db.commit()
    await db.refresh(article)

    return article

@router.put("/{article_id}", response_model=KBArticleResponse)
async def update_kb_article(
    article_id: int,
    article_data: KBArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a knowledge base article"""

    result = await db.execute(
        select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Update fields
    if article_data.title is not None:
        article.title = article_data.title
    if article_data.content is not None:
        article.content = article_data.content
    if article_data.category is not None:
        article.category = article_data.category
    if article_data.tags is not None:
        article.tags = article_data.tags
    if article_data.url is not None:
        article.url = article_data.url
    if article_data.is_public is not None:
        article.is_public = article_data.is_public

    await db.commit()
    await db.refresh(article)

    return article

@router.delete("/{article_id}")
async def delete_kb_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a knowledge base article"""

    result = await db.execute(
        select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()

    return {"message": "Article deleted successfully"}

@router.get("/categories/list")
async def get_kb_categories(db: AsyncSession = Depends(get_db)):
    """Get all knowledge base categories"""

    result = await db.execute(
        select(KnowledgeBaseArticle.category, func.count())
        .group_by(KnowledgeBaseArticle.category)
        .order_by(KnowledgeBaseArticle.category)
    )
    categories = result.all()

    return [{"category": cat, "count": count} for cat, count in categories]

@router.get("/popular/articles", response_model=List[KBArticleResponse])
async def get_popular_articles(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get popular knowledge base articles by view count"""

    result = await db.execute(
        select(KnowledgeBaseArticle)
        .where(KnowledgeBaseArticle.is_public == True)
        .order_by(KnowledgeBaseArticle.view_count.desc())
        .limit(limit)
    )
    articles = result.scalars().all()

    return articles
