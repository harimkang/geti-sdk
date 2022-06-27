# Copyright (C) 2022 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions
# and limitations under the License.

from typing import Dict, Any, Type

from sc_api_tools.data_models.containers.media_list import MediaTypeVar
from sc_api_tools.utils import deserialize_dictionary


class MediaRESTConverter:
    """
    Class that handles conversion of SC REST output for media entities to objects and
    vice versa.
    """

    @staticmethod
    def from_dict(
            input_dict: Dict[str, Any],
            media_type: Type[MediaTypeVar]
    ) -> MediaTypeVar:
        """
        Creates an instance of type `media_type` representing a media entity in SC
        from a dictionary returned by the SC /media REST endpoints

        :param input_dict: Dictionary representing the media entity
        :param media_type: Type of the media entity
        :return: Instance of type `media_type` containing the entity represented in
            the REST input in `input_dict`.
        """
        return deserialize_dictionary(input_dict, output_type=media_type)
