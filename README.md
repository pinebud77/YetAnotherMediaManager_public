Yet Another Media Manager
=========================

This is Video clip file manager. This is my personal project..

Download Windows executable or tagged version
* https://github.com/pinebud77/YetAnotherMediaManager_public/releases/latest

Features
* File addition in background through thread
* File management with database (sqlite3)
* Video thumbnail image generation
* Selection of cover image from thumbnails
* Tagging by actor names and tags
* Filter by actor or tags
* Save/load configuration file : location - user_home_dir/yamm.settings (JSON format)
* Saving thumbnail to JPG file
* Command-line interface for indexing

Command Line Arguments
* -h (--help) : print usage
* -c (--create=) : create yamm catalog file
* -a (--adddir=) : add directory when creating yamm catalog
* -s (--sync=) : sync yamm catalog file
* -d (--debug) : print debug messages
* -q (--quiet) : print no message

Planned Features
* Platform Independent code
* Creating GIFs from thumbnails
* File deletion inside app
* Action GIF on focus on file

Dependencies
* PotPlayer as media player : https://potplayer.daum.net/
* moviepy library : pip install movipy
* wxpython GUI library : pip install wxpython


Problems
* bugs!!
* DB schema is not fixed yet
* still slow

current picture
![current pic](https://github.com/pinebud77/YetAnotherMediaManager_public/blob/main/yamm.png)
