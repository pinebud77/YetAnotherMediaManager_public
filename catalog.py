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
import sqlite3
import datetime

from settings import *
import media_file
import database_utils as db_utils
import file_utils as file_utils


MAJOR_VERSION = 0
MINOR_VERSION = 1

def get_abspath(topdir):
    return topdir.abspath

def get_2nd_element(list_element):
    return list_element[1]


def get_rel_path(media_file):
    return os.path.join(media_file.reldir, media_file.filename)


class Catalog(list):
    def __init__(self, db_abspath, extension_list=DEF_FILE_EXTENTION):
        self.filepath = db_abspath
        self.topdir_list = []
        self.tag_list = []
        self.actor_list = []
        self.db_conn = None
        self.extension_list = extension_list
        self.kill_thread = False

    def open_database(self):
        try:
            self.db_conn = sqlite3.connect(self.filepath)
            logging.info('sqlite3 version: ' + sqlite3.version)
        except Exception as e:
            logging.error('failed to open database file: %s' % self.filepath)
            logging.error('exception: %s' % e)
            return None

        # get DB version
        # TODO: add migration code based on DB and APP version diff
        ver_tuple = db_utils.get_app_version(self.db_conn)
        if ver_tuple:
            logging.info('database version = %d.%d' % (ver_tuple[0], ver_tuple[1]))
        elif not ver_tuple or ver_tuple[0] != MAJOR_VERSION or ver_tuple[1] != MINOR_VERSION:
            db_utils.set_app_version(self.db_conn, MAJOR_VERSION, MINOR_VERSION)

        # enable foreign key support
        db_utils.enable_foreign_key(self.db_conn)

        # create or load topdir table
        db_utils.create_topdir_list(self.db_conn)
        db_topdir_list = db_utils.get_topdir_list(self.db_conn)
        db_topdir_list.sort(key=get_2nd_element)
        for db_td in db_topdir_list:
            td = media_file.TopDirectory(self, db_td[1], db_td[2])
            td.load_dbtuple(db_td)
            self.topdir_list.append(td)

        # create thumbnail table if does not exists
        db_utils.create_thumbnail_table(self.db_conn)

        # create or load file table
        db_utils.create_file_table(self.db_conn)
        db_file_list = db_utils.get_file_list(self.db_conn)
        for df in db_file_list:
            topdir = self.get_topdir_from_id(df[1])
            mf = media_file.MediaFile(self, topdir, df[2], df[3])
            mf.load_dbtuple(df)
            self.append(mf)

        # create actor table
        db_utils.create_actor_table(self.db_conn)
        db_actor_list = db_utils.get_actor_list(self.db_conn)
        for db_actor in db_actor_list:
            self.actor_list.append(db_actor[0])

        # create actorfile table
        db_utils.create_actorfile_table(self.db_conn)
        db_actorfile_list = db_utils.get_actorfile_list(self.db_conn)
        for db_actorfile in db_actorfile_list:
            mf = self.get_file_from_id(db_actorfile[1])
            mf.actor_list.append(db_actorfile[0])

        # create or load tag table
        db_utils.create_tag_table(self.db_conn)
        db_tag_list = db_utils.get_tag_list(self.db_conn)
        for db_tag in db_tag_list:
            tag = db_tag[0]
            mf = self.get_file_from_id(db_tag[1])
            mf.tag_list.append(tag)
            if tag not in self.tag_list:
                self.tag_list.append(tag)

        #load cover table
        db_utils.create_cover_table(self.db_conn)
        db_cover_list = db_utils.get_cover_list(self.db_conn)
        for dc in db_cover_list:
            file_id = dc[1]
            jpg = dc[2]
            for mf in self:
                if mf.id == file_id:
                    mf.cover = jpg
                    break

    def add_actor(self, name, picture=None):
        if name in self.actor_list:
            return
        db_utils.add_actor(self.db_conn, name, picture)
        self.actor_list.append(name)

    def add_tag(self, tag):
        if tag in self.tag_list:
            return
        self.tag_list.append(tag)

    def get_file_from_id(self, file_id):
        for mf in self:
            if mf.id == file_id:
                return mf
        return None

    def filter(self, actors=[], tags=[], filename='', stars=None):
        l = []
        for mf in self:
            l.append(mf)

        if actors:
            mf_i = 0
            while mf_i < len(l):
                mf = l[mf_i]
                found = False
                for actor in actors:
                    if actor in mf.actor_list:
                        found = True
                if not found:
                    del(l[mf_i])
                else:
                    mf_i += 1

        if tags:
            mf_i = 0
            while mf_i < len(l):
                mf = l[mf_i]
                found = False
                for tag in tags:
                    if tag in mf.tag_list:
                        found = True
                if not found:
                    del(l[mf_i])
                else:
                    mf_i += 1

        if filename:
            mf_i = 0
            while mf_i < len(l):
                mf = l[mf_i]
                if not (filename.lower() in mf.abspath.lower()):
                    del(l[mf_i])
                else:
                    mf_i += 1

        return l

    def get_topdir_from_id(self, topdir_id):
        for topdir in self.topdir_list:
            if topdir.id == topdir_id:
                return topdir
        return None

    def get_topdir_from_abspath(self, abspath):
        for topdir in self.topdir_list:
            if topdir.abspath == abspath:
                return topdir
        return None

    def add_topdir(self, abspath, comment=None):
        topdir = self.get_topdir_from_abspath(abspath)
        if topdir:
            return

        for self_td in self.topdir_list:
            if self_td.abspath in abspath:
                logging.info("subdirectory of %s : don't add" % self_td.abspath)
                return
        td_i = 0
        while td_i < len(self.topdir_list):
            self_td = self.topdir_list[td_i]
            if abspath in self_td.abspath:
                logging.info('removing %s because it is subdirectory of %s' % (self_td.abspath, abspath))
                del(self.topdir_list[td_i])
                td_i -= 1
            td_i += 1

        topdir = media_file.TopDirectory(self, abspath, comment)
        if (topdir):
            self.topdir_list.append(topdir)
        self.sync_topdir()

    def del_topdir(self, abspath):
        topdir = self.get_topdir_from_abspath(abspath)
        if not topdir:
            return

        self.topdir_list.remove(topdir)
        print(self.topdir_list)
        self.sync_topdir()

    def sync_topdir(self):
        db_list = db_utils.get_topdir_list(self.db_conn)
        db_list.sort(key=get_2nd_element)
        self.topdir_list.sort(key=get_abspath)

        ob_i = 0
        db_i = 0
        only_ob_list = []
        only_db_list = []
        while ob_i < len(self.topdir_list) and db_i < len(db_list):
            if self.topdir_list[ob_i].abspath > db_list[db_i][1]:
                only_db_list.append(db_list[db_i])
                db_i += 1
            elif self.topdir_list[ob_i].abspath < db_list[db_i][1]:
                only_ob_list.append(self.topdir_list[ob_i])
                ob_i += 1
            else:
                self.topdir_list[ob_i].db = db_list[db_i][0]
                ob_i += 1
                db_i += 1
        if ob_i < len(self.topdir_list):
            only_ob_list.extend(self.topdir_list[ob_i:])
        if db_i < len(db_list):
            only_db_list.extend(db_list[db_i:])

        for only_ob in only_ob_list:
            db_utils.add_topdir(self.db_conn, only_ob)
            only_ob.id = db_utils.get_topdir_id(self.db_conn, only_ob.abspath)
        for only_db in only_db_list:
            db_utils.del_topdir(self.db_conn, only_db[1])

    def sync_files(self, msg_cb=None):
        add_db_list = []
        del_db_list = []

        for topdir in self.topdir_list:
            msg_cb('processing %s' % topdir)
            fs_list = file_utils.get_topdir_filelist(topdir.abspath, self.extension_list)
            db_list = []
            for mf in self:
                if mf.topdir != topdir:
                    continue
                db_list.append(mf)

            fs_list.sort()
            db_list.sort(key=get_abspath)
            fs_i = 0
            db_i = 0
            only_fs_list = []
            only_db_list = []
            while fs_i < len(fs_list) and db_i < len(db_list):
                if fs_list[fs_i] > db_list[db_i].abspath:
                    only_db_list.append(db_list[db_i])
                    db_i += 1
                elif fs_list[fs_i] < db_list[db_i].abspath:
                    only_fs_list.append(fs_list[fs_i])
                    fs_i += 1
                else:
                    fs_i += 1
                    db_i += 1
            if fs_i < len(fs_list):
                only_fs_list.extend(fs_list[fs_i:])
            if db_i < len(db_list):
                only_db_list.extend(db_list[db_i:])

            for onlyfs in only_fs_list:
                if self.kill_thread:
                    return
                relpath = os.path.relpath(onlyfs, topdir.abspath)
                reldir = os.path.dirname(relpath)
                filename = os.path.basename(relpath)
                mf = media_file.MediaFile(self, topdir, reldir, filename)
                add_db_list.append(mf)
            for onlydb in only_db_list:
                if self.kill_thread:
                    return
                del_db_list.append(onlydb)

        total = len(add_db_list)
        count = 0
        while add_db_list:
            mf = add_db_list[0]
            mf.loadinfo()
            if msg_cb is not None:
                count += 1
                msg_cb('Adding : %s (%d/%d)' % (mf.filename, count, total))
            mf.create_thumbnails()
            if self.kill_thread:
                return
            if mf.thumbnails:
                cover_jpg = mf.thumbnails[int(len(mf.thumbnails) * 0.7)][1]
            db_utils.add_file_nocommit(self.db_conn, mf)
            self.db_conn.commit()
            db_utils.set_file_id(self.db_conn, mf)
            mf.save_thumbnails()
            db_utils.del_cover(self.db_conn, mf.id)
            db_utils.add_cover(self.db_conn, mf.id, cover_jpg)
            self.append(mf)
            del add_db_list[0]

        for mf in del_db_list:
            if self.kill_thread:
                return
            db_utils.del_file_nocommit(self.db_conn, mf)
            self.remove(mf)
            self.db_conn.commit()

        if msg_cb is not None:
            msg_cb('Sync Finished')

    def reload_files(self):
        db_file_list = db_utils.get_file_list(self.db_conn)

        mf_i = 0
        while mf_i < len(self):
            mf = self[mf_i]
            df_i = 0
            found = False
            while df_i < len(db_file_list):
                df = db_file_list[df_i]
                if mf.id == df[0]:
                    del(db_file_list[df_i])
                    df_i -= 1
                    found = True
                    break
                df_i += 1
            if not found:
                del(self[mf_i])
                mf_i -= 1
            mf_i += 1

        for df in db_file_list:
            topdir = self.get_topdir_from_id(df[1])
            mf = media_file.MediaFile(self, topdir, df[2], df[3])
            mf.load_dbtuple(df)
            mf.load_thumbnails()
            mf.get_coverjpg()
            del(mf.thumbnails)
            mf.thumbnails = None
            self.append(mf)

    def sync_database(self, msg_cb=None):
        self.sync_topdir()
        self.sync_files(msg_cb=msg_cb)

    def close_database(self):
        if self.db_conn:
            self.db_conn.close()


def print_msg(msg):
    print(msg)

if __name__ == '__main__':
    cat = Catalog('test.nmcat')
    cat.open_database()
    cat.del_topdir('Z:\\video\\on_yourmark')
    cat.del_topdir('Z:\\video\\NieA_7')
    cat.sync_database(msg_cb=print_msg)
    cat.close_database()