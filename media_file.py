#!/usr/bin/env python3
import os
import os.path
import logging
import io
from PIL import Image
from moviepy.editor import *

import database_utils as db_utils


MIN_IMAGE_COUNT = 5
MAX_IMAGE_COUNT = 40
DEF_THUMBNAIL_WIDTH = 360
DEF_THUMBNAIL_HEIGHT = 203
DEF_STREAM_PERIOD = 90


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
        self.stars = None
        self.size = None
        self.time = None
        self.lastplay = None
        self.duration = None
        self.comment = None

        self.catetory = None
        self.tag_list = None
        self.actor_list = None
        self.thumbnails = None
        self.cover = None

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

    def create_thumbnails(self, fpath, period=DEF_STREAM_PERIOD, width=DEF_THUMBNAIL_WIDTH, height=DEF_THUMBNAIL_HEIGHT):
        try:
            clip = VideoFileClip(fpath)
        except Exception as e:
            print(e)
            return

        if clip.duration < period * MIN_IMAGE_COUNT:
            period = clip.duration / MIN_IMAGE_COUNT
        if clip.duration > period * MAX_IMAGE_COUNT:
            period = clip.duration / MAX_IMAGE_COUNT

        duration = int(clip.duration)
        if duration == 0:
            duration = 1

        period = int(period)
        if period == 0:
            period = 1

        thumbnails = []
        for time in range(0, duration, period):
            frame = clip.get_frame(time)
            p = Image.fromarray(frame)
            p.thumbnail((width, height))

            byte_arr = io.BytesIO()
            p.save(byte_arr, format='JPEG')

            thumbnails.append((time, byte_arr.getvalue()))

        return thumbnails

    def abspath(self):
        return os.path.abspath(os.path.join(self.topdir.abspath, self.reldir, self.filename))

    def load_thumbnails(self, create=True):
        logging.debug('loading thumbnail for %s' % self.abspath())
        self.thumbnails = db_utils.get_thumbnails(self.catalog.db_conn, self.id)
        if self.thumbnails:
            return
        if not create:
            return
        self.thumbnails = self.create_thumbnails(self.abspath())
        if not self.thumbnails:
            return
        db_utils.add_thumbnails(self.catalog.db_conn, self.id, self.thumbnails)

    def get_thumbnails(self):
        if self.thumbnails:
            return self.thumbnails
        self.load_thumbnails(create=False)
        if self.thumbnails:
            return self.thumbnails
        return None

    def get_coverjpg(self):
        if self.cover:
            return self.cover
        if not self.thumbnails:
            self.load_thumbnails()
        if not self.thumbnails:
            return None
        count = len(self.thumbnails)
        count = int (count * 0.7)
        thumbnail = self.thumbnails[count][1]
        db_utils.del_cover(self.catalog.db_conn, self.id)
        db_utils.add_cover(self.catalog.db_conn, self.id, thumbnail)
        return thumbnail

    def set_cover_id(self, sel):
        if not self.thumbnails:
            return
        db_utils.del_cover(self.catalog.db_conn, self.id)
        db_utils.add_cover(self.catalog.db_conn, self.id, self.thumbnails[sel][1])
        self.cover = self.thumbnails[sel][1]

    def loadinfo(self):
        file_stats = os.stat(self.abspath())
        self.size = file_stats.st_size
        self.time = file_stats.st_ctime
        try:
            clip = VideoFileClip(self.abspath())
            self.duration = clip.duration
        except Exception as e:
            print(e)
            return

    def add_tag(self, tag):
        pass

    def remove_tag(self, tag):
        pass

    def set_category(self, category):
        pass

    def move_relpath(self, new_path):
        pass

    def delete(self):
        pass

    def __str__(self):
        return self.abspath()