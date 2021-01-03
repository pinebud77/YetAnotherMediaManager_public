import logging
import sys
import getopt
import wx
import tempfile
import requests
import urllib.request

from pyunpack import Archive

from settings import *
from catalog import Catalog


def check_ffmpeg():
    if os.path.exists(os.path.join(tempfile.gettempdir(), 'ffmpeg.exe')):
        logging.info('ffmpeg.exe exists, no need to download')
        return
    logging.info('ffmpeg.exe does not exist, downloading ffmpeg to the temp directory')
    url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z'
    r = requests.get(url)
    filename = r.url.split('/')[-1]
    tfile = os.path.join(tempfile.gettempdir(), filename)
    tfilename = os.path.basename(tfile)
    tfile_noext = '.'.join(tfile.split('.')[:-1])
    urllib.request.urlretrieve(url, tfile)
    Archive(tfile).extractall(tempfile.gettempdir())
    os.rename(os.path.join(tfile_noext, 'bin', 'ffmpeg.exe'),
              os.path.join(tempfile.gettempdir(), 'ffmpeg.exe'))


def wmain(yamm_file=None):
    check_ffmpeg()

    logging.info('loading settings from home directory')
    load_settings()

    app = wx.App()
    from MediaManager import MediaManager
    mm = MediaManager(None)
    mm.open_catalog(yamm_file)
    mm.Show()
    app.MainLoop()

    logging.info('saving settings to home directory')
    store_settings()

    sys.exit()


def print_msg(msg):
    logging.info(msg)


def cmain(yamm_file, topdirs, sync=False):
    check_ffmpeg()

    logging.info('creating catalog file %s', yamm_file)
    if not yamm_file.endswith('.yamm'):
        logging.warning('yamm file extension is not .yamm. This file may not be open by GUI')
    yamm_file = os.path.abspath(yamm_file)
    if not sync:
        try:
            os.remove(yamm_file)
        except:
            pass
    logging.info('open catalog file %s', yamm_file)
    catalog = Catalog(db_abspath=yamm_file)
    catalog.open_database()
    if not sync:
        for topdir in topdirs:
            topdir = os.path.abspath(topdir)
            if not os.path.exists(topdir):
                logging.error('topdir not found in the filesystem : %s' % topdir)
            logging.info('adding topdir : %s' % topdir)
            catalog.add_topdir(topdir)
    logging.info('sync catalog file %s', yamm_file)
    catalog.sync_database(msg_cb=print_msg)
    logging.info('close catalog file %s', yamm_file)
    catalog.close_database()

    sys.exit()


def print_help():
    print("open GUI                     : yamm.exe something.yamm")
    print("sync catalog                 : yamm.exe -s yamm_file")
    print("sync catalog                 : yamm.exe --sync=yamm_file")
    print("create yamm file (overwrite) : yamm.exe -c yamm_file -a topdir1 -a topdir2 ...")
    print("create yamm file (overwrite) : yamm.exe --create=yamm_file --adddir=topdir1 --adddir=topdir2 ...")


if __name__ == '__main__':
    opts = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dhc:a:qs:', ['debug', 'help', 'sync=', 'create=', 'adddir=', 'quiet'])
    except getopt.GetoptError:
        print_help()
        sys.exit(-1)

    sync_file = None
    yamm_file = None
    quiet = False
    topdirs = []
    debug = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_help()
            sys.exit(0)
        elif opt in ('-c', '--create'):
            yamm_file = arg
        elif opt in ('-a', '--adddir'):
            topdirs.append(arg)
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-s', '--sync'):
            sync_file = arg
        elif opt in ('-d', '--debug'):
            debug = True

    if not yamm_file and args:
        yamm_file = args[0]

    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    elif debug:
        logging.basicConfig(format='%(levelname)s : %(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s : %(message)s',
                            level=logging.INFO)

    if sync_file:
        cmain(sync_file, None, sync=True)
    elif yamm_file and topdirs:
        cmain(yamm_file, topdirs)
    else:
        wmain(yamm_file)
