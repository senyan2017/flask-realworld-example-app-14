# coding: utf-8
"""Public entry point for the articles blueprint.

The endpoints themselves now live in focused modules grouped by concern:

* :mod:`conduit.articles.articles`  -- article CRUD and the feed
* :mod:`conduit.articles.comments`  -- comments on an article
* :mod:`conduit.articles.favorites` -- favourite / unfavourite
* :mod:`conduit.articles.tags`      -- tag listing

Importing those modules here is what registers their routes on the shared
``blueprint``. ``app.py`` and the package ``__init__`` import this module and
use ``blueprint``, so the external wiring is unchanged.
"""

from .blueprint import blueprint  # noqa: F401
from . import articles, comments, favorites, tags  # noqa: F401
