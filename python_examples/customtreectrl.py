import wx, wx.lib.customtreectrl as CT

class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size=(600, 600), pos=(200, 200))
        
        self.splitter_window = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.splitter_window.SetMinimumPaneSize(20)
        self.left_panel = wx.Panel(self.splitter_window, -1)
        self.right_panel = wx.Panel(self.splitter_window, -1)
        
        self.tree = CT.CustomTreeCtrl(self.left_panel, 1002, pos=(0, 0), 
            style=wx.TR_DEFAULT_STYLE | 
            wx.TR_HAS_VARIABLE_ROW_HEIGHT | 
            wx.TR_HAS_BUTTONS | 
            wx.TR_FULL_ROW_HIGHLIGHT | 
            wx.TR_MULTIPLE | 
            wx.TR_EDIT_LABELS)
        self.root = self.tree.AddRoot("Root Item")
        
        offset_lists = ["Clearance Reports", "Other Offsets"]
        offset_list_combo_box = wx.ComboBox(self.right_panel, -1, choices=offset_lists)
        
        #Sizers
        offset_sizer = wx.BoxSizer(wx.VERTICAL)
        offset_sizer.Add(offset_list_combo_box, 0, wx.EXPAND)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.tree, 1, wx.EXPAND)
        self.left_panel.SetSizer(vbox)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(offset_sizer, 1, wx.EXPAND)
        self.right_panel.SetSizer(vbox2)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.splitter_window.SplitVertically(self.left_panel, self.right_panel)
        main_sizer.Add(self.splitter_window, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndLabelEdit)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        self.Bind(wx.EVT_KEY_DOWN, self.enterpressed)
        self.tree.Bind(wx.EVT_KEY_DOWN, self.enterpressed)
        self.Bind(wx.EVT_KEY_DOWN, self.enterpressed, self.tree)
        self.Bind(wx.EVT_COMMAND_ENTER, self.enterpressed)
        self.Bind(wx.EVT_TEXT_ENTER, self.enterpressed)
        
        self.Show(True)
    
    def OnBeginLabelEdit(self, event):
        pass
    def OnEndLabelEdit(self, event):
        text = self.tree.GetEditControl().GetValue()
        item_being_edited = self.tree.GetSelection()
        self.tree.SetItemText(item_being_edited, text)
    def enterpressed(self, event):
        print "pressed enter"
        
app = wx.PySimpleApp()
frame = MainWindow(None, -1, "Test")
app.MainLoop()