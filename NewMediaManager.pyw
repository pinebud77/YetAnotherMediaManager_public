#!/usr/bin/env python3

import subprocess
import sys
import wx
import io
import threading

from catalog import Catalog


LARGE_THUMBNAILS = 0
MEDIUM_THUMBNAILS = 1
SMALL_THUMBNAILS = 2
DETAIL_THUMBNAILS = 3

class FileListCtrl(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_ICON |
                                                 wx.LC_SINGLE_SEL |
                                                 wx.BORDER_SUNKEN |
                                                 wx.LC_AUTOARRANGE)

mm_global = None

def mm_sync_cb(newfile, percent):
    global mm_global
    if newfile:
        mm_global.statusbar.SetStatusText('File Added: %s (%d%% synced)' % (newfile, percent))
    else:
        mm_global.statusbar.SetStatusText('Catalog Synced Finished')
    mm_global.db_updated = True

def cat_thread_func(mm):
    global mm_global
    mm_global = mm
    cat = Catalog(mm.catalog.filepath)
    cat.open_database()
    cat.sync_database(file_cb=mm_sync_cb)
    cat.close_database()


class MediaManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MediaManager, self).__init__(*args, **kwargs)

        self.catalog = None
        self.view_type = MEDIUM_THUMBNAILS
        self.resized = False
        self.mediafile_selected = None
        self.cat_thread = None
        self.db_updated = False

        self.InitUI()

    def InitUI(self):
        menubar = wx.MenuBar()
        catMenu = wx.Menu()
        catNew = catMenu.Append(wx.ID_ANY, 'New Catalog', 'Create New Catalog')
        catOpen = catMenu.Append(wx.ID_ANY, 'Open Catalog', 'Open Existing Catalog')
        catEdit = catMenu.Append(wx.ID_ANY, 'Edit Catalog', 'Edit Opened Catalog')
        catMenu.AppendSeparator()
        catSync = catMenu.Append(wx.ID_ANY, 'Sync Catalog files', 'Sync Opened Catalog files')
        catMenu.AppendSeparator()
        catExit = catMenu.Append(wx.ID_EXIT, 'Quit', 'Quit Application')
        menubar.Append(catMenu, '&Catalog')

        self.Bind(wx.EVT_MENU, self.OnNewCatalog, catNew)
        self.Bind(wx.EVT_MENU, self.OnOpenCatalog, catOpen)
        self.Bind(wx.EVT_MENU, self.OnEditCatalog, catEdit)
        self.Bind(wx.EVT_MENU, self.OnSyncCatalog, catSync)
        self.Bind(wx.EVT_MENU, self.OnQuit, catExit)

        viewMenu = wx.Menu()
        viewSmall = viewMenu.Append(wx.ID_ANY, 'Small Thumbnails')
        viewMedium = viewMenu.Append(wx.ID_ANY, 'Medium Thumbnails')
        viewLarge = viewMenu.Append(wx.ID_ANY, 'Large Thumbnails')
        viewList = viewMenu.Append(wx.ID_ANY, 'Detailed View')
        menubar.Append(viewMenu, '&View')

        self.Bind(wx.EVT_MENU, self.OnViewSmall, viewSmall)
        self.Bind(wx.EVT_MENU, self.OnViewMedium, viewMedium)
        self.Bind(wx.EVT_MENU, self.OnViewLarge, viewLarge)
        self.Bind(wx.EVT_MENU, self.OnViewList, viewList)

        self.SetMenuBar(menubar)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.Button(self, label='filter'), 0, flag=wx.EXPAND)

        files_ctrl = FileListCtrl(self)
        files_ctrl.InsertColumn(0, 'thumbnail', width=360)
        files_ctrl.InsertColumn(1, 'filename', width=200)
        files_ctrl.InsertColumn(2, 'size', width=100)
        files_ctrl.InsertColumn(3, 'duration', width=100)
        files_ctrl.InsertColumn(4, 'path', width=360)
        files_ctrl.SetAutoLayout(True)
        hbox.Add(files_ctrl, 1, flag=wx.ALL|wx.EXPAND)
        self.image_list = wx.ImageList(360, 203)
        files_ctrl.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnFileSelect, files_ctrl)
        self.files_ctrl = files_ctrl

        hbox.Add(wx.Button(self, label='tags'), 0, flag=wx.EXPAND)
        vbox.Add(hbox, 1, flag=wx.EXPAND)

        thumbs_ctrl = wx.ListCtrl(self, size=(240 * 50, 177),  style=wx.LC_ICON|wx.LC_SINGLE_SEL|wx.LC_ALIGN_LEFT|wx.LC_AUTOARRANGE)
        self.thumbs_list = wx.ImageList(240, 135)
        thumbs_ctrl.SetImageList(self.thumbs_list, wx.IMAGE_LIST_NORMAL)
        vbox.Add(thumbs_ctrl, 0, wx.EXPAND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnThumbSelect, thumbs_ctrl)
        self.thumbs_ctrl = thumbs_ctrl

        self.db_timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnDbTimer)

        self.SetSizer(vbox)

        self.SetAutoLayout(True)

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        self.SetSize((720, 640))
        self.SetTitle('New Media Manager')
        self.Centre()

    def OnDbTimer(self, e):
        if self.db_updated:
            self.catalog.reload_files()
            self.OnViewChange(self.view_type)
            self.db_updated = False
        if self.cat_thread.is_alive():
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
        for mf_i in self.catalog:
            if mf == mf_i:
                break
            index += 1
        if index == len(self.catalog):
            self.mediafile_selected = None
        else:
            self.files_ctrl.Select(index)

    def OnViewChange(self, type):
        self.view_type = type
        sel = self.files_ctrl.GetFirstSelected()
        if sel >= 0 and sel < len(self.catalog):
            self.mediafile_selected = self.catalog[sel]
        self.files_ctrl.DeleteAllItems()
        self.thumbs_ctrl.DeleteAllItems()
        if type == SMALL_THUMBNAILS or type == DETAIL_THUMBNAILS:
            self.image_list = wx.ImageList(180, 101)
        elif type == MEDIUM_THUMBNAILS:
            self.image_list = wx.ImageList(240, 135)
        elif type == LARGE_THUMBNAILS:
            self.image_list = wx.ImageList(360, 203)
        self.files_ctrl.SetImageList(self.image_list, wx.IMAGE_LIST_NORMAL)

        if not self.catalog:
            return

        if type == DETAIL_THUMBNAILS:
            self.files_ctrl.SetWindowStyleFlag(wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_AUTOARRANGE)
        else:
            self.files_ctrl.SetWindowStyleFlag(wx.LC_ICON|wx.LC_SINGLE_SEL|wx.LC_AUTOARRANGE)

        index = 0
        for mf in self.catalog:
            if type == DETAIL_THUMBNAILS:
                self.files_ctrl.InsertItem(index, str(mf.id))
                self.files_ctrl.SetItem(index, 1, mf.filename)
                self.files_ctrl.SetItem(index, 2, '%dMB' % int(mf.size/1024 / 1024))
                if mf.duration:
                    hours = int(mf.duration/3600)
                    minutes = int((mf.duration - hours * 60) / 360)
                    seconds = mf.duration - hours * 360 - minutes * 60
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

    def OnThumbSelect(self, e):
        sel = self.thumbs_ctrl.GetFirstSelected()
        if sel < 0 or not self.mediafile_selected:
            return
        thumb = self.mediafile_selected.thumbnails[sel]
        print(self.mediafile_selected.abspath())
        run_list = ('C:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini64.exe',
                    '%s'%self.mediafile_selected.abspath(),
                    '/seek=%d' % thumb[0])
        subprocess.Popen(run_list)

    def OnFileSelect(self, e):
        sel = self.files_ctrl.GetFirstSelected()
        if sel < 0:
            return
        self.thumbs_ctrl.DeleteAllItems()
        self.thumbs_list.RemoveAll()
        mf = self.catalog[sel]
        self.mediafile_selected = mf
        index = 0
        for tb in mf.thumbnails:
            time = tb[0]
            jpg = tb[1]

            hours = int(time/3600)
            minutes = int((time - hours * 60) / 60)
            seconds = int(time - hours * 360 - minutes * 60)
            self.thumbs_ctrl.InsertItem(index, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))

            data_stream = io.BytesIO(jpg)
            image = wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG)
            image = self.get_scaled_image(self.thumbs_list, image)
            bmp = wx.Bitmap(image)
            self.thumbs_list.Add(bmp)
            self.thumbs_ctrl.SetItemImage(index, index)

            index += 1

    def OnNewCatalog(self, e):
        pass

    def OnOpenCatalog(self, e):
        with wx.FileDialog(self, "Open Catalog", wildcard='catalog files (*.nmcat)|*.nmcat',
                           style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.catalog = Catalog(db_abspath=pathname)
            self.catalog.open_database()
            #self.catalog.sync_database()
            self.OnViewChange(self.view_type)

    def OnEditCatalog(self, e):
        pass

    def OnSyncCatalog(self, e):
        if self.cat_thread:
            return
        self.cat_thread = threading.Thread(target=cat_thread_func, args=(self,))
        self.cat_thread.start()
        self.db_timer.Start(500)

    def OnQuit(self, e):
        self.catalog.kill_thread = True
        self.cat_thread.join()
        self.Close()


if __name__ == '__main__':
    app = wx.App()
    mm = MediaManager(None)
    mm.Show()
    app.MainLoop()