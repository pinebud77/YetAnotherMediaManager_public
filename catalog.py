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
import glob
import logging
import sqlite3
import datetime
import re
import threading
import multiprocessing

from settings import *
import media_file
import database_utils as db_utils


DB_MAJOR_VERSION = 0
DB_MINOR_VERSION = 2


def get_abspath(topdir):
    return topdir.abspath


def get_2nd_element(list_element):
    return list_element[1]


def get_rel_path(media_file):
    return os.path.join(media_file.reldir, media_file.filename)


class DbVersionException(Exception):
    pass


class Catalog(list):
    def __init__(self, db_abspath, extension_list=DEF_FILE_EXTENSION):
        super(Catalog, self).__init__()

        self.filepath = db_abspath
        self.topdir_list = []
        self.tag_list = []
        self.actor_list = []
        self.db_conn = None
        self.extension_list = extension_list
        self.kill_thread = False
        self.thread_files = []

    def open_database(self):
        try:
            self.db_conn = sqlite3.connect(self.filepath)
            logging.info('sqlite3 version: ' + sqlite3.version)
        except Exception as e:
            logging.error('failed to open database file: %s' % self.filepath)
            logging.error('exception: %s' % e)
            return None

        # get DB version
        ver_tuple = db_utils.get_app_version(self.db_conn)
        if ver_tuple:
            logging.info('database version = %d.%d' % (ver_tuple[0], ver_tuple[1]))
            if ver_tuple[0] != DB_MAJOR_VERSION or ver_tuple[1] != DB_MINOR_VERSION:
                raise DbVersionException('Catalog version updated')

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
            actor_name = db_utils.get_actor_from_id(self.db_conn, db_actorfile[0])
            mf.actor_list.append(actor_name)

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

        #load favorite table
        db_utils.create_favorite_table(self.db_conn)
        db_favorite_list = db_utils.get_favorite_list(self.db_conn)
        for fav in db_favorite_list:
            file_id = fav[1]
            thumb_id = fav[2]
            for mf in self:
                if mf.id != file_id:
                    continue
                thumb = db_utils.get_thumbnail_from_id(self.db_conn, thumb_id)
                fav = media_file.Favorite(mf, thumb[2], fav[0], thumb_id)
                fav.jpg = thumb[3]
                mf.favorites.append(fav)

    def add_actor(self, name):
        if name in self.actor_list:
            return
        db_utils.add_actor(self.db_conn, name)
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

    def add_topdir(self, abspath, comment=None, exclude=False):
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

        topdir = media_file.TopDirectory(self, abspath, comment, exclude)
        if (topdir):
            self.topdir_list.append(topdir)
        self.sync_topdir()

    def del_topdir(self, abspath):
        topdir = self.get_topdir_from_abspath(abspath)
        if not topdir:
            return

        self.topdir_list.remove(topdir)
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

    def in_extension_list(self, filename, ext_list):
        for ext in ext_list:
            if filename.lower().endswith(ext):
                return True
        return False

    def get_dir_filelist(self, topdir, ext_list, msg_cb=None):
        msg_cb('processing directory : %s' % topdir)

        new_filelist = []
        try:
            names = glob.glob(os.path.join(topdir, '*'))
        except re.error:
            return []

        for name in names:
            if self.kill_thread:
                return []
            path = os.path.join(topdir, name)
            abspath = os.path.abspath(path)
            if os.path.isfile(abspath):
                if not self.in_extension_list(name, ext_list):
                    continue
                new_filelist.append(abspath)
            if os.path.isdir(abspath):
                add_files = self.get_dir_filelist(path, ext_list, msg_cb=msg_cb)
                new_filelist.extend(add_files)

        return new_filelist

    def sync_files(self, msg_cb=None):
        add_db_list = []
        del_db_list = []

        for topdir in self.topdir_list:
            if not os.path.exists(topdir.abspath):
                logging.warning('topdir is not accessible.. ignoring..')
                msg_cb('topdir is not accessible.. ignoring %s' % topdir.abspath)
                continue
            fs_list = self.get_dir_filelist(topdir.abspath, self.extension_list, msg_cb=msg_cb)
            if self.kill_thread:
                return

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

        for mf in del_db_list:
            if self.kill_thread:
                return
            db_utils.del_file_nocommit(self.db_conn, mf)
            self.remove(mf)
            self.db_conn.commit()

        cpu_count = multiprocessing.cpu_count()
        if cpu_count > 4:
            cpu_count = 4
        total = len(add_db_list)
        count = 0
        thread_list = []
        while add_db_list:
            mf = add_db_list[0]
            del add_db_list[0]
            count += 1
            t = threading.Thread(target=self.sync_thread_func, args=(mf,))
            t.start()
            thread_list.append(t)
            if count % cpu_count and count < total:
                continue
            msg_cb('Adding files : %s (%d/%d)' % (mf.filename, count, total))

            for t in thread_list:
                t.join()
            thread_list = []

            if self.kill_thread:
                return

            for mf in self.thread_files:
                if mf.thumbnails:
                    cover_jpg = mf.thumbnails[int(len(mf.thumbnails) * 0.7)][1]
                db_utils.add_file_nocommit(self.db_conn, mf)
                self.db_conn.commit()
                db_utils.set_file_id(self.db_conn, mf)
                if mf.thumbnails:
                    mf.save_thumbnails()
                    db_utils.del_cover(self.db_conn, mf.id)
                    db_utils.add_cover(self.db_conn, mf.id, cover_jpg)
                self.append(mf)
            self.thread_files = []

        if msg_cb is not None:
            msg_cb('Sync Finished')

    def sync_thread_func(self, mf):
        mf.loadinfo()
        if self.kill_thread:
            return
        mf.create_thumbnails()
        self.thread_files.append(mf)

    def del_file(self, mf):
        if mf not in self:
            return

        os.remove(mf.abspath)
        self.remove(mf)
        db_utils.del_file_nocommit(self.db_conn, mf)
        self.db_conn.commit()

    def reload_files(self):
        min_fileid = 0
        for mf in self:
            if mf.id > min_fileid:
                max_fileid = mf.id
        db_file_list = db_utils.get_file_list(self.db_conn, min_fileid)

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

    def mod_topdir(self, topdir, newpath):
        newpath = os.path.abspath(newpath)
        db_utils.update_topdir(self.db_conn, topdir.abspath, newpath)
        topdir.abspath = newpath

    def modify_actor(self, orig_name, new_name):
        if orig_name not in self.actor_list:
            return False
        if new_name in self.actor_list:
            return False

        db_utils.modify_actor(self.db_conn, orig_name, new_name)
        for mf in self:
            mf.modify_actor(orig_name, new_name)
        self.actor_list.remove(orig_name)
        self.actor_list.append(new_name)
        self.actor_list.sort()
        return True

    def modify_tag(self, orig_tag, new_tag):
        if orig_tag not in self.tag_list:
            return False
        if new_tag in self.tag_list:
            return False

        for mf in self:
            mf.modify_tag(orig_tag, new_tag)
        self.tag_list.remove(orig_tag)
        self.tag_list.append(new_tag)
        self.tag_list.sort()
        return True

    def close_database(self):
        if self.db_conn:
            self.db_conn.close()


