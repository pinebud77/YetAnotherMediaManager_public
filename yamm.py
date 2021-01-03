import logging
import sys
import wx
import tempfile
import requests
import urllib.request

from pyunpack import Archive

from settings import *
from MediaManager import MediaManager


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


def main():
    logging.basicConfig(format='%(asctime)-15s: %(message)s',
                        level=logging.DEBUG)

    check_ffmpeg()

    logging.info('loading settings from home directory')
    load_settings()

    app = wx.App()
    mm = MediaManager(None)
    mm.Show()
    app.MainLoop()

    logging.info('saving settings to home directory')
    store_settings()

    sys.exit()


if __name__ == '__main__':
    main()