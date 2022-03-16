"""Initial migration

Revision ID: 11
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import json
import os
from json import JSONDecodeError

import sqlalchemy as sa
from alembic import op
from keycloak.exceptions import KeycloakClientError
from sqlalchemy import orm, inspect

import sickrage

# revision identifiers, used by Alembic.
from sickrage.core import ConfigDB

revision = '11'
down_revision = '10'


def upgrade():
    pass


def downgrade():
    # Operations to reverse the above upgrade go here.
    pass
