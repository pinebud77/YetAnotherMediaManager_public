#!/usr/bin/env python3

import sqlite3
import logging


sql_enable_fk = """PRAGMA foreign_keys = ON;"""

def enable_foreign_key(conn):
    c = conn.cursor()
    c.execute(sql_enable_fk)


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
    return c.fetchall()


sql_get_topdir_id = """SELECT id
                       FROM topdir
                       WHERE path=?;
                    """

def get_topdir_id(conn, abspath):
    c = conn.cursor()
    c.execute(sql_get_topdir_id, (abspath,))
    rows = c.fetchall()

    if not rows:
        return None
    return rows[0][0]

sql_insert_topdir = """INSERT INTO topdir (path, comment)
                       VALUES(?, ?);
                    """

def add_topdir(conn, topdir):
    c = conn.cursor()
    try:
        c.execute(sql_insert_topdir, (topdir.abspath, topdir.comment,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass


sql_delete_topdir = """DELETE FROM topdir
                       WHERE path=?;
                    """

def del_topdir(conn, abspath):
    c = conn.cursor()
    c.execute(sql_delete_topdir, (abspath,))
    conn.commit()


sql_create_file_table = """CREATE TABLE IF NOT EXISTS file (
                                id integer PRIMARY KEY AUTOINCREMENT,
                                topdir_id INTEGER,
                                reldir TEXT NOT NULL,
                                filename TEXT NOT NULL,
                                stars INTEGER,
                                size INTEGER,
                                time DATETIME,
                                lastplay DATETIME,
                                duration INTEGER,
                                comment TEXT,
                                CONSTRAINT fk_topdir_id
                                    FOREIGN KEY (topdir_id)
                                    REFERENCES topdir(id)
                                    ON DELETE CASCADE
                        );"""

def create_file_table(conn):
    c = conn.cursor()
    c.execute(sql_create_file_table)
    conn.commit()


sql_get_file = """SELECT id, topdir_id, reldir, filename, stars, size, time, lastplay, duration, comment
                  FROM file;
               """

def get_file_list(conn):
    c = conn.cursor()
    c.execute(sql_get_file)
    return c.fetchall()


sql_get_file_id = """SELECT id
                     FROM file
                     WHERE topdir_id=? and reldir=? and filename=?;
                  """

def set_file_id(conn, mf):
    c = conn.cursor()
    c.execute(sql_get_file_id, (mf.topdir.id, mf.reldir, mf.filename,))
    rows = c.fetchall()
    if not rows:
        return
    mf.id = rows[0][0]


sql_add_file = """INSERT INTO file (topdir_id, reldir, filename, stars, size, time, lastplay, duration, comment)
                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);
               """

def add_file_nocommit(conn, mf):
    c = conn.cursor()
    c.execute(sql_add_file, (mf.topdir.id, mf.reldir, mf.filename, mf.stars, mf.size,
                             mf.time, mf.lastplay, mf.duration, mf.comment,))


sql_del_file = """DELETE FROM file
                  WHERE id=?;
               """

def del_file_nocommit(conn, mf):
    c = conn.cursor()
    c.execute(sql_del_file, (mf.id,))


sql_create_thumbnail_table = """CREATE TABLE IF NOT EXISTS thumbnail (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    file_id INTEGER,
                                    time INTEGER,
                                    jpg BLOB,
                                    CONSTRAINT fk_file_id
                                        FOREIGN KEY (file_id)
                                        REFERENCES file(id)
                                        ON DELETE CASCADE
                             );"""

def create_thumbnail_table(conn):
    c = conn.cursor()
    c.execute(sql_create_thumbnail_table)
    conn.commit()


sql_add_thumbnail = """INSERT INTO thumbnail (file_id, time, jpg)
                       VALUES(?, ?, ?);
                    """

def add_thumbnails(conn, file_id, thumb_list):
    c = conn.cursor()
    for thumb in thumb_list:
        time = thumb[0]
        jpg = thumb[1]
        c.execute(sql_add_thumbnail, (file_id, time, jpg,))
    conn.commit()


sql_get_thumbnails = """SELECT time, jpg
                        FROM thumbnail
                        WHERE file_id=?;
                     """

def get_first_element(arr):
    return arr[0]

def get_thumbnails(conn, file_id):
    c = conn.cursor()
    c.execute(sql_get_thumbnails, (file_id,))
    rows = c.fetchall()
    rows.sort(key=get_first_element)
    return rows


sql_create_cover_table = """CREATE TABLE IF NOT EXISTS cover (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                file_id INTEGER UNIQUE,
                                cover BLOB,
                                CONSTRAINT fk_file_id
                                    FOREIGN KEY (file_id)
                                    REFERENCES file(id)
                                    ON DELETE CASCADE
                          );"""

def create_cover_table(conn):
    c = conn.cursor()
    c.execute(sql_create_cover_table)
    conn.commit()


sql_del_cover = """DELETE FROM cover
                   WHERE file_id=?;"""

def del_cover(conn, file_id):
    c = conn.cursor()
    c.execute(sql_del_cover, (file_id,))
    conn.commit()


sql_add_cover = """INSERT INTO cover (file_id, cover)
                   VALUES(?, ?);"""

def add_cover(conn, file_id, jpg):
    c = conn.cursor()
    c.execute(sql_add_cover, (file_id, jpg,))
    conn.commit()


sql_get_cover = """SELECT *
                   FROM cover"""

def get_cover(conn):
    c = conn.cursor()
    c.execute(sql_get_cover)
    return c.fetchall()

