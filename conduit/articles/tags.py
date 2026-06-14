# coding: utf-8
"""Tag routes."""

from flask import jsonify

from .blueprints import blueprint
from .models import Tags


@blueprint.route('/api/tags', methods=('GET',))
def get_tags():
    return jsonify({'tags': [tag.tagname for tag in Tags.query.all()]})
