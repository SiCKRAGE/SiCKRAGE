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
from marshmallow import fields
from marshmallow.validate import OneOf

from sickrage.core.enums import ProcessMethod
from sickrage.core.webserver.handlers.api.schemas import BaseSchema, BaseSuccessSchema


class PostProcessSchema(BaseSchema):
    """Complete postprocess schema"""

    path = fields.String(
        required=False,
        description="The path to the folder to post-process",
    )
    nzbName = fields.String(
        required=False,
        description="Release / NZB name if available",
    )
    processMethod = fields.String(
        required=False,
        default="copy",
        description="How should valid post-processed files be handled",
        example="copy",
        validate=[OneOf(choices=[x.name.lower() for x in ProcessMethod])]
    )
    type = fields.String(
        required=False,
        default="manual",
        description="The type of post-process being requested",
        example="auto",
        validate=[OneOf(choices=["auto", "manual"])]
    )
    delete = fields.Boolean(
        required=False,
        default=False,
        description="Mark download as failed",
    )
    failed = fields.Boolean(
        required=False,
        default=False,
        description="Mark download as failed",
    )
    isPriority = fields.Boolean(
        required=False,
        default=False,
        description="Replace the file even if it exists in a higher quality",
    )
    returnData = fields.Boolean(
        required=False,
        default=False,
        description="Returns the result of the post-process",
    )
    forceReplace = fields.Boolean(
        required=False,
        default=False,
        description="Force already post-processed files to be post-processed again",
    )
    forceNext = fields.Boolean(
        required=False,
        default=False,
        description="Waits for the current processing queue item to finish and returns result of this request",
    )


class PostProcessSuccessSchema(BaseSuccessSchema):
    data = fields.String(
        required=True,
        description="Validated and post-process logs",
    )