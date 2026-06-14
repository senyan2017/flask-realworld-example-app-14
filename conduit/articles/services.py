# coding: utf-8
"""Shared helpers for the articles blueprint.

These exist so the view functions stay thin and consistent:

* every endpoint that needs an article looks it up through
  :func:`get_article_or_404`, instead of repeating the
  ``query -> if not found -> raise`` dance in each handler; and
* favouriting and unfavouriting -- which differ only by one model call --
  funnel through :func:`set_favorite`.
"""

from conduit.exceptions import InvalidUsage

from .models import Article


def get_article_or_404(slug, **filters):
    """Return the article matching ``slug`` (plus any extra column filters).

    Raises the standard ``Article not found`` 404 when nothing matches, so
    callers never have to repeat the existence check themselves.
    """
    article = Article.query.filter_by(slug=slug, **filters).first()
    if article is None:
        raise InvalidUsage.article_not_found()
    return article


def set_favorite(slug, profile, favorite):
    """Favourite (``favorite=True``) or unfavourite the article for ``profile``.

    Collapses the two otherwise-identical favourite/unfavourite handlers into
    one place; the boolean is the only thing that differs between them.
    """
    article = get_article_or_404(slug)
    if favorite:
        article.favourite(profile)
    else:
        article.unfavourite(profile)
    return article.save()
