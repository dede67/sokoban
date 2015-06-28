#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.lib.mixins.listctrl as listmix


# ###########################################################
# Ein Dialog zum Einstellen der Farben.
class SetupColorDialog(wx.Dialog):
  def __init__(self, parent, col, col_dict):
    super(SetupColorDialog, self).__init__(parent=parent, title="Setup colors")
    self.col=col

    st=[]       # StaticText
    self.cpc=[] # ColourPickerCtrl
    sc=[]       # Colour
    for i in range(len(self.col)):
      st.append(wx.StaticText(self, label=self.col[i][0]+":"))
      self.cpc.append(wx.ColourPickerCtrl(self, wx.ID_ANY))
      self.cpc[i].SetColour(col_dict[self.col[i][1]])

    ok=wx.Button(self,      wx.ID_OK,     "&Ok")
    cancel=wx.Button(self,  wx.ID_CANCEL, "&Cancel")
    reset=wx.Button(self,   wx.ID_ANY,    "&Reset to default")
    reset.Bind(wx.EVT_BUTTON, self.reset_selected)
    ok.SetDefault()
    ok.SetFocus()

    sizer=wx.GridBagSizer()

    flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL
    border=5
    for i in range(len(st)):
      sizer.Add(st[i],        pos=(i//2, (i%2)*2+0), flag=flag, border=border)
      sizer.Add(self.cpc[i],  pos=(i//2, (i%2)*2+1), flag=flag, border=border)

    sizer.Add(wx.StaticLine(self),  pos=(len(st)//2+1, 0), span=(1, 4),  flag=wx.ALL|wx.GROW, border=5)
    sizer.Add(ok,                   pos=(len(st)//2+2, 0),             flag=flag, border=border)
    sizer.Add(cancel,               pos=(len(st)//2+2, 1),             flag=flag, border=border)
    sizer.Add(reset,                pos=(len(st)//2+2, 3),             flag=flag, border=border)

    self.SetSizerAndFit(sizer)
    self.Center()

  # ###########################################################
  # Setzt alle Farben auf Grundstellung zurueck.
  def reset_selected(self, event):
    for i in range(len(self.col)):
      self.cpc[i].SetColour(self.col[i][2])

  # ###########################################################
  # Liefert die eingestellten Farben als Dictionary zurueck und
  # speichert sie zusaetzlich noch im CONFIG_FILE.
  def GetValues(self, CONFIG_FILE):
    col_dict={}
    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    for i in range(len(self.cpc)):
      cs=self.cpc[i].GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
      col_dict.update({self.col[i][1] : cs})
      fc.Write(self.col[i][1], cs)
    fc.Flush()
    return(col_dict)





# ###########################################################
# Ein Dialog-Fensterchen zur Anzeige der Tastenbelegung.
class ShowKeyDialog(wx.Dialog):
  def __init__(self, parent, id=wx.ID_ANY, title="The keys"):
    wx.Dialog.__init__(self, parent, id, title)

    data=[  [ "",             ""                      ],
            [ "cursor-keys",  "move the player"       ],
            [ "ESC-key",      "restart game"          ],
            [ "SPACE",        "go to next game"       ],
            [ "BACKSPACE",    "go to previous game"   ],
            [ "u",            "undo last move"        ],
            [ "s (solution)", "next move in solution" ],
            [ "F5",           "repaint game"          ],
            [ "",             ""                      ] ]

    stkl=[]
    stdl=[]
    for stk, std in data:
      stkl.append(wx.StaticText(self, label=stk))
      stdl.append(wx.StaticText(self, label=std))

    ok=wx.Button(self, wx.ID_OK, "&OK")
    ok.SetDefault()

    gbsizer=wx.GridBagSizer(10, 10)
    for i in range(len(stkl)):
      gbsizer.Add(stkl[i], (i, 0), flag=wx.ALIGN_RIGHT|wx.LEFT,             border=15)
      gbsizer.Add(stdl[i], (i, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,  border=15)
    gbsizer.Add(ok, (len(stkl), 2), flag=wx.ALL, border=1)

    self.SetSizerAndFit(gbsizer)





# ###########################################################
# Ein Dialog 
class EditCollection(wx.Dialog):
  def __init__(self, parent, filename="", title="", description="", email="", url="", copyright=""):
    wx.Dialog.__init__(self, None, wx.ID_ANY, "Level Collection "+filename)
    self.parent=parent

    txt1=wx.StaticText(self, label="&Title:")
    self.tit=wx.TextCtrl(self, wx.ID_ANY, size=(400, -1))
    txt2=wx.StaticText(self, label="&Description:")
    self.des=wx.TextCtrl(self, wx.ID_ANY, size=(400, 100), style=wx.TE_MULTILINE)
    txt3=wx.StaticText(self, label="e&Mail:")
    self.ema=wx.TextCtrl(self, wx.ID_ANY, size=(400, -1))
    txt4=wx.StaticText(self, label="&URL:")
    self.url=wx.TextCtrl(self, wx.ID_ANY, size=(400, -1))
    txt5=wx.StaticText(self, label="&Copyright:")
    self.cpr=wx.TextCtrl(self, wx.ID_ANY, size=(400, -1))

    ok_but=     wx.Button(self, wx.ID_OK,     "&Ok")
    cancel_but= wx.Button(self, wx.ID_CANCEL, "&Cancel")

    topsizer=wx.BoxSizer(wx.VERTICAL)
    gbsizer=wx.GridBagSizer(2, 2)
    flag=wx.ALL
    b=5
    gbsizer.Add(txt1,     (0, 0), flag=flag, border=b)
    gbsizer.Add(self.tit, (0, 1), flag=flag, border=b)
    gbsizer.Add(txt2,     (1, 0), flag=flag, border=b)
    gbsizer.Add(self.des, (1, 1), flag=flag, border=b)
    gbsizer.Add(txt3,     (2, 0), flag=flag, border=b)
    gbsizer.Add(self.ema, (2, 1), flag=flag, border=b)
    gbsizer.Add(txt4,     (3, 0), flag=flag, border=b)
    gbsizer.Add(self.url, (3, 1), flag=flag, border=b)
    gbsizer.Add(txt5,     (4, 0), flag=flag, border=b)
    gbsizer.Add(self.cpr, (4, 1), flag=flag, border=b)

    butsizer=wx.BoxSizer(wx.HORIZONTAL)
    flag=wx.ALL|wx.ALIGN_RIGHT
    butsizer.Add(ok_but,     flag=flag, border=b)
    butsizer.Add(cancel_but, flag=flag, border=b)

    topsizer.Add(gbsizer)
    topsizer.Add(butsizer, flag=flag)

    self.tit.ChangeValue(title)
    self.des.ChangeValue(description)
    self.ema.ChangeValue(email)
    self.url.ChangeValue(url)
    self.cpr.ChangeValue(copyright)

    self.SetSizerAndFit(topsizer)
    self.tit.SetFocus()


  # ###########################################################
  # Liefert den Inhalt der Textfelder.
  def GetValues(self):
    return((self.tit.GetValue(), self.des.GetValue(), self.ema.GetValue(), \
            self.url.GetValue(), self.cpr.GetValue()))





# ###########################################################
# Ein Dialog analog zu wx.SingleChoiceDialog(), jedoch mit
# einem sortierbaren ListCtrl statt einer ListBox.
class MeinSingleChoiceDialog(wx.Dialog):
  def __init__(self, parent, dict2show, size=wx.DefaultSize):
    wx.Dialog.__init__(self, None, wx.ID_ANY, "select a game", 
                       style=wx.CAPTION|wx.RESIZE_BORDER|wx.CLOSE_BOX, size=size)
    self.parent=parent
    self.selected_idx=-1
    GameSelector(self, dict2show)

  # ###########################################################
  # Liefert den Index des gewählten Eintrages zurück.
  def GetSelection(self):
    return(self.selected_idx)




# ###########################################################
# listmix.ColumnSorterMixin will das so....
class MeinListCtrl(wx.ListCtrl):
  def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
    wx.ListCtrl.__init__(self, parent, ID, pos, size, style)



# ###########################################################
# der Spiele-Auswahl-Dialog
class GameSelector(wx.Panel, listmix.ColumnSorterMixin):
  def __init__(self, parent, dict2show):
    wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

    self.parent=parent
    self.list_ctrl=MeinListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)

    self.list_ctrl.InsertColumn(0, 'Index',     wx.LIST_FORMAT_RIGHT, width=50)
    self.list_ctrl.InsertColumn(1, 'Name',                            width=100)
    self.list_ctrl.InsertColumn(2, 'Width',     wx.LIST_FORMAT_RIGHT, width=50)
    self.list_ctrl.InsertColumn(3, 'Height',                          width=50)
    self.list_ctrl.InsertColumn(4, 'Solved by',                       width=100)
    self.list_ctrl.InsertColumn(5, 'Moves',     wx.LIST_FORMAT_RIGHT, width=50)
    self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
    self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.game_selected)

    listmix.ColumnSorterMixin.__init__(self, 6)
    self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list_ctrl)

    topsizer=wx.BoxSizer(wx.VERTICAL)
    topsizer.Add(self.list_ctrl, 1, wx.ALL|wx.EXPAND, 5)

    items=dict2show.items()
    index=0
    for key, data in items:
      self.list_ctrl.InsertStringItem(index, str(data[0]))
      self.list_ctrl.SetStringItem(index, 1, data[1])
      self.list_ctrl.SetStringItem(index, 2, str(data[2]))
      self.list_ctrl.SetStringItem(index, 3, str(data[3]))
      self.list_ctrl.SetStringItem(index, 4, data[4])
      self.list_ctrl.SetStringItem(index, 5, str(data[5]))
      self.list_ctrl.SetItemData(index, key)
      index+=1
    self.itemDataMap=dict2show

    self.SetSizer(topsizer)
    self.list_ctrl.SetFocus()
    self.list_ctrl.Select(0, 1)


  # ###########################################################
  # Setzt im umgebenden Dialog die Variable "self.selected_idx"
  # und meldet "Fertig".
  def game_selected(self, event):
    self.parent.selected_idx=int(self.list_ctrl.GetItem(event.GetIndex(), 0).GetText())-1
    self.parent.EndModal(wx.ID_OK)


  # ###########################################################
  # Schliesst das Such-Treffer-Fenster bzw. dessen Rahmen bei ESC
  def OnKeyDown(self, event):
    key=event.GetKeyCode()
    if key==wx.WXK_ESCAPE:
      self.parent.Close()
    else:
      event.Skip()


  # ###########################################################
  # will listmix.ColumnSorterMixin haben
  def GetListCtrl(self):
    return self.list_ctrl
  def OnColClick(self, event):
    event.Skip()

