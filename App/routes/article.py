from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from App.database.db import get_db
from App.models.article import Article
from App.models.user import User
from App.routes.auth import get_current_user, require_role
from App.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["Newsroom"])

PUBLISHER_ROLES = ["sug_officer", "journalist", "admin"]


@router.post("", response_model=ArticleResponse)
def create_article(request: ArticleCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(PUBLISHER_ROLES))):
    article = Article(
        author_id=current_user.id, institution=current_user.institution,
        title=request.title, category=request.category, lead=request.lead,
        body=request.body, image_url=request.image_url, status=request.status
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("", response_model=list[ArticleResponse])
def list_articles(category: str = None, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    query = db.query(Article).filter(
        Article.institution == current_user.institution, Article.status == "published"
    )
    if category:
        query = query.filter(Article.category == category)
    return query.order_by(Article.created_at.desc()).all()


@router.get("/mine", response_model=list[ArticleResponse])
def my_articles(db: Session = Depends(get_db),
                 current_user: User = Depends(require_role(PUBLISHER_ROLES))):
    return db.query(Article).filter(Article.author_id == current_user.id).order_by(
        Article.created_at.desc()).all()


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    article = db.query(Article).filter(
        Article.id == article_id, Article.institution == current_user.institution
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, request: ArticleUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(PUBLISHER_ROLES))):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your article")
    for field, value in request.dict(exclude_unset=True).items():
        setattr(article, field, value)
    article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(PUBLISHER_ROLES))):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your article")
    db.delete(article)
    db.commit()
    return {"message": "Article deleted"}
