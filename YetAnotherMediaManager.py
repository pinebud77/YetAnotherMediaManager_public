#!/usr/bin/env python3

import os
import subprocess
import sys
import wx
import io
import threading
import datetime

from catalog import *


LARGE_THUMBNAILS = 0
MEDIUM_THUMBNAILS = 1
SMALL_THUMBNAILS = 2
DETAIL_THUMBNAILS = 3


class LeftPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(LeftPanel, self).__init__(*args, **kwargs)

        self.mm_windows = None
        self.selected_actors = []
        self.selected_tags = []

        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(self, label='Filters'), 0)

        self.actorList = wx.ListCtrl(self, size=(300, -1))
        vbox.Add(self.actorList, 1, wx.EXPAND)

        self.tagList = wx.ListCtrl(self, size=(300, -1))
        vbox.Add(self.tagList, 1, wx.EXPAND)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)


class RightPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(RightPanel, self).__init__(*args, **kwargs)

        self.mm_windows = None
        self.media_file = None

        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.propertyList = wx.ListCtrl(self, size=(300, 145), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_HRULES|wx.LC_VRULES)
        self.propertyList.InsertColumn(0, 'Property', width=100)
        self.propertyList.InsertColumn(1, 'Value', width=195)

        self.propertyList.InsertItem(0, 'Filename')
        self.propertyList.SetItem(0, 1, '')
        self.propertyList.InsertItem(1, 'Path')
        self.propertyList.SetItem(1, 1, '')
        self.propertyList.InsertItem(2, 'Stars')
        self.propertyList.SetItem(2, 1, '')
        self.propertyList.InsertItem(3, 'Size')
        self.propertyList.SetItem(3, 1, '')
        self.propertyList.InsertItem(4, 'Duration')
        self.propertyList.SetItem(4, 1, '')
        self.propertyList.InsertItem(5, 'LastPlayed')
        self.propertyList.SetItem(5, 1, '')
        self.set_property()

        vbox.Add(wx.StaticText(self, label='Property'), 0)

        vbox.Add(self.propertyList)
        vbox.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ivbox = wx.BoxSizer(wx.VERTICAL)
        ivbox.Add(wx.StaticText(self, label='Actors'), 0)
        self.actorList = wx.ListCtrl(self, size=(150, -1))
        ivbox.Add(self.actorList, 1, wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)
        ivbox = wx.BoxSizer(wx.VERTICAL)
        ivbox.Add(wx.StaticText(self, label='Tags'), 0)
        self.tagList = wx.ListCtrl(self, size=(150, -1))
        ivbox.Add(self.tagList, 1, wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)

        vbox.Add(hbox, 1, wx.EXPAND)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

    def set_property(self):
        if not self.media_file:
            return
        self.propertyList.DeleteAllItems()
        self.propertyList.InsertItem(0, 'Filename')
        self.propertyList.SetItem(0, 1, self.media_file.filename)
        self.propertyList.InsertItem(1, 'Path')
        self.propertyList.SetItem(1, 1, self.media_file.abspath())
        self.propertyList.InsertItem(2, 'Stars')
        if self.media_file.stars:
            self.propertyList.SetItem(2, 1, '%d' % self.media_file.stars)
        else:
            self.propertyList.SetItem(2, 1, '')

        self.propertyList.InsertItem(3, 'Size')
        self.propertyList.SetItem(3, 1, '%dMB' % (self.media_file.size // (1024 * 1024)))

        self.propertyList.InsertItem(4, 'Duration')
        if self.media_file.duration:
            hours = self.media_file.duration // 3600
            minutes = (self.media_file.duration - hours * 3600) // 60
            seconds = int(self.media_file.duration) % 60
            self.propertyList.SetItem(4, 1, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))
        else:
            self.propertyList.SetItem(4, 1, 'no info')

        self.propertyList.InsertItem(5, 'LastPlayed')
        if self.media_file.lastplay:
            self.propertyList.SetItem(5, 1, str(self.media_file.lastplay))
        else:
            self.propertyList.SetItem(5, 1, '')

    def set_mediafile(self, mf):
        self.media_file = mf
        self.set_property()

class CatalogDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super(CatalogDialog, self).__init__(*args, **kwargs)

        self.catPath = None
        self.topdir_list = []

        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='Catalog File : ', size=(70, -1), style=wx.TE_RIGHT), 0)
        self.catPath = wx.TextCtrl(self)
        hbox.Add(self.catPath, 1, wx.EXPAND)
        catButton = wx.Button(self, label='Set Path')
        self.Bind(wx.EVT_BUTTON, self.OnCatButton, catButton)
        hbox.Add(catButton, 0, wx.EXPAND)
        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='Top Dirs : ', size=(70, -1), style=wx.TE_RIGHT), 0)
        self.topList = wx.ListBox(self, style=wx.LB_SINGLE|wx.LB_SORT)
        hbox.Add(self.topList, 1, wx.EXPAND)
        ivbox = wx.BoxSizer(wx.VERTICAL)
        addButton = wx.Button(self, label='Add')
        delButton = wx.Button(self, label='Del')
        self.Bind(wx.EVT_BUTTON, self.OnAddButton, addButton)
        self.Bind(wx.EVT_BUTTON, self.OnDelButton, delButton)
        ivbox.Add(addButton, 0)
        ivbox.Add(delButton, 0)
        hbox.Add(ivbox, 0, wx.EXPAND)
        vbox.Add(hbox, 1, wx.EXPAND)
        vbox.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self, wx.ID_OK, label='OK')
        self.okButton.Disable()
        cancelButton = wx.Button(self, wx.ID_CANCEL, label='Cancel')
        hbox.AddStretchSpacer()
        hbox.Add(self.okButton, 0, flag=wx.RIGHT)
        hbox.Add(cancelButton, 0, flag=wx.RIGHT)
        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(5)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

    def OnCatButton(self, e):
       with wx.FileDialog(self, "New Catalog File", wildcard='catalog files (*.nmcat)|*.nmcat',
                           style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.catPath.SetLabelText(pathname)

            if self.topList.GetCount() and self.catPath.GetLabelText():
                self.okButton.Enable()
            else:
                self.okButton.Disable()

    def OnAddButton(self, e):
        with wx.DirDialog(self, "Add Top Directory", style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = dirDialog.GetPath()
            for n in range(0, self.topList.GetCount()):
                if os.path.abspath(pathname) == os.path.abspath(self.topList.GetString(n)):
                    return
            self.topList.Append(os.path.abspath(pathname))

            if self.topList.GetCount() and self.catPath.GetLabelText():
                self.okButton.Enable()
            else:
                self.okButton.Disable()

    def OnDelButton(self, e):
        sel = self.topList.GetSelection()
        if sel >= 0 and sel < self.topList.GetCount():
            self.topList.Delete(sel)
        if self.topList.GetCount() and self.catPath.GetLabelText():
            self.okButton.Enable()
        else:
            self.okButton.Disable()


mm_global = None

def mm_sync_cb(newfile, percent):
    global mm_global
    if newfile:
        mm_global.statusbar.SetStatusText('File Added: %s (%d%% synced)' % (newfile, percent))
    else:
        mm_global.statusbar.SetStatusText('Catalog Sync Finished')
    mm_global.db_updated = True

def cat_thread_func(mm):
    print('thread started')
    global mm_global
    mm_global = mm
    cat = Catalog(mm.catalog.filepath)
    cat.open_database()
    cat.sync_database(file_cb=mm_sync_cb)
    cat.close_database()
    mm.cat_thread = None
    print('thread finished')


class MediaManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MediaManager, self).__init__(*args, **kwargs)

        self.catalog = None
        self.view_type = MEDIUM_THUMBNAILS
        self.resized = False
        self.mediafile_selected = None
        self.cat_thread = None
        self.db_updated = False
        self.thumb_sel = None
        self.files = []
        self.sort_method = FILTER_SORT_FILENAME
        self.sort_ascend = True

        self.InitUI()

    def InitUI(self):
        menubar = wx.MenuBar()
        catMenu = wx.Menu()
        catNew = catMenu.Append(wx.ID_ANY, 'New Catalog', 'Create New Catalog')
        catOpen = catMenu.Append(wx.ID_ANY, 'Open Catalog', 'Open Existing Catalog')
        catEdit = catMenu.Append(wx.ID_ANY, 'Edit Catalog', 'Edit Opened Catalog')
        catSync = catMenu.Append(wx.ID_ANY, 'Sync Catalog files', 'Sync Opened Catalog files')
        catClose = catMenu.Append(wx.ID_ANY, 'Close Catalog files', 'Close Opened Catalog files')
        catMenu.AppendSeparator()
        catExit = catMenu.Append(wx.ID_EXIT, 'Quit', 'Quit Application')
        menubar.Append(catMenu, '&Catalog')

        self.Bind(wx.EVT_MENU, self.OnNewCatalog, catNew)
        self.Bind(wx.EVT_MENU, self.OnOpenCatalog, catOpen)
        self.Bind(wx.EVT_MENU, self.OnEditCatalog, catEdit)
        self.Bind(wx.EVT_MENU, self.OnSyncCatalog, catSync)
        self.Bind(wx.EVT_MENU, self.OnCloseCatalog, catClose)
        self.Bind(wx.EVT_MENU, self.OnQuit, catExit)

        viewMenu = wx.Menu()
        viewSmall = viewMenu.Append(wx.ID_ANY, 'Small Thumbnails')
        viewMedium = viewMenu.Append(wx.ID_ANY, 'Medium Thumbnails')
        viewLarge = viewMenu.Append(wx.ID_ANY, 'Large Thumbnails')
        #viewList = viewMenu.Append(wx.ID_ANY, 'Detailed View')
        menubar.Append(viewMenu, '&View')

        self.Bind(wx.EVT_MENU, self.OnViewSmall, viewSmall)
        self.Bind(wx.EVT_MENU, self.OnViewMedium, viewMedium)
        self.Bind(wx.EVT_MENU, self.OnViewLarge, viewLarge)
        #self.Bind(wx.EVT_MENU, self.OnViewList, viewList)

        self.SetMenuBar(menubar)

        vbox = wx.BoxSizer(wx.VERTICAL)

        tb = wx.ToolBar(self, -1)
        tbNew = tb.AddTool(wx.ID_ANY, '', wx.ArtProvider.GetBitmap(wx.ART_NEW))
        tbOpen = tb.AddTool(wx.ID_ANY, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        tbEdit = tb.AddTool(wx.ID_ANY, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        tbClose = tb.AddTool(wx.ID_ANY, '', wx.ArtProvider.GetBitmap(wx.ART_CLOSE))
        tb.Realize()
        self.Bind(wx.EVT_TOOL, self.OnNewCatalog, tbNew)
        self.Bind(wx.EVT_TOOL, self.OnOpenCatalog, tbOpen)
        self.Bind(wx.EVT_TOOL, self.OnEditCatalog, tbEdit)
        self.Bind(wx.EVT_TOOL, self.OnCloseCatalog, tbClose)
        vbox.Add(tb, 0, flag=wx.EXPAND)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.leftPanel = LeftPanel(self, size=(300, -1))
        hbox.Add(self.leftPanel, 0, flag=wx.EXPAND)

        ivbox = wx.BoxSizer(wx.VERTICAL)

        ihbox = wx.BoxSizer(wx.HORIZONTAL)
        ihbox.AddStretchSpacer()
        ihbox.Add(wx.StaticText(self, label='sort by '), 0)
        sort_choices = ('None', 'Filename', 'Created Time', 'Last Played Time', 'Duration', )
        self.sortChoice = wx.Choice(self, choices=sort_choices)
        self.sortChoice.SetSelection(self.sort_method)
        self.Bind(wx.EVT_CHOICE, self.OnSortChange, self.sortChoice)
        ihbox.Add(self.sortChoice, 0)
        ascend_choices = ('Ascend', 'Descend')
        self.ascendChoice = wx.Choice(self, choices=ascend_choices)
        if self.sort_ascend:
            self.ascendChoice.SetSelection(0)
        else:
            self.ascendChoice.SetSelection(1)
        self.Bind(wx.EVT_CHOICE, self.OnAscendChange, self.ascendChoice)
        ihbox.Add(self.ascendChoice, 0)
        ivbox.Add(ihbox, 0, wx.EXPAND)

        files_ctrl = wx.ListCtrl(self, style=wx.LC_ICON|wx.LC_SINGLE_SEL|wx.BORDER_SUNKEN|wx.LC_AUTOARRANGE)
        files_ctrl.InsertColumn(0, 'thumbnail', width=360)
        files_ctrl.InsertColumn(1, 'filename', width=200)
        files_ctrl.InsertColumn(2, 'size', width=100)
        files_ctrl.InsertColumn(3, 'duration', width=100)
        files_ctrl.InsertColumn(4, 'path', width=360)
        files_ctrl.SetAutoLayout(True)
        ivbox.Add(files_ctrl, 1, flag=wx.ALL|wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)

        self.image_list = wx.ImageList(360, 203)
        files_ctrl.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnFileSelect, files_ctrl)
        #self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnFileRight, files_ctrl)
        self.files_ctrl = files_ctrl

        self.rightPanel = RightPanel(self, size=(300, -1))
        hbox.Add(self.rightPanel, 0, flag=wx.EXPAND)
        vbox.Add(hbox, 1, flag=wx.EXPAND)

        thumbs_ctrl = wx.ListCtrl(self, size=(240 * 50, 177),  style=wx.LC_ICON|wx.LC_SINGLE_SEL|wx.LC_ALIGN_LEFT|wx.LC_AUTOARRANGE)
        self.thumbs_list = wx.ImageList(240, 135)
        thumbs_ctrl.SetImageList(self.thumbs_list, wx.IMAGE_LIST_NORMAL)
        vbox.Add(thumbs_ctrl, 0, wx.EXPAND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnThumbSelect, thumbs_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnThumbDClick, thumbs_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnThumbRight, thumbs_ctrl)
        self.thumbs_ctrl = thumbs_ctrl

        self.db_timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnDbTimer)

        self.thumbRightMenu = wx.Menu()
        menuActor = self.thumbRightMenu.Append(wx.ID_ANY, 'Set As Actor Image')
        menuCover = self.thumbRightMenu.Append(wx.ID_ANY, 'Set As Cover Image')
        self.Bind(wx.EVT_MENU, self.OnActor, menuActor)
        self.Bind(wx.EVT_MENU, self.OnCover, menuCover)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        self.SetSize((720, 640))
        self.SetTitle('Yet Another Media Manager')
        self.Centre()

    def OnSortChange(self, e):
        self.sort_method = self.sortChoice.GetSelection()
        self.OnViewChange(self.view_type)

    def OnAscendChange(self, e):
        if self.ascendChoice.GetSelection():
            self.sort_ascend = False
        else:
            self.sort_ascend = True
        self.OnViewChange(self.view_type)

    def OnCloseCatalog(self, e):
        if not self.catalog:
            return
        self.catalog.close_database()
        self.catalog = None
        self.OnViewChange(self.view_type)

    def OnDbTimer(self, e):
        if self.db_updated:
            self.catalog.reload_files()
            self.OnViewChange(self.view_type)
            self.db_updated = False
        if self.cat_thread and self.cat_thread.is_alive():
            self.db_timer.Start(500)
        else:
            self.db_updated = False

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

    def select_mediafile(self, mf):
        index = 0
        for mf_i in self.files:
            if mf == mf_i:
                break
            index += 1
        if index == len(self.catalog):
            self.mediafile_selected = None
        else:
            self.files_ctrl.Select(index)

    def OnViewChange(self, type):
        self.view_type = type
        self.files_ctrl.DeleteAllItems()
        if type == SMALL_THUMBNAILS or type == DETAIL_THUMBNAILS:
            self.image_list = wx.ImageList(180, 101)
        elif type == MEDIUM_THUMBNAILS:
            self.image_list = wx.ImageList(240, 135)
        elif type == LARGE_THUMBNAILS:
            self.image_list = wx.ImageList(360, 203)
        self.files_ctrl.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)

        if not self.catalog:
            return
        self.files = self.catalog.filter(sort=self.sort_method,
                                         ascend=self.sort_ascend)
        if not self.files:
            return

        if type == DETAIL_THUMBNAILS:
            self.files_ctrl.SetWindowStyleFlag(wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_AUTOARRANGE)
        else:
            self.files_ctrl.SetWindowStyleFlag(wx.LC_ICON|wx.LC_SINGLE_SEL|wx.LC_AUTOARRANGE)

        index = 0
        for mf in self.files:
            if type == DETAIL_THUMBNAILS:
                self.files_ctrl.InsertItem(index, str(mf.id))
                self.files_ctrl.SetItem(index, 1, mf.filename)
                self.files_ctrl.SetItem(index, 2, '%dMB' % int(mf.size/1024 / 1024))
                if mf.duration:
                    hours = int(mf.duration/3600)
                    minutes = int((mf.duration - hours * 3600) / 60)
                    seconds = mf.duration - hours * 3600 - minutes * 60
                else:
                    hours = 0
                    minutes = 0
                    seconds = 0
                self.files_ctrl.SetItem(index, 3, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))
                self.files_ctrl.SetItem(index, 4, mf.abspath())
            else:
                self.files_ctrl.InsertItem(index, mf.filename)

            jpg_bytes = mf.get_coverjpg()
            if jpg_bytes:
                data_stream = io.BytesIO(jpg_bytes)
                image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
            else:
                image = wx.Image(360, 203)
            image = self.get_scaled_image(self.image_list, image)
            bmp = wx.Bitmap(image)
            self.image_list.Add(bmp)
            self.files_ctrl.SetItemImage(index, index)

            index += 1

        self.select_mediafile(self.mediafile_selected)
        self.GetSizer().Layout()
        self.Update()

    def OnViewSmall(self, e):
        self.OnViewChange(SMALL_THUMBNAILS)

    def OnViewMedium(self, e):
        self.OnViewChange(MEDIUM_THUMBNAILS)

    def OnViewLarge(self, e):
        self.OnViewChange(LARGE_THUMBNAILS)

    def OnViewList(self, e):
        self.OnViewChange(DETAIL_THUMBNAILS)

    def OnActor(self, e):
        pass

    def OnCover(self, e):
        mf = self.mediafile_selected
        mf.set_cover_id(self.thumb_sel)
        self.OnViewChange(self.view_type)

    def OnThumbSelect(self, e):
        self.thumb_sel = self.thumbs_ctrl.GetFirstSelected()
        if self.thumb_sel < 0 or not self.mediafile_selected:
            return

    def OnThumbDClick(self, e):
        thumb = self.mediafile_selected.thumbnails[self.thumb_sel]
        print(self.mediafile_selected.abspath())
        run_list = ('C:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini64.exe',
                    '%s'%self.mediafile_selected.abspath(),
                    '/seek=%d' % thumb[0])
        subprocess.Popen(run_list)
        self.mediafile_selected.set_lastplayed(datetime.datetime.now())

    def OnThumbRight(self, e):
        self.thumb_item_clicked = e.GetText()
        self.thumbs_ctrl.PopupMenu(self.thumbRightMenu, e.GetPoint())

    def OnFileSelect(self, e):
        sel = self.files_ctrl.GetFirstSelected()
        if sel < 0:
            return
        mf = self.files[sel]

        if mf !=self.mediafile_selected:
            self.thumbs_ctrl.DeleteAllItems()
            self.thumbs_list.RemoveAll()
            self.mediafile_selected = mf
        self.rightPanel.set_mediafile(mf)
        index = 0
        for tb in mf.thumbnails:
            time = tb[0]
            jpg = tb[1]

            hours = int(time/3600)
            minutes = int((time - hours * 3600) / 60)
            seconds = int(time - hours * 3600 - minutes * 60)
            self.thumbs_ctrl.InsertItem(index, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))

            data_stream = io.BytesIO(jpg)
            image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
            image = self.get_scaled_image(self.thumbs_list, image)
            bmp = wx.Bitmap(image)
            self.thumbs_list.Add(bmp)
            self.thumbs_ctrl.SetItemImage(index, index)

            index += 1

    def OnNewCatalog(self, e):
        with CatalogDialog(self, title="New Catalog") as catDialog:
            if catDialog.ShowModal() == wx.ID_CANCEL:
                return

            abspath = os.path.abspath(catDialog.catPath.GetLabelText())
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

            for new_topdir in new_topdirs:
                found = False
                for topdir in self.catalog.topdir_list:
                    if new_topdir == topdir.abspath:
                        found = True
                        break
                if not found:
                    self.catalog.add_topdir(new_topdir)

            td_i = 0
            while td_i < len(self.catalog.topdir_list):
                topdir = self.catalog.topdir_list[td_i]
                if not (topdir.abspath in new_topdirs):
                    print('del')
                    self.catalog.del_topdir(topdir.abspath)
                    td_i -= 1
                td_i += 1

            print(new_topdirs)
            print(self.catalog.topdir_list)

            self.statusbar.SetStatusText('Start Scanning files...')
            self.OnSyncCatalog(e)

    def OnOpenCatalog(self, e):
        with wx.FileDialog(self, "Open Catalog", wildcard='catalog files (*.nmcat)|*.nmcat',
                           style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.catalog = Catalog(db_abspath=pathname)
            self.catalog.open_database()
            self.OnViewChange(self.view_type)

            self.statusbar.SetStatusText('Start Scanning files...')
            self.OnSyncCatalog(e)

    def OnSyncCatalog(self, e):
        if self.cat_thread:
            return
        self.cat_thread = threading.Thread(target=cat_thread_func, args=(self,))
        self.cat_thread.start()
        self.db_timer.Start(500)

    def OnFileRight(self, e):
        pass

    def OnQuit(self, e):
        self.thumbRightMenu.Destroy()
        self.catalog.kill_thread = True
        if self.cat_thread:
            self.cat_thread.join()
        self.Close()


if __name__ == '__main__':
    app = wx.App()
    mm = MediaManager(None)
    mm.Show()
    app.MainLoop()