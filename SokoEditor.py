#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os, sys

import SokoReadFile
import SokoPrepare
import SokoGraphics
import SokoMove
import SokoDialogs
import Helper as hlp


# ###########################################################
#
class SokoEditor(wx.Frame):
  def __init__(self, parent, BASE_PATH, CONFIG_FILE, \
                playground, pg_size, colDict, pos=wx.DefaultPosition, size=wx.DefaultSize):
    wx.Frame.__init__(self, parent, pos=pos, size=size, title="Editor")

    self.parent=parent
    self.BASE_PATH=BASE_PATH
    self.CONFIG_FILE=CONFIG_FILE
    self.col_dict=colDict

    self.playground=[]
    for y in playground:  # Spielfeld rechteckig machen
      ln=[]
      for x in y:
        ln.append(x)
      for x in range(len(y), pg_size[0]):
        ln.append(" ")
      self.playground.append(ln)

    self.pg_size=pg_size
    self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
    self.selectedObj="#"

    self.lineOps=[ "place objects", "- copy row", "| copy column", "- delete row", "| delete column"]

    self.Bind(wx.EVT_CLOSE, self.onClose)
    self.Bind(wx.EVT_PAINT, self.onPaint)
    self.Bind(wx.EVT_SIZE, self.onSize)
    self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
    self.Bind(wx.EVT_CHILD_FOCUS, self.onSetFocusChild)
