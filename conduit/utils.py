# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from conduit.user.models import User  # noqa


def jwt_identity(jwt_header, jwt_data):
    return User.get_by_id(jwt_data["sub"])


def identity_loader(user):
    return str(user.id)
