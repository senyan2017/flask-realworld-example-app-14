# coding: utf-8
"""Shared helpers for the articles module."""

from conduit.exceptions import InvalidUsage
from .models import Article, Tags


def get_article_or_404(slug, author_id=None):
    """Look up an article by slug, raising 404 if not found.

    If *author_id* is given the query is scoped to that author, which is
    useful for update/delete endpoints that must verify ownership.
    """
    query = Article.query.filter_by(slug=slug)
    if author_id is not None:
        query = query.filter_by(author_id=author_id)
    article = query.first()
    if not article:
        raise InvalidUsage.article_not_found()
    return article


def get_or_create_tag(tagname):
    """Return the Tags row for *tagname*, creating it if it doesn't exist."""
    tag = Tags.query.filter_by(tagname=tagname).first()
    if not tag:
        tag = Tags(tagname)
        tag.save()
    return tag
