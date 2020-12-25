#!/usr/bin/env python3

import sqlite3
import logging


sql_get_version = """SELECT major, minor
                     FROM version
                     WHERE id=0;"""

def get_app_version(conn):
    c = conn.cursor()

    try:
        c.execute(sql_get_version)
        rows = c.fetchall()
    except Exception as e:
        logging.error(e)
        return None

    if rows:
        return (rows[0][0], rows[0][1])

    return None


sql_create_version_table = """CREATE TABLE IF NOT EXISTS version (
                                id integer PRIMARY KEY,
                                major integer NOT NULL,
                                minor integer NOT NULL
                            );"""

sql_update_version = """UPDATE version
                        SET major=?, minor=?
                        WHERE id = 0;
                     """

sql_insert_version = """INSERT INTO version (id, major, minor)
                        VALUES(0, ?, ?);
                     """

def set_app_version(conn, major, minor):
    c = conn.cursor()

    c.execute(sql_create_version_table)

    if get_app_version(conn):
        c.execute(sql_update_version, (major, minor,))
    else:
        c.execute(sql_insert_version, (major, minor,))

    conn.commit()


sql_create_topdir_table = """CREATE TABLE IF NOT EXISTS topdir (
                                id integer PRIMARY KEY AUTOINCREMENT,
                                path TEXT UNIQUE NOT NULL,
                                comment TEXT
                          );"""

def create_topdir_list(conn):
    c = conn.cursor()
    c.execute(sql_create_topdir_table)
    conn.commit()


sql_get_topdir = """SELECT id, path, comment FROM topdir;"""

def get_topdir_list(conn):
    c = conn.cursor()
    c.execute(sql_get_topdir)
    rows = c.fetchall()

    return rows


sql_insert_topdir = """INSERT INTO topdir (path, comment)
                       VALUES(?, ?);
                    """

def add_topdir(conn, abspath, comment):
    c = conn.cursor()
    try:
        c.execute(sql_insert_topdir, (abspath, comment,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass


sql_delete_topdir = """DELETE FROM topdir
                       WHERE abspath=?;
                    """

def del_topdir(conn, abspath):
    c = conn.cursor()
    c.execute(sql_delete_topdir, (abspath,))
    conn.commit()


sql_create_file_table = """CREATE TABLE IF NOT EXISTS file (
                                id integer PRIMARY KEY AUTOINCREMENT,
                                relpath TEXT UNIQUE NOT NULL,
                                STARS integer,
                                comment TEXT
                        );"""
