"""Initial migration

Revision ID: 4
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import json
import os
from json import JSONDecodeError

import sqlalchemy as sa
from alembic import op

import sickrage

# revision identifiers, used by Alembic.
revision = '4'
down_revision = '3'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)

    op.create_table(
        'oauth2_token',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('access_token', sa.String(255), unique=True, nullable=False),
        sa.Column('refresh_token', sa.String(255), index=True),
        sa.Column('expires_in', sa.Integer, nullable=False, default=0),
        sa.Column('expires_at', sa.Integer, nullable=False, default=0),
        sa.Column('scope', sa.Text, default=""),
        sa.Column('session_state', sa.Text, default=""),
        sa.Column('token_type', sa.Text, default="bearer"),
    )

    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    token_file = os.path.abspath(os.path.join(sickrage.app.data_dir, 'token.json'))

    if os.path.exists(token_file):
        with open(token_file, 'r') as fd:
            try:
                token = json.load(fd)
                conn.execute(oauth2_token.insert().values(
                    access_token=token['access_token'],
                    refresh_token=token['refresh_token'],
                    expires_in=token['expires_in'],
                    expires_at=token['expires_at'],
                    scope=' '.join(token['scope']) if isinstance(token['scope'], list) else token['scope']
                ))
            except JSONDecodeError:
                pass

        os.remove(token_file)


def downgrade():
    # Operations to reverse the above upgrade go here.
    pass