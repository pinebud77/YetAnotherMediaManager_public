import logging
import sys
import getopt

from settings import *
from catalog import Catalog


VERSION_MAJOR = 0
VERSION_MINOR = 672


def wmain(yamm_file=None):
    import wx
    from MediaManager import MediaManager

    logging.info('loading settings from home directory')
    load_settings()

    app = wx.App()
    mm = MediaManager(None)
    mm.Show()
    if yamm_file:
        mm.file_to_open = yamm_file
        mm.open_timer.Start(100, oneShot=True)
    app.MainLoop()

    logging.info('saving settings to home directory')
    store_settings()

    sys.exit()


def print_msg(msg):
    logging.info(msg)


def cmain(yamm_file, topdirs, sync=False):
    logging.info('creating catalog file %s', yamm_file)
    if not yamm_file.endswith('.yamm'):
        logging.warning('yamm file extension is not .yamm. This file may not be open by GUI')
    yamm_file = os.path.abspath(yamm_file)
    if not sync:
        try:
            os.remove(yamm_file)
        except:
            pass
    logging.info('open catalog file : %s' % yamm_file)
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


def info_main(yamm_file):
    logging.debug('open catalog file : %s' % yamm_file)
    yamm_file = os.path.abspath(yamm_file)
    catalog = Catalog(db_abspath=yamm_file)
    catalog.open_database()

    for topdir in catalog.topdir_list:
        count = 0
        for mf in catalog:
            if mf.topdir == topdir:
                count += 1
        logging.info('\ninfo for topdir : %s (%d files)' % (topdir.abspath, count))
    logging.debug('closing catalog file : %s' % yamm_file)
    catalog.close_database()


def mod_main(yamm_file, origpart, newpart):
    logging.debug('open catalog file : %s' % yamm_file)
    yamm_file = os.path.abspath(yamm_file)
    catalog = Catalog(db_abspath=yamm_file)
    catalog.open_database()

    for topdir in catalog.topdir_list:
        if not (topdir.abspath.startswith(origpart)):
            continue
        print(topdir.abspath)
        trun_path = topdir.abspath.split(origpart)[1]
        newpath = os.path.join(newpart, trun_path)
        newpath = os.path.abspath(newpath)
        logging.info('modify %s -> %s' % (topdir.abspath, newpath))
        catalog.mod_topdir(topdir, newpath)

    logging.debug('closing catalog file : %s' % yamm_file)
    catalog.close_database()

def print_help():
    print("open GUI                     : yamm.exe something.yamm")
    print("sync catalog                 : yamm.exe -s yamm_file")
    print("sync catalog                 : yamm.exe --sync=yamm_file")
    print("create yamm file (overwrite) : yamm.exe -c yamm_file -a topdir1 -a topdir2 ...")
    print("create yamm file (overwrite) : yamm.exe --create=yamm_file --adddir=topdir1 --adddir=topdir2 ...")
    print("print yamm file info         : yamm.exe -i yamm_file")
    print("print yamm file info         : yamm.exe --info yamm_file")
    print("modify topdir                : yamm.exe -m yamm_file -o original_start -n new_start")
    print("modify topdir                : yamm.exe --mod=yamm_file --origpart=original_start --newpart=new_start")


if __name__ == '__main__':
    opts = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'm:o:n:i:dhc:a:qs:',
                                   ['debug',
                                    'help',
                                    'sync=',
                                    'create=',
                                    'adddir=',
                                    'quiet',
                                    'info=',
                                    'origpart=',
                                    'newpart=',
                                    'mod=',
                                    ])
    except getopt.GetoptError:
        print_help()
        sys.exit(-1)

    sync_file = None
    yamm_file = None
    quiet = False
    topdirs = []
    debug = False
    info_file = None
    origpart = None
    newpart = None
    mod_file = None
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
        elif opt in ('-i', '--info'):
            info_file = arg
        elif opt in ('-o', '--origpart'):
            origpart = arg
        elif opt in ('-n', '--newpart'):
            newpart = arg
        elif opt in ('-m', '--mod'):
            mod_file = arg

    if not yamm_file and args:
        yamm_file = args[0]

    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    elif debug:
        logging.basicConfig(format='%(asctime)-15s %(levelname)s : %(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s : %(message)s',
                            level=logging.INFO)

    #if platform.system() == 'Windows':
    #    check_ffmpeg()

    if sync_file:
        cmain(sync_file, None, sync=True)
    elif info_file:
        info_main(info_file)
    elif yamm_file and topdirs:
        cmain(yamm_file, topdirs)
    elif mod_file:
        mod_main(mod_file, origpart, newpart)
    else:
        wmain(yamm_file)
