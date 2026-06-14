# coding: utf-8
"""Favourite / unfavourite endpoints for an article."""

from flask_apispec import marshal_with
from flask_jwt_extended import current_user, jwt_required

from .blueprint import blueprint
from .serializers import article_schema
from .services import set_favorite


@blueprint.route('/api/articles/<slug>/favorite', methods=('POST',))
@jwt_required
@marshal_with(article_schema)
def favorite_an_article(slug):
    return set_favorite(slug, current_user.profile, favorite=True)


@blueprint.route('/api/articles/<slug>/favorite', methods=('DELETE',))
@jwt_required
@marshal_with(article_schema)
def unfavorite_an_article(slug):
    return set_favorite(slug, current_user.profile, favorite=False)
