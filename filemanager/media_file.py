#!/usr/bin/env python3
import os
import os.path


class TopDirectory:
    def __init__(self, cat, abspath, comment=None):
        self.cat = cat
        self.id = -1
        self.abspath = abspath
        self.comment = comment

    def __str__(self):
        return self.abspath


class MediaFile:
    def __init__(self, catalog, topdir, relpath):
        self.catalog = catalog
        self.topdir = topdir
        self.relpath = relpath
        self.stars = None
        self.tag_list = None
        self.catetory = None
        self.comment = None

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

    def set_star(self, star_count):
        pass

    def __str__(self):
        return os.path.join(self.topdir.abspath, self.relpath)