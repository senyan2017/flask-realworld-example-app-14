# coding: utf-8
"""The single blueprint shared by every articles endpoint.

It lives in its own module so the per-concern view modules (``articles``,
``comments``, ``tags``, ``favorites``) can all register routes on the same
``Blueprint`` instance without importing each other. The blueprint name stays
``articles`` so endpoint names (and therefore ``url_for``) are unchanged.
"""

from flask import Blueprint

blueprint = Blueprint('articles', __name__)
