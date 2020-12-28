#!/usr/bin/env python3

import sys
import wx

import filemanager.catalog.Catalog as Catalog


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
        files_ctrl.InsertColumn(0, 'thumbnail')
        files_ctrl.InsertColumn(1, 'filename')
        files_ctrl.InsertColumn(2, 'size')
        files_ctrl.InsertColumn(3, 'duration')
        files_ctrl.InsertColumn(4, 'path')
        hbox.Add(files_ctrl, 1, flag=wx.ALL|wx.EXPAND)

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