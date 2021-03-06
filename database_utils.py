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
                                exclude BOOLEAN NOT NULL,
                                comment TEXT
                          );"""


def create_topdir_list(conn):
    c = conn.cursor()
    c.execute(sql_create_topdir_table)
    conn.commit()


sql_get_topdir = """SELECT id, path, comment, exclude FROM topdir;"""


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


sql_insert_topdir = """INSERT INTO topdir (path, comment, exclude)
                       VALUES(?, ?, ?);
                    """


def add_topdir(conn, topdir):
    c = conn.cursor()
    try:
        c.execute(sql_insert_topdir, (topdir.abspath, topdir.comment, topdir.exclude))
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


sql_update_topdir = """UPDATE topdir
                       SET path=?
                       WHERE path=?
                    """


def update_topdir(conn, oripath, newpath):
    c = conn.cursor()
    c.execute(sql_update_topdir, (newpath, oripath,))
    conn.commit()


sql_create_file_table = """CREATE TABLE IF NOT EXISTS file (
                                id integer PRIMARY KEY AUTOINCREMENT,
                                topdir_id INTEGER,
                                reldir TEXT NOT NULL,
                                filename TEXT NOT NULL,
                                size INTEGER,
                                time DATETIME,
                                lastplay DATETIME,
                                duration INTEGER,
                                comment TEXT,
                                width INTEGER,
                                height INTEGER,
                                CONSTRAINT fk_topdir_id
                                    FOREIGN KEY (topdir_id)
                                    REFERENCES topdir(id)
                                    ON DELETE CASCADE
                        );"""


def create_file_table(conn):
    c = conn.cursor()
    c.execute(sql_create_file_table)
    conn.commit()


sql_get_file = """SELECT id, topdir_id, reldir, filename, size, time, lastplay, duration, comment, width, height
                  FROM file
                  WHERE id >= ?;
               """


def get_file_list(conn, fileid=0):
    c = conn.cursor()
    c.execute(sql_get_file, (fileid,))
    return c.fetchall()


sql_update_file = """UPDATE file
                     SET topdir_id=?,
                         reldir=?,
                         filename=?,
                         size=?,
                         time=?,
                         lastplay=?,
                         duration=?,
                         comment=?,
                         width=?,
                         height=?
                     WHERE id=?;"""


def update_file(conn, mf):
    c = conn.cursor()
    c.execute(sql_update_file, (mf.topdir.id,
                                mf.reldir,
                                mf.filename,
                                mf.size,
                                mf.time,
                                mf.lastplay,
                                mf.duration,
                                mf.comment,
                                mf.width,
                                mf.height,
                                mf.id,
                                ))
    conn.commit()


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


sql_add_file = """INSERT INTO file (topdir_id, reldir, filename, size, time, lastplay, duration, comment, width, height)
                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
               """


def add_file_nocommit(conn, mf):
    c = conn.cursor()
    c.execute(sql_add_file, (mf.topdir.id, mf.reldir, mf.filename, mf.size,
                             mf.time, mf.lastplay, mf.duration, mf.comment,
                             mf.width, mf.height))


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


sql_get_thumbnails = """SELECT time, jpg, id
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


sql_del_thumbnails = """DELETE FROM thumbnail
                        WHERE file_id=?:
                     """


def del_thumbnails(conn, file_id):
    c = conn.cursor()
    c.execute(sql_del_thumbnails, (file_id,))
    conn.commit()


sql_get_thumbnail_from_id = """SELECT id, file_id, time, jpg
                               FROM thumbnail
                               WHERE id=?;"""


def get_thumbnail_from_id(conn, thumb_id):
    c = conn.cursor()
    c.execute(sql_get_thumbnail_from_id, (thumb_id,))
    rows = c.fetchall()
    return rows[0]


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


sql_get_cover_list = """SELECT *
                        FROM cover;"""


def get_cover_list(conn):
    c = conn.cursor()
    c.execute(sql_get_cover_list)
    return c.fetchall()


sql_get_cover = """SELECT cover
                   FROM cover
                   WHERE file_id=?;"""


def get_cover(conn, file_id):
    c = conn.cursor()
    c.execute(sql_get_cover, (file_id,))
    return c.fetchall()


sql_create_actor_table = """CREATE TABLE IF NOT EXISTS actor (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT UNIQUE,
                                picture BLOB,
                                bio TEXT,
                                comment TEXT);"""


def create_actor_table(conn):
    c = conn.cursor()
    c.execute(sql_create_actor_table)
    conn.commit()


sql_del_actor = """DELETE FROM actor
                   WHERE name=?;"""


def del_actor(conn, name):
    c = conn.cursor()
    c.execute(sql_del_actor, (name,))
    conn.commit()


sql_add_actor = """INSERT INTO actor (name, picture, bio, comment)
                   VALUES(?, ?, ?, ?);"""


def add_actor(conn, name, picture=None, bio=None, comment=None):
    c = conn.cursor()
    c.execute(sql_add_actor, (name, picture, bio, comment))
    conn.commit()


sql_modify_actor = """UPDATE actor
                      SET name=?, picture=?, bio=?, comment=?
                      WHERE name=?;"""


def modify_actor(conn, name, new_name, picture=None, bio=None, comment=None):
    c = conn.cursor()
    c.execute(sql_modify_actor, (new_name, picture, bio, comment, name,))
    conn.commit()


sql_get_actor = """SELECT name, picture, comment, bio, comment
                   FROM actor;"""


