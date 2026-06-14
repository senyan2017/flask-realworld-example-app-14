# coding: utf-8
"""Favorite / unfavorite routes."""

from flask_apispec import marshal_with
from flask_jwt_extended import current_user, jwt_required

from .blueprints import blueprint
from .serializers import article_schema
from .utils import get_article_or_404


@blueprint.route('/api/articles/<slug>/favorite', methods=('POST',))
@jwt_required
@marshal_with(article_schema)
def favorite_an_article(slug):
    article = get_article_or_404(slug)
    article.favourite(current_user.profile)
    article.save()
    return article


@blueprint.route('/api/articles/<slug>/favorite', methods=('DELETE',))
@jwt_required
@marshal_with(article_schema)
def unfavorite_an_article(slug):
    article = get_article_or_404(slug)
    article.unfavourite(current_user.profile)
    article.save()
    return article
