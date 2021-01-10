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
import io
import os.path
import logging
from PIL import Image
from moviepy.editor import VideoFileClip

from settings import *
import database_utils as db_utils


def get_time(fav):
    return fav.time


class TopDirectory:
    def __init__(self, cat, abspath, comment=None, exclude=False):
        self.catalog = cat
        self.id = -1
        self.abspath = os.path.abspath(abspath)
        self.comment = comment
        self.exclude = exclude

    def load_dbtuple(self, t):
        self.id = t[0]
        self.abspath = t[1]
        self.exclude = t[2]
        self.comment = t[3]

    def get_dbtuple(self):
        return self.id, self.abspath, self.exclude, self.comment,

    def __str__(self):
        return 'topdir id:%d abspath:%s exclude:%s' % (self.id, self.abspath, self.exclude)


class Favorite:
    def __init__(self, mf, time, id=None, thumb_id=None):
        self.mediafile = mf
        self.time = time
        self.id = id
        self.thumb_id = thumb_id
        self.imagelist_index =None

    def store(self):
        db_conn = self.mediafile.catalog.db_conn
        db_utils.add_favorite(db_conn, self.mediafile.id, self.thumb_id)

    def delete(self):
        db_conn = self.mediafile.catalog.db_conn
        db_utils.del_favorite(db_conn, self.id)

    def __str__(self):
        return 'favorite file:%s time:%d' % (self.mediafile, self.time)


class MediaFile:
    def __init__(self, catalog, topdir, reldir, filename):
        self.catalog = catalog
        self.id = None
        self.topdir = topdir
        self.reldir = reldir
        self.filename = filename
        self.size = None
        self.time = None
        self.lastplay = None
        self.duration = None
        self.comment = None
        self.width = None
        self.height = None

        self.catetory = None
        self.tag_list = []
        self.actor_list = []
        self.thumbnails = None
        self.cover = None
        self.favorites = []

        self.abspath = os.path.join(topdir.abspath, reldir, filename)
        self.imagelist_index = None

    def load_dbtuple(self, t):
        self.id = t[0]
        self.topdir = self.catalog.get_topdir_from_id(t[1])
        self.reldir = t[2]
        self.filename = t[3]
        self.size = t[4]
        self.time = t[5]
        self.lastplay = t[6]
        self.duration = t[7]
        self.comment = t[8]
        self.width = t[9]
        self.height = t[10]

    def set_lastplayed(self, dt):
        self.lastplay = dt
        db_utils.update_file(self.catalog.db_conn, self)

    def get_resolution(self, dwidth, dheight, width, height):
        theight = width * dheight / dwidth
        if theight <= dheight:
            return int(dwidth), int(theight)
        theight = dheight
        twidth = theight * width / height
        return int(twidth), int(theight)

    def create_thumbnails(self,
                          period=DEF_STREAM_PERIOD,
                          width=DEF_THUMBNAIL_WIDTH,
                          height=DEF_THUMBNAIL_HEIGHT):
        try:
            clip = VideoFileClip(self.abspath, audio=False)
            self.width = clip.size[0]
            self.height = clip.size[1]
            clip.close()
            del(clip)
        except Exception as e:
            logging.error(e)
            return

        width, height = self.get_resolution(width, height, self.width, self.height)
        try:
            clip = VideoFileClip(self.abspath, target_resolution=(height, width), audio=False)
        except Exception as e:
            logging.error(e)
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
            if self.catalog.kill_thread:
                return
            try:
                frame = clip.get_frame(time)
            except Exception as e:
                logging.error(e)
                return
            p = Image.fromarray(frame)

            byte_arr = io.BytesIO()
            p.save(byte_arr, format='JPEG')

            thumbnails.append((time, byte_arr.getvalue()))

        self.thumbnails = thumbnails

        try:
            clip.close()
            del(clip)
        except Exception as e:
            logging.error(e)
            return

    def save_thumbnails(self):
        if not self.thumbnails:
            return
        db_utils.add_thumbnails(self.catalog.db_conn, self.id, self.thumbnails)

    def load_thumbnails(self):
        logging.debug('loading thumbnail for %s' % self.abspath)
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

    def get_thumbjpg(self, thumb_id):
        jpg = db_utils.get_thumbnail_from_id(self.catalog.db_conn, thumb_id)[3]
        return jpg

    def get_coverjpg(self, read_db=True):
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
            self.width = clip.size[0]
            self.height = clip.size[1]
            clip.close()
            del(clip)
        except Exception as e:
            logging.error(e)
            return

    def add_actor(self, name):
        if name in self.actor_list:
            return
        self.catalog.add_actor(name)
        actor_id = db_utils.get_actorid_from_name(self.catalog.db_conn, name)
        db_utils.add_actorfile(self.catalog.db_conn, actor_id, self.id)
        self.actor_list.append(name)

    def del_actor(self, name):
        if not (name in self.actor_list):
            return
        db_utils.del_actorfile(self.catalog.db_conn, name, self.id)
        self.actor_list.remove(name)

    def modify_actor(self, orig_name, new_name):
        if not (orig_name in self.actor_list):
            return
        self.actor_list.remove(orig_name)
        self.actor_list.append(new_name)
        self.actor_list.sort()

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

    def modify_tag(self, orig_tag, new_tag):
        if not (orig_tag in self.tag_list):
            return
        db_utils.modify_tag(self.catalog.db_conn, self.id, orig_tag, new_tag)
        self.tag_list.remove(orig_tag)
        self.tag_list.append(new_tag)
        self.tag_list.sort()

    def add_favorite(self, time):
        for fav in self.favorites:
            if time == fav.time:
                return

        clean_thumbnails = False
        if not self.thumbnails:
            self.load_thumbnails()
            clean_thumbnails = True

        fav = None
        for thumb in self.thumbnails:
            if thumb[0] != time:
                continue
            thumb_id = thumb[2]
            db_utils.add_favorite(self.catalog.db_conn, self.id, thumb_id)
            fav_id = db_utils.get_favorite_id(self.catalog.db_conn, self.id, thumb_id)
            fav = Favorite(self, time, id=fav_id, thumb_id=thumb_id)
            self.favorites.append(fav)
            self.favorites.sort(key=get_time)
            break

        if clean_thumbnails:
            self.thumbnails = None

        return fav

    def del_favorite(self, fav):
        if fav not in self.favorites:
            return

        self.favorites.remove(fav)
        db_utils.del_favorite(self.catalog.db_conn, fav.id)

    def __str__(self):
        return self.abspath