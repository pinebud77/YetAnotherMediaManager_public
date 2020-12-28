#!/usr/bin/env python3

import sys
import wx
import io

from catalog import Catalog


class MediaManager(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MediaManager, self).__init__(*args, **kwargs)
        self.InitUI()

        self.catalog = None

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
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnNewCatalog, catNew)
        self.Bind(wx.EVT_MENU, self.OnOpenCatalog, catOpen)
        self.Bind(wx.EVT_MENU, self.OnEditCatalog, catEdit)
        self.Bind(wx.EVT_MENU, self.OnSyncCatalog, catSync)
        self.Bind(wx.EVT_MENU, self.OnQuit, catExit)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.Button(self, label='filter'), 0, flag=wx.EXPAND)

        files_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        files_ctrl.InsertColumn(0, 'thumbnail', width=360)
        files_ctrl.InsertColumn(1, 'filename', width=200)
        files_ctrl.InsertColumn(2, 'size', width=100)
        files_ctrl.InsertColumn(3, 'duration', width=100)
        files_ctrl.InsertColumn(4, 'path', width=360)
        hbox.Add(files_ctrl, 1, flag=wx.ALL|wx.EXPAND)
        self.files_ctrl = files_ctrl
        self.image_list = wx.ImageList(360, 240)
        self.files_ctrl.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)

        hbox.Add(wx.Button(self, label='tag'), 0, flag=wx.EXPAND)
        vbox.Add(hbox, 1, flag=wx.EXPAND)

        vbox.Add(wx.Button(self, label='thumbnails'), flag=wx.EXPAND)
        self.SetSizer(vbox)

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        self.SetSize((640, 480))
        self.SetTitle('New Media Manager')
        self.Centre()

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
            self.catalog.sync_database()
            self.files_ctrl.DeleteAllItems()
            self.image_list.RemoveAll()
            index = 0
            for mf in self.catalog:
                self.files_ctrl.InsertItem(index, str(mf.id))
                self.files_ctrl.SetItem(index, 1, mf.filename)
                self.files_ctrl.SetItem(index, 2, '%dMB' % int(mf.size/1024 / 1024))
                if mf.duration:
                    hours = int(mf.duration/360)
                    minutes = int((mf.duration - hours * 60) / 360)
                    seconds = mf.duration - hours * 360 - minutes * 60
                else:
                    hours = 0
                    minutes = 0
                    seconds = 0
                self.files_ctrl.SetItem(index, 3, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))
                self.files_ctrl.SetItem(index, 4, mf.abspath())

                jpg_bytes = mf.get_coverjpg()
                if jpg_bytes:
                    data_stream = io.BytesIO(jpg_bytes)
                    bmp = wx.Bitmap(wx.Image(data_stream, type=wx.BITMAP_TYPE_JPEG))
                    self.image_list.Add(bmp)
                    self.files_ctrl.SetItemImage(index, index)

                index += 1

    def OnEditCatalog(self, e):
        pass

    def OnSyncCatalog(self, e):
        pass

    def OnQuit(self, e):
        self.Close()


if __name__ == '__main__':
    app = wx.App()
    mm = MediaManager(None)
    mm.Show()
    app.MainLoop()