def get_actor_list(conn):
    c = conn.cursor()
    c.execute(sql_get_actor)
    return c.fetchall()


sql_get_actor_from_id = """SELECT name
                           FROM actor
                           WHERE id=?"""


def get_actor_from_id(conn, actor_id):
    c = conn.cursor()
    c.execute(sql_get_actor_from_id, (actor_id,))
    rows = c.fetchall()
    return rows[0][0]


sql_get_actorid_from_name = """SELECT id
                               FROM actor
                               WHERE name=?"""


def get_actorid_from_name(conn, name):
    c = conn.cursor()
    c.execute(sql_get_actorid_from_name, (name,))
    rows = c.fetchall()
    return rows[0][0]


sql_create_actorfile_table = """CREATE TABLE IF NOT EXISTS actorfile (
                                    actor_id INTEGER,
                                    file_id INTEGER,
                                    CONSTRAINT fk_actor_id
                                        FOREIGN KEY (actor_id)
                                        REFERENCES actor(id)
                                        ON DELETE CASCADE,
                                    CONSTRAINT fk_file_id
                                        FOREIGN KEY (file_id)
                                        REFERENCES file(id)
                                        ON DELETE CASCADE);"""


def create_actorfile_table(conn):
    c = conn.cursor()
    c.execute(sql_create_actorfile_table)
    conn.commit()


sql_add_actorfile = """INSERT INTO actorfile (actor_id, file_id)
                       VALUES(?, ?);"""


def add_actorfile(conn, actor_id, file_id):
    c = conn.cursor()
    c.execute(sql_add_actorfile, (actor_id, file_id,))
    conn.commit()


sql_del_actorfile = """DELETE FROM actorfile
                       WHERE actor_id=? AND file_id=?;"""


def del_actorfile(conn, actor_id, file_id):
    c = conn.cursor()
    c.execute(sql_del_actorfile, (actor_id, file_id,))
    conn.commit()


sql_get_actorfile = """SELECT actor_id, file_id
                       FROM actorfile;"""


def get_actorfile_list(conn):
    c = conn.cursor()
    c.execute(sql_get_actorfile)
    return c.fetchall()


sql_create_tag_table = """CREATE TABLE IF NOT EXISTS tag(
                                tag TEXT NOT NULL,
                                file_id INTEGER NOT NULL,
                                CONSTRAINT fk_file_id
                                    FOREIGN KEY (file_id)
                                    REFERENCES file(id)
                                    ON DELETE CASCADE);"""


def create_tag_table(conn):
    c = conn.cursor()
    c.execute(sql_create_tag_table)
    conn.commit()


sql_add_tag = """INSERT INTO tag (tag, file_id)
                 VALUES(?, ?);"""


def add_tag(conn, tag, file_id):
    c = conn.cursor()
    c.execute(sql_add_tag, (tag, file_id,))
    conn.commit()


sql_del_tag = """DELETE FROM tag
                 WHERE tag=? AND file_id=?;"""


def del_tag(conn, tag, file_id):
    c = conn.cursor()
    c.execute(sql_del_tag, (tag, file_id,))
    conn.commit()


sql_get_tag= """SELECT tag, file_id
                FROM tag;"""


def get_tag_list(conn):
    c = conn.cursor()
    c.execute(sql_get_tag)
    return c.fetchall()


sql_modify_tag = """UPDATE tag
                    SET tag=?
                    WHERE tag=? AND file_id=?"""


def modify_tag(conn, file_id, orig_tag, new_tag):
    c = conn.cursor()
    c.execute(sql_modify_tag, (new_tag, orig_tag, file_id,))
    conn.commit()


sql_create_favorite_table = """CREATE TABLE IF NOT EXISTS favorite(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                file_id INTEGER,
                                thumb_id INTEGER,
                                CONSTRAINT fk_file_id
                                    FOREIGN KEY (file_id)
                                    REFERENCES file(id)
                                    ON DELETE CASCADE,
                                CONSTRAINT fk_thumb_id
                                    FOREIGN KEY (thumb_id)
                                    REFERENCES thumbnail(id));"""


def create_favorite_table(conn):
    c = conn.cursor()
    c.execute(sql_create_favorite_table)
    conn.commit()


sql_add_favorite = """INSERT INTO favorite (file_id, thumb_id)
                      VALUES(?, ?);"""


def add_favorite(conn, file_id, thumb_id):
    c = conn.cursor()
    c.execute(sql_add_favorite, (file_id, thumb_id,))
    conn.commit()


sql_get_favorite_list = """SELECT id, file_id, thumb_id
                           FROM favorite;"""


def get_third_element(l):
    return l[2]


def get_favorite_list(conn):
    c = conn.cursor()
    c.execute(sql_get_favorite_list)
    rows = c.fetchall()
    rows.sort(key=get_third_element)
    return rows


sql_delete_favorite = """DELETE FROM favorite
                         WHERE id=?;"""


def del_favorite(conn, fav_id):
    c = conn.cursor()
    c.execute(sql_delete_favorite, (fav_id,))
    conn.commit()


sql_get_favorite_id = """SELECT id
                         FROM favorite
                         WHERE file_id=? AND thumb_id=?;"""


def get_favorite_id(conn, file_id, thumb_id):
    c = conn.cursor()
    c.execute(sql_get_favorite_id, (file_id, thumb_id,))
    rows = c.fetchall()
    return rows[0][0]