#    self.Bind(wx.EVT_CHAR, self.onChar)

    self.SetupMenue()

    self.file=SokoReadFile.SokoReadFile()
    self.selectableObjDsp=SokoGraphics.Display(self.col_dict)
    self.selectedObjDsp=SokoGraphics.Display(self.col_dict)
    self.pgDsp=SokoGraphics.Display(self.col_dict)

    self.prep=SokoPrepare.SokoPrepare()
    self.sm=SokoMove.SokoMove()

    self.clearDC=True
    self.InitUI()
    self.Show()

  # ###########################################################
  # Legt das Menue an.
  def SetupMenue(self):
    self.menubar=wx.MenuBar()
    self.mfile=wx.Menu()
    self.mfile.Append(101, '&New',  'create a new collection')
    self.mfile.Append(102, '&Open', 'open an existing collection')

    self.mlevel=wx.Menu()
    self.mlevel.Append(201, '&New',    'create a new level')
    self.mlevel.Append(202, '&Open',   'open an existing level')
    self.mlevel.Append(203, '&Delete', 'delete a level')

    self.menubar.Append(self.mfile,  '&File')
    self.menubar.Append(self.mlevel, '&Level')


    self.Bind(wx.EVT_MENU, self.Menu_new_coll,       id=101)
    self.Bind(wx.EVT_MENU, self.Menu_open_coll,      id=102)

    self.SetMenuBar(self.menubar)

    self.CreateStatusBar(1)


  # ###########################################################
  # Menü: File/New
  def Menu_new_coll(self, event):
    dlg=wx.FileDialog(self, message="new collection", defaultDir=self.BASE_PATH, defaultFile="", \
                      wildcard="slc|*.slc", style=wx.FD_SAVE)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      self.afterDialogClose()
      return
    fn=dlg.GetPath()
    if os.path.splitext(fn)[1].lower()!=".slc":
      fn+=".slc"
    dlg.Destroy()
    self.afterDialogClose()

    dlg=SokoDialogs.EditCollection(self, fn)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      self.afterDialogClose()
      return
    print ">>>", dlg.GetValues()
    dlg.Destroy()
    self.afterDialogClose()

  # ###########################################################
  # Menü: File/Open
  def Menu_open_coll(self, event):
    dlg=wx.FileDialog(self, message="open collection", defaultDir=self.BASE_PATH, defaultFile="", \
                      wildcard="slc|*.slc", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      self.afterDialogClose()
      return
    fn=dlg.GetPath()
    dlg.Destroy()
    self.afterDialogClose()

    self.file.openFile(fn)
    gn=self.file.listGameNames()
    if len(gn)<1:
      return
    elif len(gn)==1:
      game_number=1
    elif len(gn)>1:
      dlg=wx.SingleChoiceDialog(self, "select a game", "selection", gn)
      if dlg.ShowModal()!=wx.ID_OK:
        dlg.Destroy()
        self.afterDialogClose()
        return
      game_number=dlg.GetSelection()
      dlg.Destroy()
      self.afterDialogClose()


  # ###########################################################
  # Nach einem dlg.Destroy() aufzurufen.
  def afterDialogClose(self):
    wx.Yield()
    self.clearDC=True
    self.paint()
  

  # ###########################################################
  # Bei close die aktuelle Fenster-Position ans Hauptprogramm
  # liefern.
  def onClose(self, event):
    sp=self.GetScreenPosition()
    ss=self.GetSizeTuple()
    self.parent.edicom.SetValue("close,"+str(sp[0])+","+str(sp[1])+","+str(ss[0])+","+str(ss[1]))
    self.Destroy()


  # ###########################################################
  # Refresh angefordert.
  def onPaint(self, event):
    self.clearDC=True
    self.paint()


  # ###########################################################
  # Fenster-Grössen-Änderung verarbeiten.
  def onSize(self, event):
    self.clearDC=True
    event.Skip()


  # ###########################################################
  # Fokus-Wiederherstellung verarbeiten.
  def onSetFocus(self, event):
    self.clearDC=True
    event.Skip()
    self.Refresh(False) # paint() anfordern
  def onSetFocusChild(self, event):
    self.clearDC=True
    event.Skip()
    self.Refresh(False) # paint() anfordern


  # ###########################################################
  # Verarbeitet Tastatureingaben.
  def onChar(self, event):
    self.processKeys(event.GetKeyCode(), event.ControlDown())


  # ###########################################################
  # Setzt Tastencodes in Funktionsaufrufe um.
  # Wird ctrl mit True übergeben, war CTRL gedrückt.
  def processKeys(self, key, ctrl):
    move=-1
    if   key==wx.WXK_LEFT:  # links
      move=0
    elif key==wx.WXK_RIGHT: # rechts
      move=1
    elif key==wx.WXK_UP:    # hoch
      move=2
    elif key==wx.WXK_DOWN:  # runter
      move=3
    elif key==wx.WXK_F5:    # refresh
      self.clearDC=True

    if move>-1:
      pg_stat, pg_dynp, playerpos=self.convertPlayground(self.playground, self.pg_size)
      pg_dynp_backup=hlp.copyList(pg_dynp)
      rc, playerpos=self.sm.inverseMovePlayer(pg_stat, pg_dynp, playerpos, move)
      if ctrl==False:
        pg_dynp=hlp.copyList(pg_dynp_backup)
      self.playground=self.reconvertPlayground(pg_stat, self.pg_size, pg_dynp, playerpos)

    self.paint()


  # ###########################################################
  # Wandelt ein statisches Spielfeld in ein dynamisches.
  def convertPlayground(self, pg, size):
    pg_stat=[]
    pg_dynp=[]
    playerpos=()

    for y in range(size[1]):
      ln=[]
      for x in range(size[0]):
        if pg[y][x] in ("#", " ", "."):   # Mauer, Boden, Zielfeld
          ln.append(pg[y][x])
        if pg[y][x] in ("*", "+"):        # Box/Spielfigur auf Zielfeld
          ln.append(".")
        if pg[y][x] in ("@", "$"):        # Spielfigur oder Box
          ln.append(" ")
        if pg[y][x] in ("@", "+"):        # Spielfigur [auf Zielfeld]
          playerpos=(x, y)
        if pg[y][x] in ("$", "*"):        # Box [auf Zielfeld]
          pg_dynp.append(hlp.ppack(x, y))
      pg_stat.append(ln)
    return(pg_stat, pg_dynp, playerpos)


  # ###########################################################
  # Wandelt ein dynamisches Spielfeld in ein statisches.
  def reconvertPlayground(self, pg_stat, size, pg_dynp, playerpos):
    pg=[]
    for y in range(size[1]):
      ln=[]
      for x in range(size[0]):
        c=pg_stat[y][x]
        if hlp.ppack(x, y) in pg_dynp:
          if   c==" ":  c="$"
          elif c==".":  c="*"
        elif (x, y)==playerpos:
          if   c==" ":  c="@"
          elif c==".":  c="+"
        ln.append(c)
      pg.append(ln)
    return(pg)


  # ###########################################################
  # Baut den Fensterinhalt auf.
  def paint(self):
    self.selectableObjDC=wx.AutoBufferedPaintDC(self.selectableObj_panel)
    self.selectableObjDsp.editorShowSelectableObjects(self.selectableObjDC, self.clearDC)

    self.selectedObjDC=wx.AutoBufferedPaintDC(self.selectedObj_panel)
    self.selectedObjDsp.editorShowSelectedObject(self.selectedObjDC, self.clearDC, self.selectedObj)

    self.pgDC=wx.AutoBufferedPaintDC(self.pg_panel)
    self.pgDsp.editorShowPlayground(self.pgDC, self.clearDC, self.playground, self.pg_size)
    self.clearDC=False


  # ###########################################################
  # Verarbeitet Mausklicks im Objekt-Auswahl-Bereich.
  def onLeftUp_selectableObj(self, event):
    mp=self.ScreenToClient(wx.GetMousePosition())
    op=self.selectableObjDsp.mousePosToPlaygroundPos(mp)
    # " ", ".", "$", "#", "@", "*", "+"
    if   op[0]==0:  self.selectedObj=" "
    elif op[0]==1:  self.selectedObj="."
    elif op[0]==2:  self.selectedObj="$"
    elif op[0]==3:  self.selectedObj="#"
    elif op[0]==4:  self.selectedObj="@"
    elif op[0]==5:  self.selectedObj="*"
    elif op[0]==6:  self.selectedObj="+"
    self.lineOperations.SetValue(self.lineOps[0])
    self.paint()


  # ###########################################################
  # Verarbeitet Mausklicks im Spielfeld.
  def onLeftUp_pg(self, event):
    x, y=self.ScreenToClient(wx.GetMousePosition())
    xo, yo=self.pg_panel.GetPositionTuple()
    y-=yo
    op=self.pgDsp.mousePosToPlaygroundPos((x, y))

    nv=self.lineOperations.GetValue()
    if nv==self.lineOps[0]:
      if 0<=op[0]<self.pg_size[0]:
        if 0<=op[1]<self.pg_size[1]:
          self.playground[op[1]][op[0]]=self.selectedObj
    else:
      if   nv==self.lineOps[1]: # copy row
        nr=self.playground[op[1]][:]
        self.playground.insert(op[1], nr)
        self.pg_size=(self.pg_size[0], self.pg_size[1]+1)
      elif nv==self.lineOps[2]: # copy column
        for y in range(self.pg_size[1]):  # für jede Zeile...
          c=self.playground[y][op[0]]     # diese Objekt kopieren
          self.playground[y].insert(op[0], c)
        self.pg_size=(self.pg_size[0]+1, self.pg_size[1])
      elif nv==self.lineOps[3]: # delete row
        self.playground.pop(op[1])
        self.pg_size=(self.pg_size[0], self.pg_size[1]-1)
      elif nv==self.lineOps[4]: # delete column
        for y in range(self.pg_size[1]):  # für jede Zeile...
          self.playground[y].pop(op[0])
        self.pg_size=(self.pg_size[0]-1, self.pg_size[1])
      self.clearDC=True
    self.paint()


  # ###########################################################
  # Sendet das Spielfeld ans Hauptprogramm.
  def sendBackButton_pressed(self, event):
    strg=""
    for y in range(self.pg_size[1]):
      for x in range(self.pg_size[0]):
        strg+=self.playground[y][x]
      strg+="\n"
    self.parent.edicom.SetValue("load,"+strg)


  # ###########################################################
  # Der eigentliche Fensterinhalt
  def InitUI(self):
    ss=self.GetSizeTuple()
    vsizer=wx.BoxSizer(wx.VERTICAL)
    h1sizer=wx.BoxSizer(wx.HORIZONTAL)

    # das Feld mit den auswählbaren Objekten
    self.selectableObj_panel=wx.Panel(self, size=(7*60, 60))
    self.selectableObj_panel.Bind(wx.EVT_LEFT_UP, self.onLeftUp_selectableObj)
    h1sizer.Add(self.selectableObj_panel, 0, wx.ALL|wx.EXPAND)

    h1sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), flag=wx.ALL|wx.GROW, border=5)

    # das Feld mit dem aktuell ausgewählten Objekt
    self.selectedObj_panel=wx.Panel(self, size=(60, 60))
    h1sizer.Add(self.selectedObj_panel, 0, wx.ALL|wx.EXPAND)

    h1sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), flag=wx.ALL|wx.GROW, border=5)

    # der Rest
    self.rest_panel=wx.Panel(self)
    h2sizer=wx.BoxSizer(wx.VERTICAL)
    self.lineOperations=wx.ComboBox(self.rest_panel, value=self.lineOps[0], size=(150, -1), \
                                    choices=self.lineOps, style=wx.CB_READONLY)

    self.sendBackButton=wx.Button(self.rest_panel, label="Send")
    self.sendBackButton.Bind(wx.EVT_BUTTON, self.sendBackButton_pressed)
    h2sizer.Add(self.lineOperations, 0, wx.ALL, border=3)
    h2sizer.Add(self.sendBackButton, 0, wx.ALL, border=3)

    self.rest_panel.SetSizer(h2sizer)
    h1sizer.Add(self.rest_panel, 1, wx.ALL|wx.EXPAND)

    vsizer.Add(h1sizer, 0, flag=wx.ALL|wx.GROW)
    vsizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), flag=wx.ALL|wx.GROW, border=5)

    # das Speilfeld
    self.pg_panel=wx.Panel(self)
    self.pg_panel.Bind(wx.EVT_LEFT_UP, self.onLeftUp_pg)
    self.pg_panel.Bind(wx.EVT_CHAR, self.onChar)
    vsizer.Add(self.pg_panel, 1, wx.ALL|wx.EXPAND)
    self.SetSizer(vsizer)


