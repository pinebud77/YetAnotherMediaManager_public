Yet Another Media Manager
=========================

This is my personal Media file manager.

Features Planed
* File addition in background : done
* File management through data base : done
* Video Stream image generation : done
* Thumbnail generation : done
* Selecting thumbnail from Video Stream images : done
* tagging : done
* Category : required?
* actor name : done
* actor image
* performance optimization
* adding more GUI icons
* save/load configuration file : done

Implementation details
* GUI : wxPython
* sqlite3 : only solution for local DB?

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
