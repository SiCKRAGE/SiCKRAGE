"""Initial migration

Revision ID: 10
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

revision = '10'
down_revision = '9'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    refresh_token = None
    with op.get_context().begin_transaction():
        for row in conn.execute(oauth2_token.select()):
            refresh_token = row.refresh_token
            if refresh_token:
                break

    try:
        if refresh_token:
            certs = sickrage.app.auth_server.certs()
            if certs:
                new_token = sickrage.app.auth_server.refresh_token(refresh_token)
                if new_token:
                    decoded_token = sickrage.app.auth_server.decode_token(new_token['access_token'], certs)
                    apikey = decoded_token.get('apikey')
                    if apikey:
                        session = sickrage.app.config.db.session()
                        general = session.query(ConfigDB.General).one()
                        general.sso_api_key = apikey
                        session.commit()
    except (KeycloakClientError, orm.exc.NoResultFound):
        pass

    if inspect(conn).has_table('oauth2_token'):
        op.drop_table('oauth2_token')


def downgrade():
    # Operations to reverse the above upgrade go here.
    pass
