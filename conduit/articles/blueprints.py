# coding: utf-8
"""Shared Flask Blueprint for the articles module.

All route sub-modules (views, favorites, comments, tags) import this single
blueprint instance and register their routes on it.  This avoids circular
imports: no sub-module needs to import another sub-module just to reach the
blueprint.
"""

from flask import Blueprint

blueprint = Blueprint('articles', __name__)
