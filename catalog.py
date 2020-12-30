#!/usr/bin/env python3
import os
import os.path
import logging
import sqlite3
import datetime

import media_file
import database_utils as db_utils
import file_utils as file_utils


MAJOR_VERSION = 0
MINOR_VERSION = 1
DEFAULT_FILE_EXT = ['mkv', 'avi', 'mp4', 'asf', 'wmv']

FILTER_SORT_NONE = 0
FILTER_SORT_FILENAME = 1
FILTER_SORT_TIME = 2
FILTER_SORT_LASTPLAY = 3
FILTER_SORT_DURATION = 4

def filter_sort_filename(mf):
    return mf.filename

def filter_sort_time(mf):
    return mf.time

def filter_sort_lastplay(mf):
    if mf.lastplay:
        return datetime.datetime.strptime(mf.lastplay, '%Y-%m-%d %H:%M:%S.%f')
    else:
        return datetime.datetime.min

def filter_sort_duration(mf):
    return mf.duration

logging.basicConfig(level=logging.DEBUG)

def get_abspath(topdir):
    return topdir.abspath


def get_2nd_element(list_element):
    return list_element[1]


def get_rel_path(media_file):
    return os.path.join(media_file.reldir, media_file.filename)


class Catalog(list):
    def __init__(self, db_abspath, extension_list=DEFAULT_FILE_EXT):
        self.filepath = db_abspath
        self.topdir_list = []
        self.db_conn = None
        self.extension_list = extension_list
        self.kill_thread = False

    def open_database(self):
        try:
            self.db_conn = sqlite3.connect(self.filepath)
            logging.debug('sqlite3 version: ' + sqlite3.version)
        except Exception as e:
            logging.error('failed to open database file: %s' % self.filepath)
            logging.error('exception: %s' % e)
            return None

        # get DB version
        # TODO: add migration code based on DB and APP version diff
        ver_tuple = db_utils.get_app_version(self.db_conn)
        if ver_tuple:
            logging.debug('database version = %d.%d' % (ver_tuple[0], ver_tuple[1]))
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

        #load cover table
        db_utils.create_cover_table(self.db_conn)
        db_cover_list = db_utils.get_cover(self.db_conn)
        for dc in db_cover_list:
            file_id = dc[1]
            jpg = dc[2]
            for mf in self:
                if mf.id == file_id:
                    mf.cover = jpg
                    break

    def filter(self, sort=FILTER_SORT_NONE, ascend=True, actors=[], tags=[], stars=None):
        l = []
        for mf in self:
            l.append(mf)

        if sort == FILTER_SORT_FILENAME:
            l.sort(key=filter_sort_filename, reverse=(not ascend))
        elif sort == FILTER_SORT_TIME:
            l.sort(key=filter_sort_time, reverse=(not ascend))
        elif sort == FILTER_SORT_LASTPLAY:
            l.sort(key=filter_sort_lastplay, reverse=(not ascend))
        elif sort == FILTER_SORT_DURATION:
            l.sort(key=filter_sort_duration, reverse=(not ascend))

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
        while True:
            if ob_i == len(self.topdir_list) or db_i == len(db_list):
                break
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

    def sync_files(self, file_cb=None):
        add_db_list = []
        del_db_list = []

        for topdir in self.topdir_list:
            logging.debug('processing %s' % topdir)
            fs_list = file_utils.get_topdir_filelist(topdir.abspath, self.extension_list)
            db_list = []
            for mf in self:
                if mf.topdir != topdir:
                    continue
                db_list.append(mf)

            fs_i = 0
            db_i = 0
            only_fs_list = []
            only_db_list = []
            while True:
                if fs_i == len(fs_list) or db_i == len(db_list):
                    break
                if fs_list[fs_i] > db_list[db_i].abspath():
                    only_db_list.append(db_list[db_i])
                    db_i += 1
                elif fs_list[fs_i] < db_list[db_i].abspath():
                    only_fs_list.append(fs_list[fs_i])
                    fs_i += 1
                else:
                    fs_i += 1
                    db_i += 1
            if fs_i < len(fs_list):
                only_fs_list.extend(fs_list[fs_i:])
            if db_i < len(db_list):
                only_db_list.extend(db_list[db_i:])

            logging.debug('only on fs:')
            logging.debug(only_fs_list)
            logging.debug('only on DB:')
            logging.debug(only_db_list)

            for onlyfs in only_fs_list:
                relpath = os.path.relpath(onlyfs, topdir.abspath)
                reldir = os.path.dirname(relpath)
                filename = os.path.basename(relpath)
                mf = media_file.MediaFile(self, topdir, reldir, filename)
                mf.loadinfo()
                add_db_list.append(mf)
            for onlydb in only_db_list:
                del_db_list.append(onlydb)

        total = len(add_db_list)
        count = 0
        while add_db_list:
            mf = add_db_list[0]
            logging.debug('adding: %s' % mf.abspath())
            if self.kill_thread:
                return
            db_utils.add_file_nocommit(self.db_conn, mf)
            self.db_conn.commit()
            db_utils.set_file_id(self.db_conn, mf)
            mf.load_thumbnails(create=True)
            self.append(mf)
            if file_cb is not None:
                count += 1
                percent = int(count / total * 100)
                file_cb(mf, percent)
            del add_db_list[0]

        for mf in del_db_list:
            if self.kill_thread:
                return
            db_utils.del_file_nocommit(self.db_conn, mf)
            self.remove(mf)
            self.db_conn.commit()

        if file_cb is not None:
            file_cb(None, 100)

    def reload_files(self):
        db_file_list = db_utils.get_file_list(self.db_conn)

        mf_i = 0
        while True:
            if mf_i == len(self):
                break
            mf = self[mf_i]
            df_i = 0
            found = False
            while True:
                if df_i == len(db_file_list):
                    break
                df = db_file_list[df_i]
                topdir = self.get_topdir_from_id(df[1])
                df_abs = os.path.join(topdir.abspath, df[2], df[3])
                if mf.abspath() == df_abs:
                    del(db_file_list[df_i])
                    df_i -= 1
                    found = True
                df_i += 1
            if not found:
                del(self[mf_i])
                mf_i -= 1
            mf_i += 1

        for df in db_file_list:
            topdir = self.get_topdir_from_id(df[1])
            mf = media_file.MediaFile(self, topdir, df[2], df[3])
            mf.load_dbtuple(df)
            mf.load_thumbnails(create=False)
            self.append(mf)

    def sync_database(self, file_cb=None):
        self.sync_topdir()
        self.sync_files(file_cb=file_cb)

    def load_database(self):
        pass

    def close_database(self):
        if self.db_conn:
            self.db_conn.close()

    def add_file(self, relpath):
        pass

    def remove_file(self, relpath):
        pass

    def sort_files(self):
        pass

    def get_files_with_tag(self, tag):
        pass

    def get_files_with_category(self, tag):
        pass


def print_percent(percent):
    print(percent)

def print_path(mf):
    print(mf.abspath())

if __name__ == '__main__':
    cat = Catalog('test.nmcat')
    cat.open_database()
    cat.del_topdir('Z:\\video\\on_yourmark')
    cat.del_topdir('Z:\\video\\NieA_7')
    cat.sync_database(file_cb=print_path)
    cat.close_database()