# coding: utf-8
"""Comment endpoints scoped to a single article."""

from flask_apispec import marshal_with, use_kwargs
from flask_jwt_extended import current_user, jwt_required

from .blueprint import blueprint
from .models import Comment
from .serializers import comment_schema, comments_schema
from .services import get_article_or_404


@blueprint.route('/api/articles/<slug>/comments', methods=('GET',))
@marshal_with(comments_schema)
def get_comments(slug):
    article = get_article_or_404(slug)
    return article.comments


@blueprint.route('/api/articles/<slug>/comments', methods=('POST',))
@jwt_required
@use_kwargs(comment_schema)
@marshal_with(comment_schema)
def make_comment_on_article(slug, body, **kwargs):
    article = get_article_or_404(slug)
    comment = Comment(article, current_user.profile, body, **kwargs)
    comment.save()
    return comment


@blueprint.route('/api/articles/<slug>/comments/<cid>', methods=('DELETE',))
@jwt_required
def delete_comment_on_article(slug, cid):
    article = get_article_or_404(slug)
    comment = article.comments.filter_by(id=cid, author=current_user.profile).first()
    comment.delete()
    return '', 200
