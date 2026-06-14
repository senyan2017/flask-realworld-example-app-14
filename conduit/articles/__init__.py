# coding: utf-8

# Importing views triggers registration of all routes (articles, favorites,
# comments, tags) on the shared blueprint.
from . import views  # noqa: F401

# Re-export the blueprint so that ``articles.views.blueprint`` continues to
# work for existing imports in app.py and tests.
from .blueprints import blueprint  # noqa: F401
