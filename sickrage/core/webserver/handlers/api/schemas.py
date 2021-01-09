# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

from marshmallow import Schema, fields


class BaseSchema(Schema):
    class Meta:
        ordered = True


class NotAuthorizedSchema(BaseSchema):
    error = fields.String(
        required=False,
        description="Authorization error",
        default="Not Authorized",
    )


class NotFoundSchema(BaseSchema):
    error = fields.String(
        required=False,
        description="Not Found error",
        default="Not Found",
    )


class BaseSuccessSchema(BaseSchema):
    success = fields.Boolean(
        required=True,
        description='This is always "True" when a request succeeds',
        example=True,
    )


class BaseErrorSchema(BaseSchema):
    success = fields.Boolean(
        required=True,
        description='This is always "False" when a request fails',
        example=False,
    )


class BadRequestSchema(BaseErrorSchema):
    errors = fields.Dict(
        required=False,
        description="Attached request validation errors",
        example={"name": ["Missing data for required field."]},
    )
