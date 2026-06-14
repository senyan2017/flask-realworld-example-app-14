# coding: utf-8
"""Tag listing endpoint."""

from flask import jsonify

from .blueprint import blueprint
from .models import Tags


@blueprint.route('/api/tags', methods=('GET',))
def get_tags():
    return jsonify({'tags': [tag.tagname for tag in Tags.query.all()]})
