#!/usr/bin/env python3

# Copyright 2020 pinebud77@hotmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import sys
import wx
import io
import threading
import datetime
import logging
import requests
import webbrowser
import tempfile
import urllib.request
import copy

import settings
import icons
from catalog import *
from gui_components import *
from yamm import VERSION_MAJOR, VERSION_MINOR

GITHUB_URL = 'https://github.com/pinebud77/YetAnotherMediaManager_public'
RELEASE_URL = GITHUB_URL + '/releases'

mm_global = None


class MediaManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MediaManager, self).__init__(*args, **kwargs)

        self.catalog = None
        self.view_contents = settings.DEF_VIEW_CONTENTS
        self.last_view_contents = None
        self.view_type = settings.DEF_VIEW_TYPE
        self.resized = False
        self.cat_thread = None
        self.thread_message = None
        self.db_updated = False
        self.thumb_sel = None
        self.files = []
        self.favorites = []
        self.files_selected = []
        self.favorites_selected = []
        self.file_last_selected = None
        self.favorite_last_selected = None
        self.sort_method = settings.DEF_SORT_METHOD
        self.sort_ascend = settings.DEF_SORT_ASCEND
        if self.sort_ascend:
            self.sort_positive = 1
        else:
            self.sort_positive = -1
        self.thread_catalog = None
        self.file_to_open = None

        self.InitUI()

    def InitUI(self):
        dummyPanel = wx.Panel(self)
        dummyPanel.Hide()
        self.SetBackgroundColour(dummyPanel.GetBackgroundColour())

        menubar = wx.MenuBar()
        catMenu = wx.Menu()
        catNew = catMenu.Append(wx.ID_ANY, 'New Catalog', 'Create New Catalog')
        catOpen = catMenu.Append(wx.ID_ANY, 'Open Catalog', 'Open Existing Catalog')
        catEdit = catMenu.Append(wx.ID_ANY, 'Edit Catalog', 'Edit Opened Catalog')
        catMenu.AppendSeparator()
        catSync = catMenu.Append(wx.ID_ANY, 'Sync Catalog files', 'Sync Opened Catalog files')
        catStop = catMenu.Append(wx.ID_ANY, 'Stop Syncing Catalog', 'Stop Syncing Catalog')
        catMenu.AppendSeparator()
        catClose = catMenu.Append(wx.ID_ANY, 'Close Catalog files', 'Close Opened Catalog files')
        catMenu.AppendSeparator()
        catExit = catMenu.Append(wx.ID_EXIT, 'Quit', 'Quit Application')
        menubar.Append(catMenu, '&Catalog')

        self.Bind(wx.EVT_MENU, self.OnNewCatalog, catNew)
        self.Bind(wx.EVT_MENU, self.OnOpenCatalog, catOpen)
        self.Bind(wx.EVT_MENU, self.OnEditCatalog, catEdit)
        self.Bind(wx.EVT_MENU, self.OnSyncCatalog, catSync)
        self.Bind(wx.EVT_MENU, self.OnSyncStop, catStop)
        self.Bind(wx.EVT_MENU, self.OnCloseCatalog, catClose)
        self.Bind(wx.EVT_MENU, self.OnClose, catExit)

        viewMenu = wx.Menu()
        viewSmall = viewMenu.Append(wx.ID_ANY, 'Small Thumbnails')
        viewMedium = viewMenu.Append(wx.ID_ANY, 'Medium Thumbnails')
        viewLarge = viewMenu.Append(wx.ID_ANY, 'Large Thumbnails')
        menubar.Append(viewMenu, '&View')

        self.Bind(wx.EVT_MENU, self.OnViewSmall, viewSmall)
        self.Bind(wx.EVT_MENU, self.OnViewMedium, viewMedium)
        self.Bind(wx.EVT_MENU, self.OnViewLarge, viewLarge)

        helpMenu = wx.Menu()
        helpPage = helpMenu.Append(wx.ID_ANY, 'Open Github homepage')
        helpMenu.AppendSeparator()
        helpAbout = helpMenu.Append(wx.ID_ANY, 'About')
        menubar.Append(helpMenu, '?')

        self.Bind(wx.EVT_MENU, self.OnHelpPage, helpPage)
        self.Bind(wx.EVT_MENU, self.OnHelpAbout, helpAbout)

        self.SetMenuBar(menubar)

        vbox = wx.BoxSizer(wx.VERTICAL)

        tb = wx.ToolBar(self, -1)
        tbNew = tb.AddTool(wx.ID_ANY, 'New Catalog', self.get_toolbar_bitmap(icons.cat_new))
        tbOpen = tb.AddTool(wx.ID_ANY, 'Open Catalog file', self.get_toolbar_bitmap(icons.cat_open))
        tbEdit = tb.AddTool(wx.ID_ANY, 'Edit Catalog file', self.get_toolbar_bitmap(icons.cat_edit))
        tbSync = tb.AddTool(wx.ID_ANY, 'Sync Catalog file', self.get_toolbar_bitmap(icons.cat_sync))
        tbStop = tb.AddTool(wx.ID_ANY, 'Stop sync of Catalog file', self.get_toolbar_bitmap(icons.cat_stop))
        tbClose = tb.AddTool(wx.ID_ANY, 'Close Catalog file', self.get_toolbar_bitmap(icons.cat_close))
        tb.AddSeparator()
        tbSmall = tb.AddTool(wx.ID_ANY, 'Small file list image', self.get_toolbar_bitmap(icons.file_small))
        tbMedium = tb.AddTool(wx.ID_ANY, 'Medium file list image', self.get_toolbar_bitmap(icons.file_medium))
        tbLarge = tb.AddTool(wx.ID_ANY, 'Large file list image', self.get_toolbar_bitmap(icons.file_large))
        tb.AddSeparator()
        tbDelete = tb.AddTool(wx.ID_ANY, 'Delete selected files or favorites', self.get_toolbar_bitmap(icons.file_delete))
        tb.AddSeparator()
        tbExit = tb.AddTool(wx.ID_ANY, 'Exit Application', self.get_toolbar_bitmap(icons.app_exit))
        tb.AddSeparator()
        tbHome = tb.AddTool(wx.ID_ANY, 'Open Github homepage', self.get_toolbar_bitmap(icons.help_home))
        tbAbout = tb.AddTool(wx.ID_ANY, 'About this Application', self.get_toolbar_bitmap(icons.help_about))

        tb.Realize()
        self.Bind(wx.EVT_TOOL, self.OnNewCatalog, tbNew)
        self.Bind(wx.EVT_TOOL, self.OnOpenCatalog, tbOpen)
        self.Bind(wx.EVT_TOOL, self.OnEditCatalog, tbEdit)
        self.Bind(wx.EVT_TOOL, self.OnSyncCatalog, tbSync)
        self.Bind(wx.EVT_TOOL, self.OnSyncStop, tbStop)
        self.Bind(wx.EVT_TOOL, self.OnCloseCatalog, tbClose)
        self.Bind(wx.EVT_TOOL, self.OnViewSmall, tbSmall)
        self.Bind(wx.EVT_TOOL, self.OnViewMedium, tbMedium)
        self.Bind(wx.EVT_TOOL, self.OnViewLarge, tbLarge)
        self.Bind(wx.EVT_TOOL, self.OnFileDelete, tbDelete)
        self.Bind(wx.EVT_TOOL, self.OnHelpAbout, tbAbout)
        self.Bind(wx.EVT_TOOL, self.OnHelpPage, tbHome)
        self.Bind(wx.EVT_TOOL, self.OnClose, tbExit)

        vbox.Add(tb, 0, flag=wx.EXPAND)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.leftPanel = LeftPanel(self, size=(200, -1))
        self.leftPanel.set_mm_window(self)
        hbox.Add(self.leftPanel, 0, flag=wx.EXPAND)

        ivbox = wx.BoxSizer(wx.VERTICAL)

        ihbox = wx.BoxSizer(wx.HORIZONTAL)
        self.favRadio = wx.RadioButton(self, label='Favorites', style=wx.RB_GROUP)
        ihbox.Add(self.favRadio, 0, flag=wx.EXPAND)
        self.fileRadio = wx.RadioButton(self, label='Files')
        ihbox.Add(self.fileRadio, 0, flag=wx.EXPAND)
        if self.view_contents == VIEW_FILES:
            self.fileRadio.SetValue(True)
        else:
            self.favRadio.SetValue(True)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnContentsRadio, self.favRadio)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnContentsRadio, self.fileRadio)
        ihbox.AddStretchSpacer()
        ihbox.Add(wx.StaticText(self, label='sort by :'), 0, wx.EXPAND)
        sort_choices = ('Filename', 'Created Time', 'Last Played Time', 'Duration', 'Path', 'Size', 'Resolution')
        self.sortChoice = wx.Choice(self, choices=sort_choices)
        self.sortChoice.SetSelection(self.sort_method)
        self.Bind(wx.EVT_CHOICE, self.OnSortChange, self.sortChoice)
        ihbox.Add(self.sortChoice, 0)
        ascend_choices = ('Descend', 'Ascend')
        self.ascendChoice = wx.Choice(self, choices=ascend_choices)
        if self.sort_ascend:
            self.ascendChoice.SetSelection(1)
        else:
            self.ascendChoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnAscendChange, self.ascendChoice)
        ihbox.Add(self.ascendChoice, 0)
        ivbox.Add(ihbox, 0, wx.EXPAND)

        filesList = wx.ListCtrl(self, style=wx.LC_ICON |
                                            wx.BORDER_SUNKEN |
                                            wx.LC_AUTOARRANGE |
                                            wx.NO_FULL_REPAINT_ON_RESIZE |
                                            wx.CLIP_CHILDREN |
                                            wx.LC_EDIT_LABELS)
        filesList.SetDoubleBuffered(True)
        filesList.InsertColumn(0, 'thumbnail', width=360)
        filesList.InsertColumn(1, 'filename', width=200)
        filesList.InsertColumn(2, 'size', width=100)
        filesList.InsertColumn(3, 'duration', width=100)
        filesList.InsertColumn(4, 'path', width=360)
        ivbox.Add(filesList, 1, flag=wx.ALL|wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)
        if self.view_type == SMALL_THUMBNAILS:
            self.image_list = wx.ImageList(DEF_SMALL_RESOLUTION[0], DEF_SMALL_RESOLUTION[1])
        elif self.view_type == MEDIUM_THUMBNAILS:
            self.image_list = wx.ImageList(DEF_MEDIUM_RESOLUTION[0], DEF_MEDIUM_RESOLUTION[1])
        else:
            self.image_list = wx.ImageList(DEF_THUMBNAIL_WIDTH, DEF_THUMBNAIL_HEIGHT)
        filesList.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnFileSelect, filesList)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnFileDeselect, filesList)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnFileDClick, filesList)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnFileEdit, filesList)
        filesList.Bind(wx.EVT_KEY_DOWN, self.OnFilesKeyDown)
        filesList.SetDoubleBuffered(True)
        self.filesList = filesList

        self.rightPanel = RightPanel(self, size=(300, -1))
        self.rightPanel.mm_window = self
        hbox.Add(self.rightPanel, 0, flag=wx.EXPAND)
        vbox.Add(hbox, 1, flag=wx.EXPAND)

        w = settings.DEF_THUMBS_HEIGHT * 240 // 135
        thumbsList = wx.ListCtrl(self,
                                 size=(w * 50, settings.DEF_THUMBS_HEIGHT + 42),
                                 style=wx.LC_ICON |
                                       wx.LC_SINGLE_SEL |
                                       wx.LC_ALIGN_LEFT |
                                       wx.LC_AUTOARRANGE)
        self.thumbs_list = wx.ImageList(w, settings.DEF_THUMBS_HEIGHT)
        thumbsList.SetImageList(self.thumbs_list, wx.IMAGE_LIST_NORMAL)
        vbox.Add(thumbsList, 0, wx.EXPAND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnThumbSelect, thumbsList)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnThumbDClick, thumbsList)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnThumbRight, thumbsList)
        self.thumbsList = thumbsList

        self.db_timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnDbTimer, self.db_timer)
        self.open_timer = wx.Timer(self, 1)
        self.Bind(wx.EVT_TIMER, self.OnOpenTimer, self.open_timer)
        self.thumb_timer = wx.Timer(self, 2)
        self.Bind(wx.EVT_TIMER, self.OnThumbTimer, self.thumb_timer)


        self.thumbRightMenu = wx.Menu()
        menuFavorite = self.thumbRightMenu.Append(wx.ID_ANY, 'Add to Favorites')
        menuCover = self.thumbRightMenu.Append(wx.ID_ANY, 'Set as Cover Image')
        menuThumbSave = self.thumbRightMenu.Append(wx.ID_ANY, 'Save as JPG file')
        self.Bind(wx.EVT_MENU, self.OnFavorite, menuFavorite)
        self.Bind(wx.EVT_MENU, self.OnCover, menuCover)
        self.Bind(wx.EVT_MENU, self.OnThumbSave, menuThumbSave)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        icopath = os.path.join(tempfile.gettempdir(), 'yamm.ico')
        try:
            f = open(icopath, 'wb')
            f.write(icons.app_icon)
            f.close()
            self.SetIcon(wx.Icon(icopath))
        except Exception as e:
            logging.error('setting app icon failed')

        self.SetSize((720, 640))
        self.SetTitle('Yet Another Media Manager v%d.%d' % (VERSION_MAJOR, VERSION_MINOR))
        self.Centre()

        logging.info('Yet Another Media Manager v%d.%d' % (VERSION_MAJOR, VERSION_MINOR))
        r = requests.get(RELEASE_URL + '/latest')
        if r.url != '%s/tag/%d.%d' % (RELEASE_URL, VERSION_MAJOR, VERSION_MINOR):
            try:
                wx.MessageBox('Update found at the github. Web page openned for the update.', 'update', wx.OK | wx.ICON_WARNING)
                webbrowser.open(RELEASE_URL)
            except:
                pass

    def disable(self):
        self.leftPanel.Disable()
        self.favRadio.Disable()
        self.fileRadio.Disable()
        self.sortChoice.Disable()
        self.ascendChoice.Disable()

    def enable(self):
        self.leftPanel.Enable()
        self.favRadio.Enable()
        self.fileRadio.Enable()
        self.sortChoice.Enable()
        self.ascendChoice.Enable()

    def get_toolbar_bitmap(self, bimg):
        dstream = io.BytesIO(bimg)
        image = wx.Image(dstream, type=wx.BITMAP_TYPE_PNG)
        image.Rescale(24, 24)
        return wx.Bitmap(image)

    def delete_files(self):
        self.filesList.Freeze()
        selected = copy.copy(self.files_selected)
        for list_idx in range(self.filesList.GetItemCount()):
            self.filesList.Select(list_idx, on=0)

        for mf in selected:
            logging.debug('deleting file : %s' % mf)
            try:
                self.catalog.del_file(mf)
            except Exception as e:
                logging.error(e)
                continue
            index = self.files.index(mf)
            target_idx = None
            for list_idx in range(self.filesList.GetItemCount()):
                data = self.filesList.GetItemData(list_idx)
                if data == index:
                    target_idx = list_idx
                    break
            for list_idx in range(self.filesList.GetItemCount()):
                data = self.filesList.GetItemData(list_idx)
                if data <= index:
                    continue
                self.filesList.SetItemData(list_idx, data - 1)
            if target_idx is not None:
                self.filesList.DeleteItem(target_idx)
            del(self.files[index])

        self.files_selected = []
        self.favorites_selected = []
        self.filesList.Thaw()

    def delete_favorites(self):
        self.filesList.Freeze()
        selected = copy.copy(self.favorites_selected)
        for list_idx in range(self.filesList.GetItemCount()):
            self.filesList.Select(list_idx, on=0)

        for fav in selected:
            logging.debug('delete favorite : %s' % fav)
            fav.mediafile.del_favorite(fav)
            index = self.favorites.index(fav)
            target_idx = None
            for list_idx in range(self.filesList.GetItemCount()):
                data = self.filesList.GetItemData(list_idx)
                if data == index:
                    target_idx = list_idx
                    break
            for list_idx in range(self.filesList.GetItemCount()):
                data = self.filesList.GetItemData(list_idx)
                if data <= index:
                    continue
                self.filesList.SetItemData(list_idx, data - 1)
            if target_idx is not None:
                self.filesList.DeleteItem(target_idx)
            del(self.files[index])
            del(self.favorites[index])

        self.files_selected = []
        self.favorites_selected = []
        self.filesList.Select(-1)
        self.filesList.Thaw()

    def OnFileDelete(self, e):
        if self.fileRadio.GetValue():
            self.delete_files()
        else:
            self.delete_favorites()

    def OnFilesKeyDown(self, e):
        if e.GetKeyCode() != wx.WXK_DELETE:
            return
        self.OnFileDelete(None)

    def OnContentsRadio(self, e):
        if self.fileRadio.GetValue():
            self.view_contents = VIEW_FILES
        else:
            self.view_contents = VIEW_FAVORITES
        self.update_view()

    def OnHelpPage(self, e):
        logging.debug('opening Github homepage : %s' % GITHUB_URL)
        try:
            webbrowser.open(GITHUB_URL)
        except Exception as e:
            logging.error('calling webrowser failed')
            logging.error(e)

    def OnHelpAbout(self, e):
        wx.MessageBox('Yet Another Media Manager v%d.%d' % (VERSION_MAJOR, VERSION_MINOR),
                      'About',
                      wx.OK | wx.ICON_WARNING)

    def OnSortChange(self, e):
        self.sort_method = self.sortChoice.GetSelection()
        logging.debug('sorting method changed to %d' % self.sort_method)
        if self.sort_method == FILTER_SORT_FILENAME:
            self.filesList.SortItems(self.sort_filename)
        elif self.sort_method == FILTER_SORT_TIME:
            self.filesList.SortItems(self.sort_time)
        elif self.sort_method == FILTER_SORT_LASTPLAY:
            self.filesList.SortItems(self.sort_lastplay)
        elif self.sort_method == FILTER_SORT_DURATION:
            self.filesList.SortItems(self.sort_duration)
        elif self.sort_method == FILTER_SORT_PATH:
            self.filesList.SortItems(self.sort_path)
        elif self.sort_method == FILTER_SORT_SIZE:
            self.filesList.SortItems(self.sort_size)
        elif self.sort_method == FILTER_SORT_RESOLUTION:
            self.filesList.SortItems(self.sort_resolution)
        else:
            logging.error('not a defined sorting method')
            self.sort_method = FILTER_SORT_PATH
            self.filesList.SortItems(self.sort_path)

    def OnAscendChange(self, e):
        if self.ascendChoice.GetSelection() == 0:
            self.sort_ascend = False
            self.sort_positive = -1
        else:
            self.sort_ascend = True
            self.sort_positive = 1
        self.OnSortChange(None)

        if self.sort_ascend:
            logging.debug('sorting ascend changed to ascend')
        else:
            logging.debug('sorting ascend changed to descend')

    def add_mediafile(self, mf):
        if self.view_contents == VIEW_FILES:
            index = len(self.files)
            self.files.append(mf)
            if mf.imagelist_index is None:
                jpg_bytes = mf.get_coverjpg()
                if jpg_bytes:
                    data_stream = io.BytesIO(jpg_bytes)
                    image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
                else:
                    image = wx.Image(360, 203)
                image = self.get_scaled_image(self.image_list, image)
                bmp = wx.Bitmap(image)
                mf.imagelist_index = self.image_list.Add(bmp)

            list_idx = self.filesList.InsertItem(index,
                                                 mf.filename,
                                                 mf.imagelist_index)
            self.filesList.SetItemData(list_idx, index)
        else:
            for fav in mf.favorites:
                index = len(self.files)
                self.files.append(mf)
                self.favorites.append(fav)
                if fav.imagelist_index is None:
                    jpg_bytes = mf.get_thumbjpg(fav.thumb_id)
                    if jpg_bytes:
                        data_stream = io.BytesIO(jpg_bytes)
                        image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
                    else:
                        image = wx.Image(360, 203)
                    image = self.get_scaled_image(self.image_list, image)
                    bmp = wx.Bitmap(image)
                    fav.imagelist_index = self.image_list.Add(bmp)

                list_idx = self.filesList.InsertItem(index,
                                                     mf.filename,
                                                     fav.imagelist_index)
                self.filesList.SetItemData(list_idx, index)

    def OnViewChange(self, vtype=None, update_period=None):
        if self.view_type != vtype and vtype is not None:
            if vtype is not None:
                self.view_type = vtype
            if self.view_type == SMALL_THUMBNAILS:
                self.image_list = wx.ImageList(DEF_SMALL_RESOLUTION[0], DEF_SMALL_RESOLUTION[1])
            elif self.view_type == MEDIUM_THUMBNAILS:
                self.image_list = wx.ImageList(DEF_MEDIUM_RESOLUTION[0], DEF_MEDIUM_RESOLUTION[1])
            elif self.view_type == LARGE_THUMBNAILS:
                self.image_list = wx.ImageList(DEF_THUMBNAIL_WIDTH, DEF_THUMBNAIL_HEIGHT)
            self.filesList.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)
            for mf in self.catalog:
                mf.imagelist_index = None
            update_period = 50

        if update_period is None:
            update_period = 200

        logging.debug('view loading started')

        self.files = []
        self.favorites = []
        self.files_selected = []
        self.favorites_selected = []
        self.file_last_selected = None
        self.favorite_last_selected = None
        self.rightPanel.set_mediafiles([])

        self.filesList.DeleteAllItems()

        if not self.catalog:
            return
        files = self.catalog.filter(actors=self.leftPanel.actor_selected,
                                    tags=self.leftPanel.tag_selected,
                                    filename=self.leftPanel.file_filter)

        self.filesList.Freeze()
        self.disable()
        count = 0
        total = len(files)
        for mf in files:
            count += 1
            if count % update_period == 0:
                self.statusbar.SetStatusText('loading files (%d/%d)' % (count, total))
                self.filesList.Thaw()
                wx.Yield()
                self.filesList.Freeze()
            self.add_mediafile(mf)
        self.statusbar.SetStatusText('files loaded (%d/%d)' % (count, total))

        self.OnSortChange(None)
        self.enable()
        self.filesList.Thaw()

        logging.debug('view loading finished')

    def OnDbTimer(self, e):
        logging.debug('OnDbTimer called')
        if self.thread_message:
            self.statusbar.SetStatusText(self.thread_message)
            self.thread_message = None

        if self.db_updated:
            self.catalog.reload_files()

            files = self.catalog.filter(actors=self.leftPanel.actor_selected,
                                        tags=self.leftPanel.tag_selected,
                                        filename=self.leftPanel.file_filter)
            for mf in files:
                if not (mf in self.files):
                    self.add_mediafile(mf)
                    logging.debug('file added to the view : %s' % mf)

            mf_i = 0
            while mf_i < len(self.files):
                mf = self.files[mf_i]
                if not (mf in files):
                    for idx in range(self.filesList.GetItemCount()):
                        data = self.filesList.GetItemData(idx)
                        if data == mf_i:
                            self.filesList.DeleteItem(idx)
                            break
                    for idx in range(self.filesList.GetItemCount()):
                        data = self.filesList.GetItemData(idx)
                        if data >= mf_i:
                            self.filesList.SetItemData(idx, data - 1)
                    if mf in self.files_selected:
                        self.deselect_file(mf)
                    logging.debug('file removed from view : %s' % mf)
                    del self.files[mf_i]
                    mf_i -= 1
                mf_i += 1

            self.db_updated = False
        if not self.cat_thread or not self.cat_thread.is_alive():
            self.db_updated = False
            self.db_timer.Stop()

    def get_scaled_image(self, il, image):
        il_size = il.GetSize()
        im_size = image.GetSize()

        max_width = il_size.width
        max_height = il_size.height
        width = im_size.width
        height = im_size.height

        new_width = max_width
        new_height = int(max_width * height / width)
        if new_height > max_height:
            new_width = int(new_width * max_height / new_height)
            new_height = max_height

        image = image.Rescale(new_width, new_height)
        return image.Resize(wx.Size(max_width, max_height), wx.Point((max_width-new_width)//2, (max_height-new_height)//2))

    def deselect_file(self, mf):
        if not (mf in self.files_selected):
            return

        mf.thumbnails = None
        self.files_selected.remove(mf)
        self.rightPanel.set_mediafiles(self.files_selected)

        if mf != self.file_last_selected:
            return
        self.thumbsList.DeleteAllItems()
        self.thumbs_list.RemoveAll()
        self.file_last_selected = None

    def deselect_favorite(self, fav):
        if not (fav in self.favorites_selected):
            return

        index = self.favorites_selected.index(fav)
        del(self.files_selected[index])
        del(self.favorites_selected[index])
        self.rightPanel.set_mediafiles(self.files_selected)

        if fav != self.favorite_last_selected:
            return
        self.thumbsList.DeleteAllItems()
        self.thumbs_list.RemoveAll()
        self.file_last_selected = None

    def OnThumbTimer(self, e):
        if not self.file_last_selected:
            return
        thumbs = self.file_last_selected.get_thumbnails()
        if not thumbs:
            return
        index = 0
        for tb in thumbs:
            time = tb[0]
            jpg = tb[1]

            hours = int(time / 3600)
            minutes = int((time - hours * 3600) / 60)
            seconds = int(time - hours * 3600 - minutes * 60)
            self.thumbsList.InsertItem(index, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))

            data_stream = io.BytesIO(jpg)
            image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
            image = self.get_scaled_image(self.thumbs_list, image)
            bmp = wx.Bitmap(image)
            self.thumbs_list.Add(bmp)
            self.thumbsList.SetItemImage(index, index)

            index += 1

    def select_file(self, mf, update_thumbs=True):
        if mf in self.files_selected:
            return

        self.files_selected.append(mf)
        self.rightPanel.set_mediafiles(self.files_selected)
        self.file_last_selected = mf
        if update_thumbs:
            self.thumbsList.DeleteAllItems()
            self.thumbs_list.RemoveAll()
            self.thumb_timer.Stop()
            self.thumb_timer.Start(5, oneShot=True)

    def select_favorite(self, fav, update_thumbs=False):
        if fav in self.favorites_selected:
            return

        self.files_selected.append(fav.mediafile)
        self.favorites_selected.append(fav)
        self.rightPanel.set_mediafiles(self.files_selected)
        self.thumbsList.DeleteAllItems()
        self.thumbs_list.RemoveAll()
        self.file_last_selected = fav.mediafile
        self.favorite_last_selected = fav
        self.thumb_timer.Stop()
        if not update_thumbs:
            self.thumb_timer.Start(5, oneShot=True)

    def sort_filename(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if mf1.filename == mf2.filename:
            return 0
        elif mf1.filename < mf2.filename:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_time(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if mf1.time == mf2.time:
            return 0
        elif mf1.time < mf2.time:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_lastplay(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if (not mf1.lastplay) and mf2.lastplay:
            return -self.sort_positive
        if mf1.lastplay and (not mf2.lastplay):
            return self.sort_positive
        if not mf1.lastplay and not mf2.lastplay:
            return 0
        if mf1.lastplay == mf2.lastplay:
            return 0
        elif mf1.lastplay < mf2.lastplay:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_duration(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if (not mf1.duration) and mf2.duration:
            return -self.sort_positive
        if mf1.duration and not (mf2.duration):
            return self.sort_positive
        if not mf1.duration and not mf2.duration:
            return 0
        if mf1.duration == mf2.duration:
            return 0
        elif mf1.duration < mf2.duration:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_path(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if mf1.abspath == mf2.abspath:
            return 0
        elif mf1.abspath < mf2.abspath:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_size(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if (not mf1.size) and mf2.size:
            return -self.sort_positive
        if mf1.size and (not mf2.size):
            return self.sort_positive
        if not mf1.size and not mf2.size:
            return 0
        if mf1.size == mf2.size:
            return 0
        elif mf1.size < mf2.size:
            return -self.sort_positive
        else:
            return self.sort_positive

    def sort_resolution(self, item1, item2):
        mf1 = self.files[item1]
        mf2 = self.files[item2]
        if not (mf1.width and mf1.height):
            mf1_size = None
        if not (mf2.width and mf2.height):
            mf1_size = None
        if mf1.width > mf1.height:
            mf1_size = mf1.width
        else:
            mf1_size = mf1_height
        if mf2.width > mf2.height:
            mf2_size = mf2.width
        else:
            mf2_size = mf2_height
        if (not mf1_size) and mf2_size:
            return -self.sort_positive
        if mf1_size and (not mf2_size):
            return self.sort_positive
        if not mf1_size and not mf2_size:
            return 0
        if mf1_size == mf2_size:
            return 0
        elif mf1_size < mf2_size:
            return -self.sort_positive
        else:
            return self.sort_positive

    def update_view(self, update_period=None):
        self.OnViewChange(vtype=None, update_period=update_period)

    def OnViewSmall(self, e):
        self.OnViewChange(SMALL_THUMBNAILS)

    def OnViewMedium(self, e):
        self.OnViewChange(MEDIUM_THUMBNAILS)

    def OnViewLarge(self, e):
        self.OnViewChange(LARGE_THUMBNAILS)

    def OnCover(self, e):
        mf = self.file_last_selected
        if mf is None:
            return
        logging.info('cover selected for %s' % mf)
        mf.set_cover_id(self.thumb_sel)
        for mf_i in range(len(self.files)):
            if self.files[mf_i] == mf:
                break
        jpg_bytes = mf.get_coverjpg()
        if jpg_bytes:
            data_stream = io.BytesIO(jpg_bytes)
            image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
        else:
            image = wx.Image(360, 203)
        image = self.get_scaled_image(self.image_list, image)
        bmp = wx.Bitmap(image)
        self.image_list.Replace(mf_i, bmp)
        self.filesList.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)

    def OnFavorite(self, e):
        mf = self.file_last_selected
        if not mf:
            return
        if not mf.thumbnails:
            return
        thumb = mf.thumbnails[self.thumb_sel]
        fav = mf.add_favorite(thumb[0])
        if self.fileRadio.GetValue():
            self.select_file(mf, update_thumbs=False)
        else:
            self.update_view()
            self.select_favorite(fav, update_thumbs=False)

    def OnThumbSave(self, e):
        if not self.file_last_selected:
            return
        with wx.FileDialog(self, 'save thumbnail', '', '', 'JPEG file (*.jpg)|*.jpg',
                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            thumb = self.file_last_selected.thumbnails[self.thumb_sel]
            try:
                with open(pathname, 'wb') as f:
                    f.write(thumb[1])
                    f.close()
            except IOError:
                logging.error('cannot save jpg file : %s' % pathname)

    def OnThumbSelect(self, e):
        self.thumb_sel = self.thumbsList.GetFirstSelected()

    def OnThumbDClick(self, e):
        logging.debug('openning videoclip : %s' % self.file_last_selected)
        thumb = self.file_last_selected.thumbnails[self.thumb_sel]
        run_list = (DEF_OPEN_EXE,
                    DEF_OPEN_FILE % self.file_last_selected.abspath,
                    DEF_OPEN_SEEK % thumb[0])
        subprocess.Popen(run_list)
        self.file_last_selected.set_lastplayed(datetime.datetime.now())
        self.rightPanel.set_mediafiles(self.files_selected)

    def OnFileDClick(self, e):
        if self.fileRadio.GetValue():
            logging.debug('openning videoclip : %s' % self.file_last_selected)
            run_list = (DEF_OPEN_EXE,
                        DEF_OPEN_FILE % self.file_last_selected.abspath)
            subprocess.Popen(run_list)
        else:
            logging.debug('openning videoclip : %s' % self.file_last_selected)
            run_list = (DEF_OPEN_EXE,
                        DEF_OPEN_FILE % self.file_last_selected.abspath,
                        DEF_OPEN_SEEK % self.favorite_last_selected.time)
            subprocess.Popen(run_list)
        self.file_last_selected.set_lastplayed(datetime.datetime.now())
        self.rightPanel.set_mediafiles(self.files_selected)

    def OnFileEdit(self, e):
        orig_filename = self.filesList.GetItemText(e.GetIndex())
        new_filename = e.GetLabel()
        if orig_filename.lower()[-4:] != new_filename.lower()[-4:]:
            e.Veto()
            return
        mf = self.files[self.filesList.GetItemData(e.GetIndex())]
        res = mf.rename(new_filename)
        if not res:
            e.Veto()
            return
        if not self.fileRadio.GetValue():
            self.update_view()

    def OnThumbRight(self, e):
        self.thumb_item_clicked = e.GetText()
        self.thumbsList.PopupMenu(self.thumbRightMenu, e.GetPoint())

    def OnFileSelect(self, e):
        sel = self.filesList.GetItemData(e.GetIndex())
        if self.fileRadio.GetValue():
            mf = self.files[sel]
            self.select_file(mf)
        else:
            fav = self.favorites[sel]
            self.select_favorite(fav)

    def OnFileDeselect(self, e):
        sel = self.filesList.GetItemData(e.GetIndex())
        if self.fileRadio.GetValue():
            mf = self.files[sel]
            self.deselect_file(mf)
        else:
            fav = self.favorites[sel]
            self.deselect_favorite(fav)

    def OnNewCatalog(self, e):
        self.stop_sync()
        self.OnCloseCatalog(None)

        with CatalogDialog(self, title="New Catalog") as catDialog:
            if catDialog.ShowModal() == wx.ID_CANCEL:
                return

            abspath = os.path.abspath(catDialog.catPath.GetLabelText())
            try:
                os.remove(abspath)
            except Exception as e:
                pass
            self.catalog = Catalog(db_abspath=abspath)
            self.catalog.open_database()

            for n in range(catDialog.topList.GetCount()):
                self.catalog.add_topdir(catDialog.topList.GetString(n))

            self.statusbar.SetStatusText('Start Scanning files...')
            self.OnSyncCatalog(e)

    def OnEditCatalog(self, e):
        if not self.catalog:
            self.statusbar.SetStatusText('Open or Create Catalog first')
            return

        self.stop_sync()

        with CatalogDialog(self, title='Modify Catalog') as catDialog:
            catDialog.catPath.SetLabelText(self.catalog.filepath)
            catDialog.catPath.Disable()

            for topdir in self.catalog.topdir_list:
                catDialog.topList.Append(topdir.abspath)

            if catDialog.ShowModal() == wx.ID_CANCEL:
                return

            new_topdirs = []
            for n in range(catDialog.topList.GetCount()):
                new_topdirs.append(catDialog.topList.GetString(n))

            td_i = 0
            while td_i < len(self.catalog.topdir_list):
                topdir = self.catalog.topdir_list[td_i]
                if not (topdir.abspath in new_topdirs):
                    self.catalog.del_topdir(topdir.abspath)
                    td_i -= 1
                td_i += 1

            for new_topdir in new_topdirs:
                found = False
                for topdir in self.catalog.topdir_list:
                    if new_topdir == topdir.abspath:
                        found = True
                        break
                if not found:
                    self.catalog.add_topdir(new_topdir)

            self.statusbar.SetStatusText('Start Scanning files (This will take time to check filesystem')
            self.OnSyncCatalog(e)

    def open_catalog(self, yamm_file):
        yamm_file = os.path.abspath(yamm_file)
        self.catalog = Catalog(db_abspath=yamm_file)
        self.statusbar.SetStatusText('Openning catalog file (This will take time to load files)')
        try:
            self.catalog.open_database()
        except DbVersionException as e:
            wx.MessageBox('Sorry. Catalog Version was updated. You need to create new .yamm file.',
                          'Version Mismatch',
                          wx.OK)
            return

        self.update_view(update_period=50)
        self.leftPanel.set_mm_window(self)
        self.statusbar.SetStatusText('Start Scanning files...')
        self.OnSyncCatalog(None)

    def OnOpenTimer(self, e):
        pathname = os.path.abspath(self.file_to_open)
        self.open_catalog(pathname)

    def OnOpenCatalog(self, e):
        self.OnCloseCatalog(None)

        with wx.FileDialog(self, "Open Catalog", wildcard='catalog files (*.yamm)|*.yamm',
                           style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.open_catalog(pathname)

    def OnCloseCatalog(self, e):
        if self.catalog is None:
            return
        self.stop_sync()
        self.catalog.close_database()
        self.catalog = None
        self.leftPanel.set_mm_window(None)
        for mf in self.files_selected:
            self.deselect_file(mf)
        self.update_view()

    def mm_sync_cb(self, msg):
        self.thread_message = msg
        self.db_updated = True

    def cat_thread_func(self):
        logging.info('sync thread started')
        self.thread_catalog = Catalog(self.catalog.filepath)
        self.thread_catalog.open_database()
        self.thread_catalog.sync_database(msg_cb=self.mm_sync_cb)
        self.thread_catalog.close_database()
        self.thread_catalog = None
        self.cat_thread = None
        logging.info('sync thread finished')

    def OnSyncCatalog(self, e):
        if self.catalog is None:
            return
        self.cat_thread = threading.Thread(target=self.cat_thread_func)
        self.cat_thread.start()
        self.db_timer.Start(500)

    def OnSyncStop(self, e):
        self.stop_sync()

    def stop_sync(self, timeout=90):
        if not self.cat_thread or not self.thread_catalog:
            return
        self.statusbar.SetStatusText('Trying to stop sync')
        self.thread_catalog.kill_thread = True
        for n in range(int(timeout * 2)):
            if not self.cat_thread:
                break
            if not self.cat_thread.is_alive():
                break
            self.cat_thread.join(timeout=0.5)
            wx.Yield()
        self.cat_thread = None
        self.db_timer.Stop()
        self.statusbar.SetStatusText('Sync Stopped')

    def OnFileRight(self, e):
        pass

    def OnClose(self, e):
        logging.info('closing application')
        settings.DEF_VIEW_CONTENTS = self.view_contents
        settings.DEF_VIEW_TYPE = self.view_type
        settings.DEF_SORT_METHOD = self.sort_method
        settings.DEF_SORT_ASCEND = self.sort_ascend

        if self.catalog:
            self.catalog.kill_thread = True
        if self.cat_thread:
            self.stop_sync(0)
        self.Destroy()