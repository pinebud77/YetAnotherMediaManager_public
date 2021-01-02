from distutils.core import setup
import py2exe

import os.path
import imageio_ffmpeg

ffmpeg_location = imageio_ffmpeg.__file__
ffmpeg_location = os.path.join(os.path.dirname(ffmpeg_location), 'binaries', 'ffmpeg.exe')

setup(windows=['YetAnotherMediaManager.pyw'],
      options = {
          'py2exe': {
              'includes':['appdirs',
                          'packaging',
                          'packaging.version',
                          'packaging.specifiers',
                          'packaging.requirements',
                          'moviepy'
                          ],
              'excludes':['tk',
                         'tkinter',
                          ],
              #'bundle_files': 1,
              #'compressed': True,
          },
      },
      data_files = [('ffmpeg', [ffmpeg_location,],)],
      #zipfile = None,
      )