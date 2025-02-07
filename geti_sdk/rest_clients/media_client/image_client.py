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

import datetime
import glob
import io
import os
from typing import List, Optional, Sequence, Union

import cv2
import numpy as np

from geti_sdk.data_models import Image, MediaType
from geti_sdk.data_models.containers import MediaList
from geti_sdk.data_models.project import Dataset
from geti_sdk.rest_converters import MediaRESTConverter

from .media_client import MEDIA_SUPPORTED_FORMAT_MAPPING, BaseMediaClient


class ImageClient(BaseMediaClient[Image]):
    """
    Class to manage image uploads and downloads for a certain project.
    """

    _MEDIA_TYPE = MediaType.IMAGE

    def get_all_images(self, dataset: Optional[Dataset] = None) -> MediaList[Image]:
        """
        Get the ID's and filenames of all images in the project, from a specific
        dataset. If no dataset is passed, images from the training dataset will be
        returned

        :param dataset: Dataset for which to retrieve the images. If no dataset is
            passed, images from the training dataset are returned.
        :return: MediaList containing all Image entities in the dataset
        """
        return self._get_all(dataset=dataset)

    def upload_image(
        self,
        image: Union[np.ndarray, str, os.PathLike],
        dataset: Optional[Dataset] = None,
    ) -> Image:
        """
        Upload an image file to the server.

        :param image: full path to the image on disk, or numpy array representing the
            image
        :param dataset: Dataset to which to upload the image. If no dataset is
            passed, the image is uploaded to the training dataset
        :return: Image object representing the uploaded image on the server
        """
        if isinstance(image, (str, os.PathLike)):
            image_dict = self._upload(image, dataset=dataset)
        elif isinstance(image, np.ndarray):
            image_io = io.BytesIO(cv2.imencode(".jpg", image)[1].tobytes())
            time_now = datetime.datetime.now()
            image_io.name = f"numpy_{time_now.strftime('%Y-%m-%dT%H-%M-%S.%f')}.jpg"
            image_dict = self._upload_bytes(image_io, dataset=dataset)
        else:
            raise TypeError(f"Invalid image type: {type(image)}.")
        return MediaRESTConverter.from_dict(input_dict=image_dict, media_type=Image)

    def upload_folder(
        self,
        path_to_folder: str,
        n_images: int = -1,
        skip_if_filename_exists: bool = False,
        dataset: Optional[Dataset] = None,
    ) -> MediaList[Image]:
        """
        Upload all images in a folder to the project. Returns a MediaList containing
        all images in the project after upload.

        :param path_to_folder: Folder with images to upload
        :param n_images: Number of images to upload from folder
        :param skip_if_filename_exists: Set to True to skip uploading of an image
            if an image with the same filename already exists in the project.
            Defaults to False
        :param dataset: Dataset to which to upload the images. If no dataset is
            passed, the images are uploaded to the training dataset
        :return: MediaList containing all image's in the project
        """
        return self._upload_folder(
            path_to_folder=path_to_folder,
            n_media=n_images,
            skip_if_filename_exists=skip_if_filename_exists,
            dataset=dataset,
        )

    def download_all(self, path_to_folder: str, append_image_uid: bool = False) -> None:
        """
        Download all images in a project to a folder on the local disk.

        :param path_to_folder: path to the folder in which the images should be saved
        :param append_image_uid: True to append the UID of an image to the
            filename (separated from the original filename by an underscore, i.e.
            '{filename}_{image_id}'). If there are images in the project with
            duplicate filename, this must be set to True to ensure all images are
            downloaded. Otherwise images with the same name will be skipped.
        """
        self._download_all(path_to_folder, append_media_uid=append_image_uid)

    def upload_from_list(
        self,
        path_to_folder: str,
        image_names: List[str],
        extension_included: bool = False,
        n_images: int = -1,
        skip_if_filename_exists: bool = False,
        image_names_as_full_paths: bool = False,
        dataset: Optional[Dataset] = None,
    ) -> MediaList[Image]:
        """
        From a folder containing images `path_to_folder`, this method uploads only
        those images that have their filenames included in the `image_names` list.

        :param path_to_folder: Folder containing the images
        :param image_names: List of names of the images that should be uploaded
        :param extension_included: Set to True if the extension of the image is
            included in the name, for each image in the image_names list. Defaults to
            False
        :param n_images: Number of images to upload from the list
        :param skip_if_filename_exists: Set to True to skip uploading of an image
            if an image with the same filename already exists in the project.
            Defaults to False
        :param image_names_as_full_paths: Set to True if the list of `image_names`
            contains full paths to the images, rather than just the filenames
        :param dataset: Dataset to which to upload the images. If no dataset is
            passed, the images are uploaded to the training dataset
        :return: List of images that were uploaded
        """
        media_formats = MEDIA_SUPPORTED_FORMAT_MAPPING[self._MEDIA_TYPE]

        if n_images > len(image_names) or n_images == -1:
            n_to_upload = len(image_names)
        else:
            n_to_upload = n_images

        image_filepaths: List[str] = []
        if image_names_as_full_paths:
            if extension_included:
                image_filepaths = image_names
            else:
                for image_name in image_names:
                    for media_extension in media_formats:
                        if os.path.isfile(image_name + media_extension):
                            image_filepaths.append(image_name + media_extension)
            image_filepaths = image_filepaths[0:n_to_upload]

        else:
            for image_name in image_names[0:n_to_upload]:
                if not extension_included:
                    matches: List[str] = []
                    for media_extension in media_formats:
                        matches += glob.glob(
                            os.path.join(
                                path_to_folder, "**", f"{image_name}{media_extension}"
                            ),
                            recursive=True,
                        )
                else:
                    matches = glob.glob(
                        os.path.join(path_to_folder, "**", image_name), recursive=True
                    )
                if not matches:
                    raise ValueError(
                        f"No matching file found for image with name {image_name}"
                    )
                elif len(matches) != 1:
                    raise ValueError(
                        f"Multiple files found for image with name {image_name}: "
                        f"{matches}"
                    )
                image_filepaths.append(matches[0])
        return self._upload_loop(
            filepaths=image_filepaths,
            skip_if_filename_exists=skip_if_filename_exists,
            dataset=dataset,
        )

    def delete_images(self, images: Sequence[Image]) -> bool:
        """
        Delete all Image entities in `images` from the project.

        :param images: List of Image entities to delete
        :return: True if all images on the list were deleted successfully,
            False otherwise
        """
        return self._delete_media(media_list=images)
