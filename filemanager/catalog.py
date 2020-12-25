#!/usr/bin/env python3
import os
import os.path
import logging
import sqlite3

import media_file
import database_utils as db_utils
import file_utils as file_utils


MAJOR_VERSION = 0
MINOR_VERSION = 1
DEFAULT_FILE_EXT = ['mkv', 'avi', 'mp4', 'asf', 'wmv']


def get_abspath(topdir):
    return topdir.abspath


def get_2nd_element(list_element):
    return list_element[1]


def get_rel_path(media_file):
    return media_file.relpath


class Catalog(list):
    def __init__(self, db_abspath, topdir_list=[], extension_list=DEFAULT_FILE_EXT):
        self.filepath = db_abspath
        self.topdir_list = topdir_list
        self.db_conn = None
        self.extension_list = extension_list

    def open_database(self):
        try:
            self.db_conn = sqlite3.connect(self.filepath)
            logging.info('sqlite3 version: ' + sqlite3.version)
        except Exception as e:
            logging.error('failed to open database file: %s' % self.filepath)
            logging.error('exception: %s' % e)
            return None

        ver_tuple = db_utils.get_app_version(self.db_conn)
        if ver_tuple:
            logging.info('database version = %d.%d' % (ver_tuple[0], ver_tuple[1]))
        elif not ver_tuple or ver_tuple[0] != MAJOR_VERSION or ver_tuple[1] != MINOR_VERSION:
            db_utils.set_app_version(self.db_conn, MAJOR_VERSION, MINOR_VERSION)

        db_utils.create_topdir_list(self.db_conn)
        db_topdir_list = db_utils.get_topdir_list(self.db_conn)
        db_topdir_list.sort(key=get_2nd_element)
        for db_td in db_topdir_list:
            td = media_file.TopDirectory(self, db_td[1], db_td[2])
            td.db_id = db_td[0]
            self.topdir_list.append(td)

    def add_topdir(self, abspath, comment=None):
        topdir = media_file.TopDirectory(self, abspath, comment)
        if (topdir):
            self.topdir_list.append(topdir)
        self.sync_topdir()

    def sync_topdir(self):
        db_topdir_list = db_utils.get_topdir_list(self.db_conn)
        db_topdir_list.sort(key=get_2nd_element)
        self.topdir_list.sort(key=get_abspath)

        ob_i = 0
        db_i = 0
        only_ob_list = []
        only_db_list = []
        while True:
            if ob_i == len(self.topdir_list) or db_i == len(db_topdir_list):
                break
            if self.topdir_list[ob_i].abspath > db_topdir_list[db_i][1]:
                only_db_list.append(db_topdir_list[db_i])
                db_i += 1
            elif self.topdir_list[ob_i].abspath < db_topdir_list[db_i][1]:
                only_ob_list.append(self.topdir_list[ob_i])
                ob_i += 1
            else:
                self.topdir_list[ob_i].db_id = db_topdir_list[db_i][0]
                ob_i += 1
                db_i += 1
        if ob_i < len(self.topdir_list):
            only_ob_list.extend(self.topdir_list[ob_i:])
        if db_i < len(db_topdir_list):
            only_db_list.extend(db_topdir_list[db_i])

        logging.info('only on object:')
        logging.info(only_ob_list)
        logging.info('only on db:')
        logging.info(only_db_list)

        for only_ob in only_ob_list:
            db_utils.add_topdir(self.db_conn, only_ob.abspath, only_ob.comment)
        for only_db in only_db_list:
            td = media_file.TopDirectory(self, only_db[1], only_db[2])
            td.db_id = only_db[0]
            self.topdir_list.append(td)

    def sync_files(self):
        fs_list = file_utils.get_fs_filelist(self.topdir_list, self.extension_list)

    def sync_database(self):
        fs_list = file_utils.get_fs_filelist(self.topdir_list, self.extension_list)

        self.sort(key=get_rel_path)

        fs_i = 0
        self_i = 0
        only_self_list = []
        only_fs_list = []

        while True:
            if fs_i == len(fs_list) or self_i == len(self):
                break

            if self[self_i].relpath > fs_list[fs_i]:
                only_fs_list.append(fs_list[fs_i])
                fs_i += 1
            elif self[self_i].relpath < fs_list[fs_i]:
                only_self_list.append(self[self_i])
                self_i += 1
            else:
                fs_i += 1
                self_i += 1

        if fs_i < len(fs_list):
            only_fs_list.extend(fs_list[fs_i:])
        if self_i < len(self):
            only_self_list.extend(self[self_i:])

        #logging.info('only on filesystem: %d' % len(only_fs_list))
        #logging.info(only_fs_list)
        #logging.info('only in db:')
        #logging.info(only_self_list)

        for fs_file in only_fs_list:
            db_utils.add_me

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    cat = Catalog('C:\\Users\\pineb\\Desktop\\python\\test.db')
    cat.open_database()
    cat.add_topdir("\\\\192.168.25.25\\administrator\\tt\\.t\\Administrator\\Recycled\\download")
    cat.sync_topdir()
    #cat.sync_database()
    cat.close_database()