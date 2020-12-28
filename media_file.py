#!/usr/bin/env python3
import os
import os.path
import logging
from moviepy.editor import *

from thumbnail_gen import create_thumbnails
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

    def abspath(self):
        return os.path.abspath(os.path.join(self.topdir.abspath, self.reldir, self.filename))

    def load_thumbnails(self, create=True):
        logging.info('loading thumbnail for %s' % self.abspath())
        self.thumbnails = db_utils.get_thumbnails(self.catalog.db_conn, self.id)
        if self.thumbnails:
            return
        if not create:
            return
        self.thumbnails = create_thumbnails(self.abspath())
        db_utils.add_thumbnails(self.catalog.db_conn, self.id, self.thumbnails)

    def get_coverjpg(self):
        if not self.thumbnails:
            return None
        count = len(self.thumbnails)
        count = int (count * 0.7)
        return self.thumbnails[count][1]

    def loadinfo(self):
        file_stats = os.stat(self.abspath())
        self.size = file_stats.st_size
        self.time = file_stats.st_atime
        clip = VideoFileClip(self.abspath)
        self.duration = clip.duration

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