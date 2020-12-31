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

import os
import os.path
import logging
import io
from PIL import Image
from moviepy.editor import VideoFileClip

from settings import *
import database_utils as db_utils

class TopDirectory:
    def __init__(self, cat, abspath, comment=None):
        self.catalog = cat
        self.id = -1
        self.abspath = abspath
        self.comment = comment

    def load_dbtuple(self, t):
        self.id = t[0]
        self.abspath = t[1]
        self.comment = t[2]

    def get_dbtuple(self):
        return (self.id, self.abspath, self.comment)

    def __str__(self):
        return 'topdir id:%d abspath:%s' % (self.id, self.abspath)


class MediaFile:
    def __init__(self, catalog, topdir, reldir, filename):
        self.catalog = catalog
        self.id = None
        self.topdir = topdir
        self.reldir = reldir
        self.filename = filename
        self.abspath = os.path.join(topdir.abspath, reldir, filename)
        self.stars = None
        self.size = None
        self.time = None
        self.lastplay = None
        self.duration = None
        self.comment = None

        self.catetory = None
        self.tag_list = []
        self.actor_list = []
        self.thumbnails = None
        self.cover = None

        self.imagelist_index = None

    def load_dbtuple(self, t):
        self.id = t[0]
        self.topdir = self.catalog.get_topdir_from_id(t[1])
        self.reldir = t[2]
        self.filename = t[3]
        self.stars = t[4]
        self.size = t[5]
        self.time = t[6]
        self.lastplay = t[7]
        self.duration = t[8]
        self.comment = t[9]

    def set_lastplayed(self, dt):
        self.lastplay = dt
        db_utils.update_file(self.catalog.db_conn, self)

    def create_thumbnails(self,
                          period=DEF_STREAM_PERIOD,
                          width=DEF_THUMBNAIL_WIDTH,
                          height=DEF_THUMBNAIL_HEIGHT):
        fpath = self.abspath
        try:
            clip = VideoFileClip(fpath, audio=False)
        except Exception as e:
            print(e)
            return

        if clip.duration < period * DEF_MIN_IMAGE_COUNT:
            period = clip.duration / DEF_MIN_IMAGE_COUNT
        if clip.duration > period * DEF_MAX_IMAGE_COUNT:
            period = clip.duration / DEF_MAX_IMAGE_COUNT
        period = int(period)
        if period == 0:
            period = 1

        duration = int(clip.duration)
        if duration == 0:
            duration = 1

        thumbnails = []
        for time in range(0, duration, period):
            try:
                frame = clip.get_frame(time)
            except Exception as e:
                print(e)
                return
            p = Image.fromarray(frame)
            p.thumbnail((width, height))

            byte_arr = io.BytesIO()
            p.save(byte_arr, format='JPEG')

            thumbnails.append((time, byte_arr.getvalue()))

        self.thumbnails = thumbnails

    def save_thumbnails(self):
        if not self.thumbnails:
            return
        db_utils.add_thumbnails(self.catalog.db_conn, self.id, self.thumbnails)

    def load_thumbnails(self):
        logging.info('loading thumbnail for %s' % self.abspath)
        self.thumbnails = db_utils.get_thumbnails(self.catalog.db_conn, self.id)
        if self.thumbnails:
            return

    def get_thumbnails(self):
        if self.thumbnails:
            return self.thumbnails
        self.load_thumbnails()
        if self.thumbnails:
            return self.thumbnails
        return None

    def get_coverjpg(self, read_db=False):
        if self.cover:
            return self.cover
        if not read_db:
            return None
        rows = db_utils.get_cover(self.catalog.db_conn, self.id)
        if rows:
            self.cover = rows[0][0]
            if self.cover:
                return self.cover
        return None

    def set_cover_id(self, sel):
        if not self.thumbnails:
            return
        db_utils.del_cover(self.catalog.db_conn, self.id)
        db_utils.add_cover(self.catalog.db_conn, self.id, self.thumbnails[sel][1])
        self.cover = self.thumbnails[sel][1]

    def loadinfo(self):
        file_stats = os.stat(self.abspath)
        self.size = file_stats.st_size
        self.time = file_stats.st_ctime
        try:
            clip = VideoFileClip(self.abspath, audio=False)
            self.duration = clip.duration
        except Exception as e:
            print(e)
            return

    def add_actor(self, name):
        if name in self.actor_list:
            return
        self.catalog.add_actor(name)
        db_utils.add_actorfile(self.catalog.db_conn, name, self.id)
        self.actor_list.append(name)

    def del_actor(self, name):
        if not (name in self.actor_list):
            return
        db_utils.del_actorfile(self.catalog.db_conn, name, self.id)
        self.actor_list.remove(name)

    def add_tag(self, tag):
        if tag in self.tag_list:
            return
        self.catalog.add_tag(tag)
        db_utils.add_tag(self.catalog.db_conn, tag, self.id)
        self.tag_list.append(tag)

    def del_tag(self, tag):
        if not (tag in self.tag_list):
            return
        db_utils.del_tag(self.catalog.db_conn, tag, self.id)
        self.tag_list.remove(tag)

    def set_category(self, category):
        pass

    def move_relpath(self, new_path):
        pass

    def delete(self):
        pass

    def __str__(self):
        return self.abspath