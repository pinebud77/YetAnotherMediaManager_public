Yet Another Media Manager
=========================

This is Video clip file manager. This is my personal project..

Download
* https://github.com/pinebud77/YetAnotherMediaManager_public/releases/latest

Features
* File addition in background through thread
* File management with database (sqlite3)
* Video thumbnail image generation
* Selection of cover image from thumbnails
* tagging by actor names and tags
* save/load configuration file : location - user_home_dir/yamm.settings (JSON format)

Dependencies
* moviepy library : pip install movipy
* wxpython GUI library : pip install wxpython

Problems
* DB schema is not fixed yet
* main list control is too slow to update : fixed
* lag during scaning files
* should use sort function from wx.ListCtrl : fixed

current picture
![current pic](https://github.com/pinebud77/YetAnotherMediaManager_public/blob/main/yamm.png)
