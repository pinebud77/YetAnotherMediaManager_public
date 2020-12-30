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


logging.basicConfig(level=logging.INFO)


def in_extension_list(filename, ext_list):
    for ext in ext_list:
        if filename.lower().endswith(ext):
            return True

    return False

def get_topdir_filelist(topdir, ext_list):
    new_filelist = []

    for dirpath, dirnames, filenames in os.walk(topdir):
        for filename in filenames:
            if not in_extension_list(filename, ext_list):
                continue

            filepath = os.path.join(dirpath, filename)
            abspath = os.path.abspath(filepath)
            new_filelist.append(abspath)

            logging.debug('file found: %s' % abspath)

    return new_filelist