# coding: utf-8

import datetime as dt

from flask import Blueprint, jsonify
from flask_apispec import marshal_with, use_kwargs
from flask_jwt_extended import current_user, jwt_required, jwt_optional
from marshmallow import fields

from conduit.exceptions import InvalidUsage
from conduit.user.models import User
from .models import Article, Tags, Comment
from .serializers import (article_schema, articles_schema, comment_schema,
                          comments_schema)

blueprint = Blueprint('articles', __name__)


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
            mtag = Tags.query.filter_by(tagname=tag).first()
            if not mtag:
                mtag = Tags(tag)
                mtag.save()
            article.add_tag(mtag)
    article.save()
    return article


@blueprint.route('/api/articles/<slug>', methods=('PUT',))
@jwt_required
@use_kwargs(article_schema)
@marshal_with(article_schema)
def update_article(slug, **kwargs):
    article = Article.query.filter_by(slug=slug, author_id=current_user.profile.id).first()
    if not article:
        raise InvalidUsage.article_not_found()
    article.update(updatedAt=dt.datetime.utcnow(), **kwargs)
    article.save()
    return article


@blueprint.route('/api/articles/<slug>', methods=('DELETE',))
@jwt_required
def delete_article(slug):
    article = Article.query.filter_by(slug=slug, author_id=current_user.profile.id).first()
    article.delete()
    return '', 200


@blueprint.route('/api/articles/<slug>', methods=('GET',))
@jwt_optional
@marshal_with(article_schema)
def get_article(slug):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    return article


@blueprint.route('/api/articles/<slug>/favorite', methods=('POST',))
@jwt_required
@marshal_with(article_schema)
def favorite_an_article(slug):
    profile = current_user.profile
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    article.favourite(profile)
    article.save()
    return article


@blueprint.route('/api/articles/<slug>/favorite', methods=('DELETE',))
@jwt_required
@marshal_with(article_schema)
def unfavorite_an_article(slug):
    profile = current_user.profile
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    article.unfavourite(profile)
    article.save()
    return article


@blueprint.route('/api/articles/feed', methods=('GET',))
@jwt_required
@use_kwargs({'limit': fields.Int(), 'offset': fields.Int()})
@marshal_with(articles_schema)
def articles_feed(limit=20, offset=0):
    return Article.query.join(current_user.profile.follows). \
        order_by(Article.createdAt.desc()).offset(offset).limit(limit).all()


def find_related_articles(article, limit=5):
    """Return articles related to ``article`` ranked deterministically.

    Ranking priority (all descending):
        1. number of shared tags -- the more tags in common, the higher
        2. same author as the source article
        3. most recently created
        4. id, as a final stable tie-breaker

    The source article itself is never included, and ``limit`` caps how many
    related articles come back so the "you might also like" entry point stays
    focused instead of dumping the whole table.
    """
    tag_ids = {tag.id for tag in article.tagList}

    # Keyed by id so an article matched by both tag and author is only kept once.
    candidates = {}

    if tag_ids:
        tagged = Article.query \
            .filter(Article.id != article.id) \
            .filter(Article.tagList.any(Tags.id.in_(tag_ids))) \
            .all()
        for candidate in tagged:
            candidates[candidate.id] = candidate

    authored = Article.query \
        .filter(Article.id != article.id) \
        .filter(Article.author_id == article.author_id) \
        .all()
    for candidate in authored:
        candidates[candidate.id] = candidate

    def rank(candidate):
        shared_tags = len(tag_ids & {tag.id for tag in candidate.tagList})
        same_author = 1 if candidate.author_id == article.author_id else 0
        created_at = candidate.createdAt or dt.datetime.min
        return (shared_tags, same_author, created_at, candidate.id)

    ranked = sorted(candidates.values(), key=rank, reverse=True)

    if limit is not None and limit >= 0:
        ranked = ranked[:limit]
    return ranked


@blueprint.route('/api/articles/<slug>/related', methods=('GET',))
@jwt_optional
@use_kwargs({'limit': fields.Int()})
@marshal_with(articles_schema)
def get_related_articles(slug, limit=5):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    return find_related_articles(article, limit)


######
# Tags
######

@blueprint.route('/api/tags', methods=('GET',))
def get_tags():
    return jsonify({'tags': [tag.tagname for tag in Tags.query.all()]})


##########
# Comments
##########


@blueprint.route('/api/articles/<slug>/comments', methods=('GET',))
@marshal_with(comments_schema)
def get_comments(slug):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    return article.comments


@blueprint.route('/api/articles/<slug>/comments', methods=('POST',))
@jwt_required
@use_kwargs(comment_schema)
@marshal_with(comment_schema)
def make_comment_on_article(slug, body, **kwargs):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()
    comment = Comment(article, current_user.profile, body, **kwargs)
    comment.save()
    return comment


@blueprint.route('/api/articles/<slug>/comments/<cid>', methods=('DELETE',))
@jwt_required
def delete_comment_on_article(slug, cid):
    article = Article.query.filter_by(slug=slug).first()
    if not article:
        raise InvalidUsage.article_not_found()

    comment = article.comments.filter_by(id=cid, author=current_user.profile).first()
    comment.delete()
    return '', 200
