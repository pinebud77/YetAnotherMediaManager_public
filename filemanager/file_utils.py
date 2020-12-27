#!/usr/bin/env python3

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