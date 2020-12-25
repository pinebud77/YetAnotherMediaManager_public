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

def get_fs_filelist(topdir_list, ext_list):
    new_filelist = []

    for topdirpath in topdir_list:
        for dirpath, dirnames, filenames in os.walk(topdirpath):
            for filename in filenames:
                if not in_extension_list(filename, ext_list):
                    continue

                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, topdirpath)
                new_filelist.append(relpath)

                logging.debug('file found: %s' % relpath)

    new_filelist.sort()

    return new_filelist