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


import sickrage
from sickrage.core.enums import ProcessMethod
from sickrage.core.webserver.handlers.api.v2 import ApiV2BaseHandler
from sickrage.core.webserver.handlers.api.v2.postprocess.schemas import PostProcessSchema


class Apiv2PostProcessHandler(ApiV2BaseHandler):
    def get(self):
        """Postprocess TV show video files"
        ---
        tags: [Post-Processing]
        summary: Manually post-process the files in the download folder
        description: Manually post-process the files in the download folder
        parameters:
        - in: query
          schema:
            PostProcessSchema
        responses:
          200:
            description: Success payload containing postprocess information
            content:
              application/json:
                schema:
                  PostProcessSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
        """
        path = self.get_argument("path", sickrage.app.config.general.tv_download_dir)
        nzb_name = self.get_argument("nzbName", None)
        process_method = self.get_argument("processMethod", ProcessMethod.COPY.name)
        proc_type = self.get_argument("type", 'manual')
        delete = self._parse_boolean(self.get_argument("delete", 'false'))
        failed = self._parse_boolean(self.get_argument("failed", 'false'))
        is_priority = self._parse_boolean(self.get_argument("isPriority", 'false'))
        return_data = self._parse_boolean(self.get_argument("returnData", 'false'))
        force_replace = self._parse_boolean(self.get_argument("forceReplace", 'false'))
        force_next = self._parse_boolean(self.get_argument("forceNext", 'false'))

        validation_errors = self._validate_schema(PostProcessSchema, self.request.arguments)
        if validation_errors:
            return self._bad_request(error=validation_errors)

        if not path and not sickrage.app.config.general.tv_download_dir:
            return self._bad_request(error={"path": "You need to provide a path or set TV Download Dir"})

        json_data = sickrage.app.postprocessor_queue.put(path, nzbName=nzb_name, process_method=ProcessMethod[process_method.upper()], force=force_replace,
                                                         is_priority=is_priority, delete_on=delete, failed=failed, proc_type=proc_type, force_next=force_next)

        if 'Processing succeeded' not in json_data and 'Successfully processed' not in json_data:
            return self._bad_request(error=json_data)

        return self.json_response({'data': json_data if return_data else ''})
