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

import wx
import os
import io

import icons


class LeftPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(LeftPanel, self).__init__(*args, **kwargs)

        self.mm_window = None

        self.file_filter = ''
        self.actor_list = []
        self.actor_selected = []
        self.tag_list = []
        self.tag_selected = []

        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='Filters'), 0)
        hbox.AddStretchSpacer()
        self.clearButton = wx.Button(self, size=(100, -1), label='Clear Filters')
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.clearButton)
        hbox.Add(self.clearButton, 0, wx.EXPAND)
        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.AddSpacer(3)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='From Path : '), 0)
        self.fileText = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnFileFilter, self.fileText)
        hbox.Add(self.fileText, 1, wx.EXPAND)
        dstream = io.BytesIO(icons.filter_button)
        image = wx.Image(dstream, type=wx.BITMAP_TYPE_PNG)
        image.Rescale(16, 16)
        fileSetBtn = wx.BitmapButton(self, bitmap=wx.Bitmap(image))
        self.Bind(wx.EVT_BUTTON, self.OnFileFilter, fileSetBtn)
        hbox.Add(fileSetBtn)
        vbox.Add(hbox, 0, wx.EXPAND)

        self.actorList = wx.ListCtrl(self, size=(300, -1), style=wx.LC_LIST |
                                                                 wx.LC_ALIGN_TOP |
                                                                 wx.LC_EDIT_LABELS)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnActorSelect, self.actorList)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnActorSelect, self.actorList)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnActorEdit, self.actorList)
        vbox.Add(self.actorList, 1, wx.EXPAND)

        self.tagList = wx.ListCtrl(self, size=(300, -1), style=wx.LC_LIST |
                                                               wx.LC_ALIGN_TOP |
                                                               wx.LC_EDIT_LABELS)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTagSelect, self.tagList)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnTagSelect, self.tagList)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnTagEdit, self.tagList)
        vbox.Add(self.tagList, 1, wx.EXPAND)

        self.update_timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnUpdateTimer)

        self.clearButton.Disable()
        self.fileText.Disable()
        self.actorList.Disable()
        self.tagList.Disable()

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

    def OnActorEdit(self, e):
        self.mm_window.catalog.modify_actor(self.actorList.GetItemText(e.GetIndex()),
                                            e.GetLabel())
        self.update_lists()
        self.mm_window.rightPanel.set_mediafiles((self.mm_windows.rightPanel.files_selected))

    def OnTagEdit(self, e):
        self.mm_window.catalog.modify_tag(self.tagList.GetItemText(e.GetIndex()),
                                          e.GetLabel())
        self.update_lists()
        self.mm_window.rightPanel.set_mediafiles((self.mm_windows.rightPanel.files_selected))

    def OnFileFilter(self, e):
        self.file_filter = self.fileText.GetValue()
        self.mm_window.update_view()

    def OnUpdateTimer(self, e):
        self.update_timer.Stop()
        self.mm_window.update_view()

    def OnActorSelect(self, e):
        self.actor_selected = []
        idx = self.actorList.GetFirstSelected()
        if idx < 0:
            self.update_timer.Start(10)
            return
        name = self.actorList.GetItemText(idx)
        self.actor_selected.append(name)
        while idx >= 0:
            idx = self.actorList.GetNextSelected(idx)
            if idx < 0:
                break
            name = self.actorList.GetItemText(idx)
            self.actor_selected.append(name)
        self.actor_selected.sort()
        self.update_timer.Start(10)

    def OnTagSelect(self, e):
        self.tag_selected = []
        idx = self.tagList.GetFirstSelected()
        if idx < 0:
            self.update_timer.Start(10)
            return
        tag = self.tagList.GetItemText(idx)
        self.tag_selected.append(tag)
        while idx >= 0:
            idx = self.tagList.GetNextSelected(idx)
            if idx < 0:
                break
            name = self.tagList.GetItemText(idx)
            self.tag_selected.append(name)
        self.tag_selected.sort()
        self.update_timer.Start(10)

    def OnClear(self, e):
        self.actor_selected = []
        for n in range(self.actorList.GetItemCount()):
            self.actorList.Select(n, on=0)
        self.tag_selected = []
        for n in range(self.tagList.GetItemCount()):
            self.tagList.Select(n, on=0)
        self.file_filter = ''
        self.fileText.SetValue('')
        self.mm_window.update_view()

    def update_lists(self):
        self.actor_list.sort()
        self.actorList.DeleteAllItems()
        for name in self.actor_list:
            idx = self.actorList.Append((name,))
            if name in self.actor_selected:
                self.actorList.Select(idx)

        self.tag_list.sort()
        self.tagList.DeleteAllItems()
        for tag in self.tag_list:
            idx = self.tagList.Append((tag,))
            if tag in self.tag_selected:
                self.tagList.Select(idx)

    def set_mm_window(self, mm):
        self.mm_window = mm

        self.actor_list = []
        self.tag_list = []
        if not mm or not mm.catalog:
            self.update_lists()

            self.clearButton.Disable()
            self.fileText.Disable()
            self.actorList.Disable()
            self.tagList.Disable()
            return

        for actor in mm.catalog.actor_list:
            self.actor_list.append(actor)
        for tag in mm.catalog.tag_list:
            self.tag_list.append(tag)

        self.update_lists()

        self.clearButton.Enable()
        self.fileText.Enable()
        self.actorList.Enable()
        self.tagList.Enable()

    def add_actor(self, actor):
        if actor in self.actor_list:
            return
        self.actor_list.append(actor)
        self.actor_list.sort()
        self.update_lists()

    def add_tag(self, tag):
        if tag in self.tag_list:
            return
        self.tag_list.append(tag)
        self.tag_list.sort()
        self.update_lists()


class RightPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(RightPanel, self).__init__(*args, **kwargs)

        self.mm_window = None
        self.files_selected = []

        self.actor_list = []
        self.actor_selected = []
        self.tag_list = []
        self.tag_selected = []

        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.propertyList = wx.ListCtrl(self, size=(300, 145), style=wx.LC_REPORT |
                                                                     wx.BORDER_SUNKEN |
                                                                     wx.LC_HRULES |
                                                                     wx.LC_VRULES)
        self.propertyList.InsertColumn(0, 'Property', width=100)
        self.propertyList.InsertColumn(1, 'Value', width=195)

        self.propertyList.InsertItem(0, 'Filename')
        self.propertyList.InsertItem(1, 'Path')
        self.propertyList.InsertItem(2, 'Stars')
        self.propertyList.InsertItem(3, 'Size')
        self.propertyList.InsertItem(4, 'Duration')
        self.propertyList.InsertItem(5, 'LastPlayed')
        self.set_property()

        vbox.Add(self.propertyList)
        vbox.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ivbox = wx.BoxSizer(wx.VERTICAL)
        ivbox.Add(wx.StaticText(self, label='Actors'), 0)
        ihbox = wx.BoxSizer(wx.HORIZONTAL)
        self.actorText = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnActorAdd, self.actorText)
        ihbox.Add(self.actorText, 1, wx.EXPAND)
        dstream = io.BytesIO(icons.add_button)
        image = wx.Image(dstream, type=wx.BITMAP_TYPE_PNG)
        image.Rescale(14, 14)
        fileSetBtn = wx.BitmapButton(self, bitmap=wx.Bitmap(image))
        self.Bind(wx.EVT_BUTTON, self.OnActorAdd, fileSetBtn)
        ihbox.Add(fileSetBtn, 0, wx.EXPAND)
        ivbox.Add(ihbox)
        self.actorList = wx.ListCtrl(self, size=(150, -1), style=wx.LC_REPORT |
                                                                 wx.LC_NO_HEADER |
                                                                 wx.LC_SINGLE_SEL)
        self.actorList.EnableCheckBoxes()
        self.actorList.InsertColumn(0, 'Icon', width=20)
        self.actorList.InsertColumn(1, 'name', width=120)
        self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnActorCheck, self.actorList)
        self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnActorUncheck, self.actorList)
        ivbox.Add(self.actorList, 1, wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)

        ivbox = wx.BoxSizer(wx.VERTICAL)
        ivbox.Add(wx.StaticText(self, label='Tags'), 0)
        ihbox = wx.BoxSizer(wx.HORIZONTAL)
        self.tagText = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTagAdd, self.tagText)
        ihbox.Add(self.tagText, 1, wx.EXPAND)
        dstream = io.BytesIO(icons.add_button)
        image = wx.Image(dstream, type=wx.BITMAP_TYPE_PNG)
        image.Rescale(14, 14)
        fileSetBtn = wx.BitmapButton(self, bitmap=wx.Bitmap(image))
        self.Bind(wx.EVT_BUTTON, self.OnTagAdd, fileSetBtn)
        ihbox.Add(fileSetBtn, 0, wx.EXPAND)
        ivbox.Add(ihbox)
        self.tagList = wx.ListCtrl(self, size=(150, -1), style=wx.LC_REPORT |
                                                               wx.LC_NO_HEADER |
                                                               wx.LC_SINGLE_SEL)
        self.tagList.EnableCheckBoxes()
        self.tagList.InsertColumn(0, 'Icon', width=20)
        self.tagList.InsertColumn(1, 'name', width=120)
        self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnTagCheck, self.tagList)
        self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnTagUncheck, self.tagList)
        ivbox.Add(self.tagList, 1, wx.EXPAND)
        hbox.Add(ivbox, 1, wx.EXPAND)

        vbox.Add(hbox, 1, wx.EXPAND)

        self.propertyList.Disable()
        self.actorText.Disable()
        self.actorList.Disable()
        self.tagText.Disable()
        self.tagList.Disable()

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

    def OnActorCheck(self, e):
        sel = e.GetIndex()
        name = self.actorList.GetItemText(sel, 1)
        for mf in self.files_selected:
            mf.add_actor(name)

    def OnActorUncheck(self, e):
        sel = e.GetIndex()
        name = self.actorList.GetItemText(sel, 1)

        for mf in self.files_selected:
            if not (name in mf.actor_list):
                return

        for mf in self.files_selected:
            mf.del_actor(name)

    def OnActorAdd(self, e):
        name = self.actorText.GetValue()
        if not name:
            return

        if not (name in self.actor_list):
            self.actor_list.append(name)
            self.mm_window.leftPanel.add_actor(name)
        if not (name in self.actor_selected):
            self.actor_selected.append(name)
            for mf in self.files_selected:
                mf.add_actor(name)

        self.update_actor()

    def update_actor(self):
        self.actor_list.sort()
        self.actor_selected.sort()
        self.actorList.DeleteAllItems()
        for actor in self.actor_list:
            idx = self.actorList.Append(('', actor,))
            if actor in self.actor_selected:
                self.actorList.CheckItem(idx, check=True)
            else:
                self.actorList.CheckItem(idx, check=False)
        self.actorText.SetValue('')

    def OnTagCheck(self, e):
        sel = e.GetIndex()
        tag = self.tagList.GetItemText(sel, 1)
        for mf in self.files_selected:
            mf.add_tag(tag)

    def OnTagUncheck(self, e):
        sel = e.GetIndex()
        name = self.tagList.GetItemText(sel, 1)

        for mf in self.files_selected:
            if not (tag in mf.tag_list):
                return

        for mf in self.files_selected:
            mf.add_tag(tag)

    def OnTagAdd(self, e):
        tag = self.tagText.GetValue()
        if not tag:
            return

        if not (tag in self.tag_list):
            self.tag_list.append(tag)
            self.mm_window.leftPanel.add_tag(tag)
        if not (tag in self.tag_selected):
            self.tag_selected.append(tag)
            for mf in self.files_selected:
                mf.add_tag(tag)

        self.update_tag()

    def update_tag(self):
        self.tag_list.sort()
        self.tag_selected.sort()
        self.tagList.DeleteAllItems()
        for tag in self.tag_list:
            idx = self.tagList.Append(('', tag,))
            if tag in self.tag_selected:
                self.tagList.CheckItem(idx, check=True)
            else:
                self.tagList.CheckItem(idx, check=False)
        self.tagText.SetValue('')

    def set_property(self):
        if len(self.files_selected) != 1:
            self.propertyList.DeleteAllItems()
            self.propertyList.InsertItem(0, 'Filename')
            if not self.files_selected:
                self.propertyList.SetItem(0, 1, '')
            else:
                self.propertyList.SetItem(0, 1, 'Multi-Files')
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
            return

        media_file = self.files_selected[0]
        self.propertyList.DeleteAllItems()
        self.propertyList.InsertItem(0, 'Filename')
        self.propertyList.SetItem(0, 1, media_file.filename)
        self.propertyList.InsertItem(1, 'Path')
        self.propertyList.SetItem(1, 1, media_file.abspath)
        self.propertyList.InsertItem(2, 'Resolution')
        if media_file.width and media_file.height:
            self.propertyList.SetItem(2, 1, '%d x %d' % (media_file.width, media_file.height))
        else:
            self.propertyList.SetItem(2, 1, '')

        self.propertyList.InsertItem(3, 'Size')
        self.propertyList.SetItem(3, 1, '%dMB' % (media_file.size // (1024 * 1024)))

        self.propertyList.InsertItem(4, 'Duration')
        if media_file.duration:
            hours = media_file.duration // 3600
            minutes = (media_file.duration - hours * 3600) // 60
            seconds = int(media_file.duration) % 60
            self.propertyList.SetItem(4, 1, '%2.2d:%2.2d:%2.2d' % (hours, minutes, seconds))
        else:
            self.propertyList.SetItem(4, 1, 'no info')

        self.propertyList.InsertItem(5, 'LastPlayed')
        if media_file.lastplay:
            self.propertyList.SetItem(5, 1, str(media_file.lastplay))
        else:
            self.propertyList.SetItem(5, 1, '')

    def set_mediafiles(self, mf_list):
        self.files_selected = mf_list

        if not self.files_selected:
            self.actor_list = []
            self.actor_selected = []
            self.tag_list = []
            self.tag_selected = []
            self.update_actor()
            self.update_tag()
            self.set_property()
            self.actorText.Disable()
            self.actorList.Disable()
            self.tagText.Disable()
            self.tagList.Disable()
            return

        catalog = self.files_selected[0].catalog

        self.actor_list = []
        for actor in catalog.actor_list:
            self.actor_list.append(actor)
        self.actor_selected = []
        for sactor in self.actor_list:
            all_found = True
            for mf in self.files_selected:
                if not (sactor in mf.actor_list):
                    all_found = False
                    break
            if all_found:
                self.actor_selected.append(sactor)

        self.tag_list = []
        for tag in catalog.tag_list:
            self.tag_list.append(tag)
        self.tag_selected = []
        for stag in self.tag_list:
            all_found = True
            for mf in self.files_selected:
                if not (stag in mf.tag_list):
                    all_found = False
                    break
            if all_found:
                self.tag_selected.append(stag)
        self.update_actor()
        self.update_tag()
        self.set_property()

        self.actorText.Enable()
        self.actorList.Enable()
        self.tagText.Enable()
        self.tagList.Enable()

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
       with wx.FileDialog(self, "New Catalog File", wildcard='catalog files (*.yamm)|*.yamm',
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
