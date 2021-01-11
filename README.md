Yet Another Media Manager
=========================

This is Video clip file manager. This is my personal project. No guarantee or obligations..

Download Windows executable or tagged version
* https://github.com/pinebud77/YetAnotherMediaManager_public/releases

Features
* File addition in background through thread
* File management with database (sqlite3)
* Video thumbnail image generation
* Selection of cover image from thumbnails
* Tagging by actor names and tags
* Filter by actor or tags
* Save/load configuration file : location - user_home_dir/yamm.settings (JSON format)
* Saving thumbnail to JPG file
* Command-line interface for indexing : can run with Linux (tried Rasp-PI)
* Managing Favorite(bookmark) scenes
* File deletion
* File deletion inside app

Command Line Arguments
* -h (--help) : print usage
* -c (--create=) : create yamm catalog file
* -a (--adddir=) : add directory when creating yamm catalog
* -s (--sync=) : sync yamm catalog file
* -d (--debug) : print debug messages
* -q (--quiet) : print no message

Planned Features
* Creating GIFs from thumbnails
* Action GIF on focus on file

Dependencies (Raspberry PI has different dependencies T_T)
* PotPlayer as media player : https://potplayer.daum.net/ - this can be hand modified by editing $(USER)/.yamm_settings JSON file
* moviepy library : pip install movipy
* wxpython GUI library : pip install wxpython

Problems
* bugs!!
* still slow

Rasberry PI setup guide (only command line tried)
```
sudo su
# apt update
# apt install git python3 python3-pip ffmpeg libatlas-base-dev p7zip
# pip3 install moviepy pyunpack patool
# git clone https://github.com/pinebud77/YetAnotherMediaManager_public.git
# cd YetAnotherMediaManager_public
# python3 yamm.py -c /mnt/backup/test.yamm -a /mnt/backup/video/
# chmod 777 /mnt/backup/test.yamm
```

On Windows machine
```
> python yamm.py -i 'z:\test.yamm'
> python yamm.py -m 'z:\test.yamm' -o '/mnt/backup' -n 'z:\'
> python yamm.py 'z:\test.yamm'
```


current picture
![current pic](https://github.com/pinebud77/YetAnotherMediaManager_public/blob/main/yamm.png)
