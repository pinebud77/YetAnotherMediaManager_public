from distutils.core import setup
import py2exe

setup(windows=['yamm.py'],
      options = {
          'py2exe': {
              'includes':['appdirs',
                          'packaging',
                          'packaging.version',
                          'packaging.specifiers',
                          'packaging.requirements',
                          ],
              'excludes':['tk',
                         'tkinter',
                          ],
              #'bundle_files': 1,
              #'compressed': True,
              'dist_dir': 'YetAnotherMediaManager'
          },
      },
      #zipfile = None,
      )