#!/usr/bin/env python3

# Copyright 2020 pinebud77@hotmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import os
import os.path
from pathlib import Path

DEF_SETTINGS_FILENAME = 'yamm.settings'

LARGE_THUMBNAILS = 0
MEDIUM_THUMBNAILS = 1
SMALL_THUMBNAILS = 2

FILTER_SORT_FILENAME = 0
FILTER_SORT_TIME = 1
FILTER_SORT_LASTPLAY = 2
FILTER_SORT_DURATION = 3
FILTER_SORT_PATH = 4
FILTER_SORT_SIZE = 5

#main window settings
DEF_VIEW_TYPE = MEDIUM_THUMBNAILS
DEF_SORT_METHOD = FILTER_SORT_PATH
DEF_SORT_ASCEND = True
DEF_THUMBS_HEIGHT = 133
DEF_SMALL_RESOLUTION = (179, 101)
DEF_MEDIUM_RESOLUTION = (239, 135)

#mediafile settings
DEF_FILE_EXTENTION = ('mkv', 'avi', 'mp4', 'asf', 'wmv', 'flv')
DEF_MIN_IMAGE_COUNT = 5
DEF_MAX_IMAGE_COUNT = 40
DEF_THUMBNAIL_WIDTH = 360
DEF_THUMBNAIL_HEIGHT = 203
DEF_STREAM_PERIOD = 90

#open directives
DEF_OPEN_EXE = 'C:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini64.exe'
DEF_OPEN_FILE = '%s'
DEF_OPEN_SEEK = '/seek=%d'

def load_settings():
    path = os.path.join(Path.home(), DEF_SETTINGS_FILENAME)
    try:
        with open(path, 'r') as json_file:
            d = json.load(json_file)
    except:
        return

    global DEF_VIEW_TYPE
    global DEF_SORT_METHOD
    global DEF_SORT_ASCEND
    global DEF_THUMBS_HEIGHT
    global DEF_FILE_EXTENTION
    global DEF_MIN_IMAGE_COUNT
    global DEF_MAX_IMAGE_COUNT
    global DEF_THUMBNAIL_WIDTH
    global DEF_THUMBNAIL_HEIGHT
    global DEF_SMALL_RESOLUTION
    global DEF_MEDIUM_RESOLUTION
    global DEF_STREAM_PERIOD
    global DEF_OPEN_EXE
    global DEF_OPEN_FILE
    global DEF_OPEN_SEEK

    try:
        DEF_VIEW_TYPE = d['view_type']
        DEF_SORT_METHOD = d['sort_method']
        DEF_SORT_ASCEND = d['sort_ascend']
        DEF_THUMBS_HEIGHT = d['thumbs_height']
        DEF_FILE_EXTENTION = d['file_extention']
        DEF_MIN_IMAGE_COUNT = d['min_image_count']
        DEF_MAX_IMAGE_COUNT = d['max_image_count']
        DEF_THUMBNAIL_WIDTH = d['thumbnail_width']
        DEF_THUMBNAIL_HEIGHT = d['thumbnail_height']
        DEF_SMALL_RESOLUTION = d['small_resolution']
        DEF_MEDIUM_RESOLUTION = d['medium_resolution']
        DEF_STREAM_PERIOD = d['stream_period']
        DEF_OPEN_EXE = d['player_path']
        DEF_OPEN_FILE = d['player_file_opt']
        DEF_OPEN_SEEK = d['player_seek_opt']
    except:
        os.remove(path)


def store_settings():
    d = dict()

    global DEF_VIEW_TYPE
    global DEF_SORT_METHOD
    global DEF_SORT_ASCEND
    global DEF_THUMBS_HEIGHT
    global DEF_FILE_EXTENTION
    global DEF_MIN_IMAGE_COUNT
    global DEF_MAX_IMAGE_COUNT
    global DEF_THUMBNAIL_WIDTH
    global DEF_THUMBNAIL_HEIGHT
    global DEF_SMALL_RESOLUTION
    global DEF_MEDIUM_RESOLUTION
    global DEF_STREAM_PERIOD
    global DEF_OPEN_EXE
    global DEF_OPEN_FILE
    global DEF_OPEN_SEEK

    d['view_type'] = DEF_VIEW_TYPE
    d['sort_method'] = DEF_SORT_METHOD
    d['sort_ascend'] = DEF_SORT_ASCEND
    d['thumbs_height'] = DEF_THUMBS_HEIGHT
    d['file_extention'] = DEF_FILE_EXTENTION
    d['min_image_count'] = DEF_MIN_IMAGE_COUNT
    d['max_image_count'] = DEF_MAX_IMAGE_COUNT
    d['thumbnail_width'] = DEF_THUMBNAIL_WIDTH
    d['thumbnail_height'] = DEF_THUMBNAIL_HEIGHT
    d['small_resolution'] = DEF_SMALL_RESOLUTION
    d['medium_resolution'] = DEF_MEDIUM_RESOLUTION
    d['stream_period'] = DEF_STREAM_PERIOD
    d['player_path'] = DEF_OPEN_EXE
    d['player_file_opt'] = DEF_OPEN_FILE
    d['player_seek_opt'] = DEF_OPEN_SEEK

    path = os.path.join(Path.home(), DEF_SETTINGS_FILENAME)
    with open(path, 'w') as json_file:
        json.dump(d, json_file, indent=4, sort_keys=True)
