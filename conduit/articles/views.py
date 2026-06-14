# coding: utf-8
"""Article CRUD routes.

This module keeps only the four core article endpoints (list, create,
update, delete, get-by-slug, and the authenticated feed).  Favorites,
comments, and tags live in their own sibling modules and are pulled in
via the imports at the bottom of this file so that a single
``import conduit.articles.views`` registers every route on the shared
blueprint.
"""

import datetime as dt

from flask_apispec import marshal_with, use_kwargs
from flask_jwt_extended import current_user, jwt_required, jwt_optional
from marshmallow import fields

from conduit.user.models import User
from .blueprints import blueprint
from .models import Article, Tags
from .serializers import article_schema, articles_schema
from .utils import get_article_or_404, get_or_create_tag


##########
# Articles
##########

@blueprint.route('/api/articles', methods=('GET',))
@jwt_optional
@use_kwargs({'tag': fields.Str(), 'author': fields.Str(),
             'favorited': fields.Str(), 'limit': fields.Int(), 'offset': fields.Int()})
@marshal_with(articles_schema)
def get_articles(tag=None, author=None, favorited=None, limit=20, offset=0):
    res = Article.query
    if tag:
        res = res.filter(Article.tagList.any(Tags.tagname == tag))
    if author:
        res = res.join(Article.author).join(User).filter(User.username == author)
    if favorited:
        res = res.join(Article.favoriters).filter(User.username == favorited)
    return res.offset(offset).limit(limit).all()


@blueprint.route('/api/articles', methods=('POST',))
@jwt_required
@use_kwargs(article_schema)
@marshal_with(article_schema)
def make_article(body, title, description, tagList=None):
    article = Article(title=title, description=description, body=body,
                      author=current_user.profile)
    if tagList is not None:
        for tag in tagList:
            article.add_tag(get_or_create_tag(tag))
    article.save()
    return article


@blueprint.route('/api/articles/<slug>', methods=('PUT',))
@jwt_required
@use_kwargs(article_schema)
@marshal_with(article_schema)
def update_article(slug, **kwargs):
    article = get_article_or_404(slug, author_id=current_user.profile.id)
    article.update(updatedAt=dt.datetime.utcnow(), **kwargs)
    article.save()
    return article


@blueprint.route('/api/articles/<slug>', methods=('DELETE',))
@jwt_required
def delete_article(slug):
    article = get_article_or_404(slug, author_id=current_user.profile.id)
    article.delete()
    return '', 200


@blueprint.route('/api/articles/<slug>', methods=('GET',))
@jwt_optional
@marshal_with(article_schema)
def get_article(slug):
    return get_article_or_404(slug)


@blueprint.route('/api/articles/feed', methods=('GET',))
@jwt_required
@use_kwargs({'limit': fields.Int(), 'offset': fields.Int()})
@marshal_with(articles_schema)
def articles_feed(limit=20, offset=0):
    return Article.query.join(current_user.profile.follows). \
        order_by(Article.createdAt.desc()).offset(offset).limit(limit).all()


# ---------------------------------------------------------------------------
# Register routes from sibling modules so that importing this module is
# sufficient to activate all articles-related endpoints.
# ---------------------------------------------------------------------------
from . import favorites, comments, tags  # noqa: E402, F401
