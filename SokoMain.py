#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os, sys
import sqlite3
import time

import SokoReadFile   # Klasse= SokoReadFile()
import SokoPrepare    # Klasse= SokoPrepare()
import SokoGraphics   # Klasse= Display()
import SokoMove       # Klasse= SokoMove()
import SokoDB         # Klasse= Database()
import SokoDialogs    # Klasse= SetupColorDialog() und ShowKeyDialog()
import SokoAutoSolveV1
import SokoNavigate   # Klasse= NavigationArea() und NavigationPanel()
import SokoEditor     # Klasse= SokoEditor
import HostSelect     # Klasse= HostSelect
import Helper as hlp






# ###########################################################
#
class SokobanPanel(wx.Window):
  def __init__(self, parent):
    wx.Window.__init__(self, parent)
    self.parent=parent

    self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
    self.Bind(wx.EVT_PAINT, self.onPaint)
    self.Bind(wx.EVT_SIZE, self.onSize)
    self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
    self.Bind(wx.EVT_CHAR, self.onChar)

    self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
    self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
    self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
    self.parent.Bind(wx.EVT_CLOSE, self.onClose)

    self.file=SokoReadFile.SokoReadFile()
    self.sm=SokoMove.SokoMove()
    self.prep=SokoPrepare.SokoPrepare()
    self.db=SokoDB.Database(DB_NAME)

    self.clearDC=True
    self.displayDirty=False
    self.finalMessageDisplayed=False

    self.filename=""
    self.file_title=""
    self.game_number=0
    self.game_title=""
    self.warning=False
    self.game_md5=""
    self.playground_raw=[]
    self.solution=""
    self.solvedBy=""
    self.keyseq=""        # die aktuelle Bewegungsfolge ("LRUDlrud")
    self.gotFocus=False   # deaktiviert die Spielerbewegung
    self.snapshot=""
    self.showSolutionMode=False
    self.showSolutionIdx=0

    self.pg_stat=[]       # das statische Spielfeld ("#", " ", "." "i", "u", "_")
    self.pg_schk=[]       # das gekürzte statische Spielfeld ("#", " ")
    self.pg_dof=[]        # die Freiheitsgrade der überquerbaren Felder
    self.size=(0, 0)      # Tupel mit Breite, Höhe des Spielfeldes
    self.pg_dynp=[]       # das dynamische Spielfeld als Liste aus gepackten Box-Koordinaten
    self.pg_zfl=[]        # eine Liste der ungepackten Zielfeld-Koordinaten (x, y)
    self.playerpos=(0, 0) # die ungepackte Koordinate der Spielfigur (x, y)

    self.isDeadList=[]

    self.autosolveActive=False
    self.moves_s=0
    self.solvedBy=""

    self.useMouseToo=True
    self.markDeadBoxes=True
    self.showMovesSpeed=20

    # hier wird ein unsichtbares TextCtrl() zur Kommunikation mit dem Navigations-Fenster angelegt
    # und eine Event-Funktion beim Event "change" definiert
    pan=wx.Panel(self, size=(0, 0))
    self.navcom=wx.TextCtrl(pan, -1, pos=(0,0), size=(0,0), style=wx.DEFAULT)
    self.Bind(wx.EVT_TEXT, self.__msgFromNavigation, self.navcom)
    self.navigationWin=None

    self.edicom=wx.TextCtrl(pan, -1, pos=(0,0), size=(0,0), style=wx.DEFAULT)
    self.Bind(wx.EVT_TEXT, self.__msgFromEditor, self.edicom)
    self.editorWin=None

    self.col=[  ["Background",                "col_bg",         "#CCCCCC"],
                ["Text",                      "col_txt",        "#000000"],
                ["Box body",                  "col_boxbdy",     "#00FF90"],
                ["Box border",                "col_boxbdr",     "#000000"],
                ["Floor",                     "col_flrbdy",     "#CCCCCC"],
                ["Floor border",              "col_flrbdr",     "#00CCCC"],
                ["Floor (bad)",               "col_flrbad",     "#FFAAAA"],
                ["Floor (unreachable)",       "col_flrunr",     "#CCCCCC"],
                ["Wall",                      "col_wall",       "#777777"],
                ["Wall border",               "col_wallbdr",    "#777777"],
                ["Player body",               "col_plrbdy",     "#AAAAAA"],
                ["Player border",             "col_plrbdr",     "#000000"],
                ["Player reflection",         "col_plrref",     "#DDDDDD"],
                ["Player reflection border",  "col_plrrefbdr",  "#FFFFFF"],
                ["Goal square top/left",      "col_gs1",        "#000000"],
                ["Goal square bottom/right",  "col_gs2",        "#FFFFFF"],
                ["Marks",                     "col_mrks",       "#000000"]  ]

    self.td={"l":0, "r":1, "u":2, "d":3, "L":0, "R":1, "U":2, "D":3}

    self.col_dict={}
    for i in range(len(self.col)):
      self.col_dict.update({self.col[i][1] : self.col[i][2]})

    self.SetupMenue()
    self.loadConfig()
    self.dsp=SokoGraphics.Display(self.col_dict)

    if self.filename!="":
      self.file.openFile(self.filename)
      self.load(self.game_number)

    wx.FutureCall(200, self.setFocus)


  # ###########################################################
  # Legt die Toolbar an.
  def SetupToolbar(self):
    vsizer=wx.BoxSizer(wx.VERTICAL)
    toolbar=wx.ToolBar(self.parent, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
    toolbar.AddSimpleTool(1, wx.Image('/usr/share/icons/gnome/24x24/actions/gtk-refresh.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Repaint', '')
    toolbar.AddSeparator()
    toolbar.Realize()
    vsizer.Add(toolbar, 0)

    self.pg_panel=wx.Panel(self.parent)
    vsizer.Add(self.pg_panel, 1, wx.EXPAND)
    self.parent.SetSizer(vsizer)

  # ###########################################################
  # Legt das Menue an.
  def SetupMenue(self):
    self.menubar=wx.MenuBar()
    self.mfile=wx.Menu()
    self.mfile.Append(101, '&Open', 'open a file')
    self.mfile.Append(102, '&Single game from clipboard', 'load a single game from the clipboard')
    self.mfile.AppendSeparator()
    self.mfile.Append(105, '&Merge solutions', 'open another database and load all new or better solutions')
    self.mfile.AppendSeparator()
    self.mfile.Append(107, '&Editor', 'open the level edior')
    self.mfile.AppendSeparator()
    self.mfile.Append(109, '&Quit', 'exit program')

    self.mgame=wx.Menu()
    self.mgame.Append(202, '&Show solution', 'step through the solution (key is "s")')
    self.mgame.Append(204, '&Enter solution', 'enter a solution')
    self.mgame.Append(206, 'Solution to &clipboard', 'copies the solution-string into the clipboard')
    self.mgame.AppendSeparator()
    self.mgame.Append(210, '&Take snapshot', 'remember the current position')
    self.mgame.Append(215, '&Revert to snapshot', 'restore to a previously remembered position')
    self.mgame.AppendSeparator()
    self.mgame.Append(230, '&Next game', 'Load the next game from file')
    self.mgame.Append(235, '&Previous game', 'Load the previous game from file')
    self.mgame.AppendSeparator()
    self.mgame.Append(240, '&Use mouse too', 'use the mouse to move the player', True)
    self.mgame.Append(245, '&Mark dead boxes/floors', 'mark boxes, if they are no longer movable', True)

    self.msetup=wx.Menu()
    self.msetup.Append(302, '&Adjust speed', 'Changes the speed for player movements')
    self.msetup.Append(305, '&Setup colors', 'Change the colors of playground objects')
    self.msetup.AppendSeparator()
    self.msetup.Append(310, '&Open navigation area', 'opens a new window with navigation controls')

    self.mhelp=wx.Menu()
    self.mhelp.Append(402, '&Keys-Help', 'the keys and their function')
    self.mhelp.AppendSeparator()
    self.mhelp.Append(405, 'Auto-&Solve v1', 'solve the game (brute-force -> optimal moves)')
    self.mhelp.Append(406, 'Auto-Solve &v2', 'solve the game')
    self.mhelp.AppendSeparator()
    self.mhelp.Append(409, '&About', 'version info')

    self.menubar.Append(self.mfile,   '&File')
    self.menubar.Append(self.mgame,   '&Game')
    self.menubar.Append(self.msetup,  '&Setup')
    self.menubar.Append(self.mhelp,   '&Help')

    self.parent.SetMenuBar(self.menubar)

    self.parent.CreateStatusBar(3)
    self.parent.SetStatusWidths([-1, 150, 100])
    self.mgame.Enable(202, False)
    self.mgame.Enable(206, False)
    self.mhelp.Enable(406, False)

    self.parent.Bind(wx.EVT_MENU, self.MenuOpen,  id=101)
    self.parent.Bind(wx.EVT_MENU, self.MenuLfCb,  id=102)
    self.parent.Bind(wx.EVT_MENU, self.MenuMerge, id=105)
    self.parent.Bind(wx.EVT_MENU, self.MenuEditor,id=107)
    self.parent.Bind(wx.EVT_MENU, self.MenuQuit,  id=109)

    self.parent.Bind(wx.EVT_MENU, self.MenuShow,  id=202)
    self.parent.Bind(wx.EVT_MENU, self.MenuEnter, id=204)
    self.parent.Bind(wx.EVT_MENU, self.Menu2Clip, id=206)
    self.parent.Bind(wx.EVT_MENU, self.MenuTkSS,  id=210)
    self.parent.Bind(wx.EVT_MENU, self.MenuRtSS,  id=215)
    self.parent.Bind(wx.EVT_MENU, self.MenuNG,    id=230)
    self.parent.Bind(wx.EVT_MENU, self.MenuPG,    id=235)
    self.parent.Bind(wx.EVT_MENU, self.MenuMouse, id=240)
    self.parent.Bind(wx.EVT_MENU, self.MenuMarkB, id=245)

    self.parent.Bind(wx.EVT_MENU, self.MenuAdjSp, id=302)
    self.parent.Bind(wx.EVT_MENU, self.MenuSCol,  id=305)
    self.parent.Bind(wx.EVT_MENU, self.MenuNavW,  id=310)

    self.parent.Bind(wx.EVT_MENU, self.MenuKeys,  id=402)
    self.parent.Bind(wx.EVT_MENU, self.MenuAS,    id=405)
    self.parent.Bind(wx.EVT_MENU, self.MenuASv2,  id=406)
    self.parent.Bind(wx.EVT_MENU, self.MenuAbout, id=409)


  # ###########################################################
  # Deaktiviert das Menue (ausser Quit).
  def disableMenu(self):
    self.mfile.Enable(101, False)
    self.mfile.Enable(102, False)
    self.mfile.Enable(105, False)
    self.mfile.Enable(107, False)
    self.menubar.EnableTop(1, False)
    self.menubar.EnableTop(2, False)
    self.menubar.EnableTop(3, False)


  # ###########################################################
  # Aktiviert das Menue.
  def enableMenu(self):
    self.mfile.Enable(101, True)
    self.mfile.Enable(102, True)
    self.mfile.Enable(105, True)
    self.mfile.Enable(107, True)
    self.menubar.EnableTop(1, True)
    self.menubar.EnableTop(2, True)
    self.menubar.EnableTop(3, True)


  # ###########################################################
  # Menue: Open
  def MenuOpen(self, event):
    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    fi=fc.ReadInt("filteridx", 0)
    dlg=wx.FileDialog(self, message="open file", defaultDir=BASE_PATH, defaultFile="", \
                      wildcard="skm|*.skm|slc|*.slc|txt|*.txt|all|*", \
                      style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
    dlg.SetFilterIndex(fi)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return

    fn=dlg.GetPath()
    fi=dlg.GetFilterIndex()
    dlg.Destroy()
    fc.WriteInt("filteridx", fi)
    fc.Flush()

    self.file.openFile(fn)
    self.fileLoad(fn)


  # ###########################################################
  # Lädt die Datei oder den String aus dem Clipboard ins Spiel.
  def fileLoad(self, fn):
    wx.BeginBusyCursor()
    wx.Yield()

    gl=self.file.listGameNames()

    gl2=[]
    gl3={}
    for i in range(len(gl)):
      pg=self.file.loadGame(i)
      if pg==[]:
        gl2.append(str(i+1)+" <<< illegal playground >>>")
        gl3.update({ i+1 : ( i+1, "<<< illegal playground >>>", 0, 0, "", 0)})
        continue
      pg2=self.prep.getLines(pg)
      sz=self.prep.getSize(pg2)
      md5=self.prep.getMD5(pg2)
      sl, sb=self.db.getSolutionLength(md5)
      if sl!="":
        gl2.append(str(i+1)+" ("+str(sl)+", "+sb+")  "+gl[i])
        gl3.update({ i+1 : ( i+1, gl[i], sz[0], sz[1], sb, sl )})
      else:
        gl2.append(str(i+1)+" ( - ? - )  "+gl[i])
        gl3.update({ i+1 : ( i+1, gl[i], sz[0], sz[1], "?", 0 )})

    wx.EndBusyCursor()
    wx.Yield()

    if len(gl2)>1:
#      dlg=wx.SingleChoiceDialog(self, "select a game", "selection", gl2)
      sz=self.GetSizeTuple()
      dlg=SokoDialogs.MeinSingleChoiceDialog(self, gl3, size=(450, sz[1]))
      if dlg.ShowModal()!=wx.ID_OK:
        dlg.Destroy()
        return

      self.game_number=dlg.GetSelection()
      dlg.Destroy()

      self.filename=fn                        # Dateiname mit Pfad
      self.gamesList=gl
      self.gamename=self.gamesList[self.game_number]

      fc=wx.FileConfig(localFilename=CONFIG_FILE)
      fc.Write("filename", self.filename)
      fc.WriteInt("gameidx", self.game_number)
      fc.Flush()
    else:
      self.game_number=0
      self.filename=fn
      self.gamesList=gl
      if self.gamesList!=[]:
        self.gamename=self.gamesList[self.game_number]
    self.load(self.game_number)


  # ###########################################################
  # Menue: From clipboard
  def MenuLfCb(self, event):
    if wx.TheClipboard.Open():
      if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT))==True:
        do=wx.TextDataObject()
        wx.TheClipboard.GetData(do)
        wx.TheClipboard.Close()
      else:
        wx.MessageBox("Unsupported data in the clipboard!", "Error", wx.OK | wx.ICON_ERROR)
        wx.TheClipboard.Close()
        return
    else:
      wx.MessageBox("Unable to open clipboard!", "Error", wx.OK | wx.ICON_ERROR)
      return

    fn="<<<from clipboard>>>"
    self.file.openFile(fn, do.GetText())
    self.fileLoad(fn)
    

  # ###########################################################
  # Menue: Merge solutions
  def MenuMerge(self, event):
    dlg=HostSelect.HostSelect(self, CONFIG_FILE, DB_NAME, self.db)
    dlg.ShowModal()
    dlg.Destroy()
    self.clearDC=True


  # ###########################################################
  # Menue: Editor
  def MenuEditor(self, event):
    if self.editorWin!=None:          # wenn schon offen...
      self.editorWin.Iconize(False)   # ...nur in den Vordergrund holen
      return

    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    sp=(fc.ReadInt("pos_x_edit", -1), fc.ReadInt("pos_y_edit", -1))
    ss=(fc.ReadInt("size_x_edit", -1), fc.ReadInt("size_y_edit", -1))
    self.editorWin=SokoEditor.SokoEditor(self, BASE_PATH, CONFIG_FILE, \
                    self.playground_raw, self.size, self.col_dict, pos=sp, size=ss)
    self.clearDC=True


  # ###########################################################
  # Menue: Quit
  def MenuQuit(self, event):
    self.parent.Close()


  # ###########################################################
  # Menue: Show solution
  def MenuShow(self, event):
    self.resetGame()
    self.keyseq=""
    self.isDeadList=[]
    self.showSolutionMode=True
    self.showSolutionIdx=0
    if self.displayDirty==True:
      self.NewPaint()
    self.paint()
    self.clearDC=True # das Menü hat das Spielfeld überlagert und bedarf eines rePaints


  # ###########################################################
  # Menue: Enter solution
  def MenuEnter(self, event):
    self.resetGame()
    self.keyseq=""
    solution=wx.GetTextFromUser("Enter solution string", "Key sequence")
    self.solution=""
    for c in solution:
      if c in self.td:
        self.solution+=c
    
    if self.solution!="":
      self.isDeadList=[]
      self.showSolutionMode=True
      self.showSolutionIdx=0


  # ###########################################################
  # Menue: Solution to clipboard
  def Menu2Clip(self, event):
    if wx.TheClipboard.Open():
      do=wx.TextDataObject()
      do.SetText(self.solution)
      wx.TheClipboard.SetData(do)
      wx.TheClipboard.Close()
    else:
      wx.MessageBox("Unable to open clipboard!", "Error", wx.OK | wx.ICON_ERROR)
    self.clearDC=True


  # ###########################################################
  # Menue: Take snapshot
  def MenuTkSS(self, event):
    self.snapshot=self.keyseq
    self.clearDC=True


  # ###########################################################
  # Menue: Revert to snapshot
  def MenuRtSS(self, event):
    self.resetGame()
    self.keyseq=""
    for i in self.snapshot:
      rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[i])
      self.keyseq+=ms
      if isdead==True:
        self.isDeadList.append(bp)
        self.isDeadList.append(self.keyseq)

    self.showSolutionMode=False
    self.showSolutionIdx=0
    if self.displayDirty==True:
      self.NewPaint()
    self.paint()
    self.showMovesCounter()
    self.checkForIsSolved()
    self.clearDC=True


  # ###########################################################
  # Menue: Adjust speed
  def MenuAdjSp(self, event):
    dlg=wx.NumberEntryDialog(self, "Set the milliseconds to wait after each move", "between 1 and 100", 
              "Adjust speed", self.showMovesSpeed, 1, 100)
    if dlg.ShowModal()==wx.ID_OK:
      self.showMovesSpeed=dlg.GetValue()
      dlg.Destroy()


  # ###########################################################
  # Menue: Setup colors
  def MenuSCol(self, event):
    dlg=SokoDialogs.SetupColorDialog(self, self.col, self.col_dict)
    if dlg.ShowModal()==wx.ID_OK:
      self.col_dict=dlg.GetValues(CONFIG_FILE)
      dlg.Destroy()
      self.dsp.re_init(self.col_dict)


  # ###########################################################
  # Menue: Open navigation area
  def MenuNavW(self, event):
    if self.navigationWin!=None:          # wenn schon offen...
      self.navigationWin.Iconize(False)   # ...nur in den Vordergrund holen
      return

    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    sp=(fc.ReadInt("pos_x_nav", -1), fc.ReadInt("pos_y_nav", -1))
    self.navigationWin=SokoNavigate.NavigationArea(self, pos=sp)
    self.clearDC=True


  # ###########################################################
  # Menue: Next game
  def MenuNG(self, event):
    self.loadNext()
    self.clearDC=True


  # ###########################################################
  # Menue: Previous game
  def MenuPG(self, event):
    self.loadPrev()
    self.clearDC=True


  # ###########################################################
  # Menue: Use mouse too
  def MenuMouse(self, event):
    self.useMouseToo=self.mgame.IsChecked(240)
    self.clearDC=True


  # ###########################################################
  # Menue: Mark dead boxes
  def MenuMarkB(self, event):
    self.markDeadBoxes=self.mgame.IsChecked(245)
    self.clearDC=True
    self.paint()
    self.clearDC=True


  # ###########################################################
  # Menue: Keys
  def MenuKeys(self, event):
    dlg=SokoDialogs.ShowKeyDialog(self)
    dlg.ShowModal()
    dlg.Destroy()


  # ###########################################################
  # Menue: Auto-Solve
  def MenuAS(self, event):
    self.autoSolveBruteForceOnOneCore()


  # ###########################################################
  # Menue: Auto-Solve
  def MenuASv2(self, event):
    pass


  # ###########################################################
  # Menue: About
  def MenuAbout(self, event):
    info=wx.AboutDialogInfo()
    info.SetName("Sokoban")
    info.SetVersion("2.0")
    info.SetCopyright("D.A.  (12.2012)")
    info.SetDescription("An implementation of the Sokoban-Game")
    info.SetLicence("Dieses Programm ist freie Software gemaess GNU General Public License")
    info.AddDeveloper("Detlev Ahlgrimm")
    wx.AboutBox(info)








  # ###########################################################
  # Aktualisiert das Fenster.
  def onPaint(self, event):
    self.paint()


  # ###########################################################
  # Fenster-Grössen-Änderung verarbeiten.
  def onSize(self, event):
    self.clearDC=True
    self.Refresh(False)


  # ###########################################################
  # Fokus-Wiederherstellung verarbeiten.
  def onSetFocus(self, event):
    # vermerken, dass wahrsheinlich nur ins Fenster geklickt wurde, um es zu fokussieren...und nicht, um
    # den Player an die Klick-Position zu bewegen.
    self.gotFocus=True
    self.clearDC=True   # Spielfeld-Neuaufbau anfordern
    self.Refresh(False) # paint() anfordern
    wx.FutureCall(200, self.setFocus)


  # ###########################################################
  # Wird von __init__ und onSetFocus aufgerufen, um den
  # unberechtigten "self.gotFocus=True" abzuschalten.
  def setFocus(self):
    self.SetFocus()
    self.gotFocus=False


  # ###########################################################
  # Stellt das Spielfeld dar.
  def paint(self):
    self.dc=wx.AutoBufferedPaintDC(self)
    self.dsp.showPlayground(self.dc, self.clearDC, self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, \
                            self.size, self.isDeadList, self.markDeadBoxes, self.showSolutionMode)
    self.clearDC=False


  # ###########################################################
  # Verarbeitet Tastatureingaben.
  def onChar(self, event):
    self.processKeys(event.GetKeyCode())


  # ###########################################################
  # Vermerkt in (self.from_x, self.from_y), an welchen
  # Koordinaten die linke Maustaste gedrückt wurde. Nach 200ms
  # wird dann ggf. der Mauscursor auf ein Drag&Drop-Symbol
  # geändert.
  def onLeftDown(self, event):
    if self.useMouseToo==False or self.autosolveActive==True:
      return

    self.from_x, self.from_y=self.dsp.mousePosToPlaygroundPos(self.ScreenToClient(wx.GetMousePosition()))
    wx.CallLater(200, self.leftButtonStillDown)
    self.dragdrop=True

  # ###########################################################
  # Schließt bei Bedarf das Navigations-Fenster, bevor das
  # eigene Fenster geschlossen wird.
  def onClose(self, event):
    if self.navigationWin!=None:
      self.navigationWin.Close()
    self.parent.Destroy()

  # ###########################################################
  # Wenn 200ms nach leftDown immer noch leftDown gilt, wird
  # der Maus-Cursor geändert.
  # Eine Hand wird gezeigt, wenn der Klick auf einer Box
  # erfolgt ist (soll wohl ein Drag&Drop auf eine andere
  # Postion werden). Ansonsten wird ein Sperrsymbol gezeigt.
  def leftButtonStillDown(self):
    if self.dragdrop==True:
      if hlp.ppack(self.from_x, self.from_y) in self.pg_dynp:
        csr=wx.StockCursor(wx.CURSOR_HAND)
      else:
        csr=wx.StockCursor(wx.CURSOR_NO_ENTRY)
      self.SetCursor(csr)


  # ###########################################################
  # Setzt Maus-Klicks in Spieler-Bewegungen um.
  def onLeftUp(self, event):
    if self.useMouseToo==False or self.autosolveActive==True:
      return

    self.dragdrop=False
    csr=wx.StockCursor(wx.CURSOR_ARROW)
    self.SetCursor(csr)

    if self.displayDirty==True: # wenn eine Meldung auf dem Display steht und ein weiterer Zug gemacht
      self.NewPaint()           # wird, dann muss erstmal die Meldung gelöscht werden.

    x, y=self.dsp.mousePosToPlaygroundPos(self.ScreenToClient(wx.GetMousePosition()))

    if self.gotFocus==True:                   # wenn das Fenster gerade frisch fokussiert wurde...
      self.gotFocus=False                     # ...dann soll der Player wohl nicht zur angeklickten
      return                                  # Position bewegt werden.

    if not(1<=x<=(self.size[0]-2) and 1<=y<=(self.size[1]-2) and \
           1<=self.from_x<=(self.size[0]-2) and 1<=self.from_y<=(self.size[1]-2)):
      return
    elif self.pg_stat[y][x] in ("i", "u") or \
         self.pg_stat[self.from_y][self.from_x] in ("i", "u"):
      return

    if (self.from_x, self.from_y)!=(x, y):
      if (self.from_x, self.from_y)==self.playerpos:
        # Der Spieler soll (unnötigerweise per D&D) bewegt werden. Also Weg suchen.
        ms=self.sm.findBestWayTo(self.pg_stat, self.pg_dynp, self.playerpos, (x, y))
        if ms!="":
          rc=0
        else:
          rc=5
      else:
        # Eine Box soll bewegt werden. Also Weg suchen.
        rc, ms=self.sm.findBestPushTrackTo(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, (self.from_x, self.from_y), (x, y))
      if rc==0:
        # Weg gefunden - also Ausführen bzw. Anzeigen.
        self.showMoves(ms)
      else:
        # kein Weg gefunden.
        self.markProblem(rc, self.from_x, self.from_y, x, y)
    else:
      # Es soll nur der Spieler bewegt werden. Also Weg suchen.
      ms=self.sm.findBestWayTo(self.pg_stat, self.pg_dynp, self.playerpos, (x, y))
      if ms!="":
        # Weg gefunden.
        self.showMoves(ms)
      else:
        # kein Weg gefunden.
        if 1<=x<=(self.size[0]-2) and 1<=y<=(self.size[1]-2):
          if self.pg_stat[y][x] not in ("i", "u"):
            self.markProblem(4, self.from_x, self.from_y, x, y)

    self.checkForIsSolved()


  # ###########################################################
  # Führt eine Zug-Folge auf dem Bildschirm sichtbar aus.
  def showMoves(self, moveList):
    self.autosolveActive=True
    self.showSolutionMode=False
    for k in moveList:
      rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[k])
      self.keyseq+=k
      if isdead==True:
        self.isDeadList.append(bp)
        self.isDeadList.append(self.keyseq)
      self.showMovesCounter()
      self.paint()
      wx.Yield()
      wx.MilliSleep(self.showMovesSpeed)
    self.autosolveActive=False
    self.paint()
    self.showMovesCounter()


  # ###########################################################
  # Zeigt auf dem Bildschirm an, wenn eine Player-Bewegung, die
  # via Maus gewählt wurde, nicht möglich ist. Nach einer
  # Sekunde wird die Markierung wieder gelöscht.
  # Für mark gilt:
  #   1 = Start-Pos nicht Box
  #   2 = Ziel-Pos nicht frei
  #   4 = kein Weg zum Start
  #   5 = kein Weg von Start nach Ziel
  def markProblem(self, mark, start_x, start_y, dest_x, dest_y):
    self.dsp.showMark(mark, (start_x, start_y), (dest_x, dest_y), self.playerpos)
    wx.CallLater(1000, self.NewPaint)


  # ###########################################################
  # Paint() mit Neuaufbau.
  def NewPaint(self):
    self.clearDC=True
    self.paint()
    self.displayDirty=False

  # ###########################################################
  # Verarbeitet Mouse-Wheel-Bewegungen.
  # Mouse-Wheel(zurück)   entspricht der u-Taste
  # Mouse-Wheel(vorwärts) entspricht der s-Taste
  def onMouseWheel(self, event):
    if self.useMouseToo==False or self.autosolveActive==True:
      return

    if event.GetWheelRotation()<0:  # Wheel runter (entspricht "u")
      if self.displayDirty==True:
        self.NewPaint()
      self.undoMove()
    else:                           # Wheel rauf (entspricht "s")
      if self.showSolutionMode==True:
        if self.showSolutionIdx<len(self.solution):
          m=self.solution[self.showSolutionIdx]
          rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[m])
          self.keyseq+=ms
          self.showSolutionIdx+=1
          self.paint()
          self.showMovesCounter()


  # ###########################################################
  # Event-Routine, die auf Meldungen vom Editor-Fenster
  # reagiert.
  def __msgFromEditor(self, event):
    v=self.edicom.GetValue()
    if v[0:5]=="close":
      dummy, pos_x, pos_y, size_x, size_y=v.split(",")
      fc=wx.FileConfig(localFilename=CONFIG_FILE)
      fc.WriteInt("pos_x_edit", int(pos_x))
      fc.WriteInt("pos_y_edit", int(pos_y))
      fc.WriteInt("size_x_edit", int(size_x))
      fc.WriteInt("size_y_edit", int(size_y))
      fc.Flush()
      self.editorWin=None
      return
    elif v[0:4]=="load":
      pg=v[5:]
      print pg
      fn="<<<from clipboard>>>"
      self.file.openFile(fn, pg)
      self.fileLoad(fn)


  # ###########################################################
  # Event-Routine, die auf "keys" vom Navigations-Fenster
  # reagiert.
  def __msgFromNavigation(self, event):
    if self.displayDirty==True:
      self.NewPaint()

    v=self.navcom.GetValue()
    if v[0:5]=="close":
      dummy, pos_x, pos_y, size_x, size_y=v.split(",")
      fc=wx.FileConfig(localFilename=CONFIG_FILE)
      fc.WriteInt("pos_x_nav", int(pos_x))
      fc.WriteInt("pos_y_nav", int(pos_y))
      fc.WriteInt("size_x_nav", int(size_x))
      fc.WriteInt("size_y_nav", int(size_y))
      fc.Flush()
      self.navigationWin=None
      return

    move=-1
    if   v=="lt":
      move=0
    elif v=="rt":
      move=1
    elif v=="up":
      move=2
    elif v=="dn":
      move=3
    elif v=="ud":
      self.undoMove()
    elif v=="rf":
      self.clearDC=True
    elif v=="fw":
      if self.showSolutionMode==True:
        if self.showSolutionIdx<len(self.solution):
          m=self.solution[self.showSolutionIdx]
          rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[m])
          self.keyseq+=ms
          self.showSolutionIdx+=1
    elif v=="rg":
      self.load(self.game_number)
    elif v=="ng":
      self.loadNext()
    elif v=="pg":
      self.loadPrev()
    else:
      print "illegal msg from navi-win:", v

    if move>-1:
      self.showSolutionMode=False
      rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, move)

      self.keyseq+=ms
      if isdead==True:
        self.isDeadList.append(bp)
        self.isDeadList.append(self.keyseq)

    self.paint()
    self.showMovesCounter()
    self.checkForIsSolved()

    self.navcom.ChangeValue("")


  # ###########################################################
  # Setzt Tastencodes in Funktionsaufrufe um.
  def processKeys(self, key):
    if self.autosolveActive==True:
      if key==wx.WXK_ESCAPE:
        self.autosolveActive=False
      return

    if self.displayDirty==True:
      self.NewPaint()

    move=-1
    if   key==wx.WXK_LEFT:  # links
      move=0
    elif key==wx.WXK_RIGHT: # rechts
      move=1
    elif key==wx.WXK_UP:    # hoch
      move=2
    elif key==wx.WXK_DOWN:  # runter
      move=3
    elif key==ord("u"):     # undo
      self.undoMove()
    elif key==ord("n"):
      self.MenuNavW(0)
    elif key==ord("s"):     # solution step
      if self.showSolutionMode==True:
        if self.showSolutionIdx<len(self.solution):
          m=self.solution[self.showSolutionIdx]
          rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[m])
          self.keyseq+=ms
          self.showSolutionIdx+=1
    elif key==wx.WXK_ESCAPE:# Reload
      self.load(self.game_number)
    elif key==wx.WXK_SPACE: # next game
      self.loadNext()
    elif key==wx.WXK_BACK:  # previos game
      self.loadPrev()
    elif key==wx.WXK_F5:    # refresh
      self.clearDC=True

    if move>-1:
      self.showSolutionMode=False
      rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, move)

      self.keyseq+=ms
      if isdead==True:
        self.isDeadList.append(bp)
        self.isDeadList.append(self.keyseq)

    self.paint()
    self.showMovesCounter()
    self.checkForIsSolved()


  # ###########################################################
  # Nimmt den letzten Zug zurück, indem das Spielfeld neu
  # geladen wird und bis zur aktuellen Position minus eins
  # bewegt wird.
  def undoMove(self):
    if self.isDeadList!=[] and self.keyseq in self.isDeadList:
      self.isDeadList.pop()
      self.isDeadList.pop()

    self.resetGame()
    if len(self.keyseq)>0:
      self.keyseq=self.keyseq[0:len(self.keyseq)-1]
      for i in self.keyseq:
        rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[i], False)

      if self.showSolutionMode==True:
        # wenn im Lösung-Anzeigen-Modus...auch dort einen Zug zurück
        self.showSolutionIdx-=1

    self.paint()
    self.showMovesCounter()
    self.checkForIsSolved()


  # ###########################################################
  # Setzt das aktuelle Spiel auf Startwerte.
  def resetGame(self):
    self.pg_dynp=hlp.copyList(self.pg_dynp_backup)
    self.playerpos=self.playerpos_backup


  # ###########################################################
  # Gibt ggf. die isSolved-Meldung aus und setzt in diesem
  # Fall self.displayDirty=True
  def checkForIsSolved(self):
    if self.showSolutionMode==True:
      return

    if self.sm.isSolved(self.pg_stat, self.pg_dynp, self.pg_zfl)==True:
      if self.finalMessageDisplayed==False:
        self.dsp.showIsReady(0)
        self.displayDirty=True
        self.finalMessageDisplayed=True
        self.db.saveSolution(self.game_md5, USERNAME, self.file_title, self.game_title, self.keyseq)
        self.solutionUpdate()
    else:
      self.finalMessageDisplayed=False


  # ###########################################################
  # Lädt das aktuelle Spiel gemäß gn.
  def load(self, gn):
    self.finalMessageDisplayed=False
    g=self.file.loadGame(gn)

    if g!=[]:
      self.file_title=self.file.getFileTitle()
      self.game_number=gn
      self.game_title=self.file.getGameTitle(gn)
      self.pg_stat, self.pg_schk, self.pg_dof, self.size, self.pg_dynp, self.pg_zfl, self.playerpos, self.playground_raw=self.prep.importPlayground(g)
      self.pg_dynp_backup=hlp.copyList(self.pg_dynp)
      self.playerpos_backup=self.playerpos
      self.warning=len(self.pg_dynp)!=len(self.pg_zfl)  # ist True, wenn die Anzahl der Boxen != der Anzahl der Zielfelder ist
      self.game_md5=self.prep.getMD5(self.playground_raw)
      self.clearDC=True
      self.paint()
      self.saveConfig()

      self.keyseq=""
      self.isDeadList=[]
      self.solutionUpdate()
    else:
      wx.MessageBox('Illegal playground !\n\nUse File/Open/... to select another game.', 'Error', wx.OK | wx.ICON_ERROR)
    self.__StatusUpdate()


  # ###########################################################
  # Liefert eine Kopie der Liste "list2copy".
  def solutionUpdate(self):
    self.solution, self.solvedBy=self.db.loadSolution(self.game_md5)
    self.showSolutionMode=False
    self.showSolutionIdx=0

    if self.solution=="":
      self.mgame.Enable(202, False)
      self.mgame.Enable(206, False)
    else:
      self.mgame.Enable(202, True)
      self.mgame.Enable(206, True)
    self.showMovesCounter()    


  # ###########################################################
  # Lädt das nächste Spiel in der geöffneten Datei.
  def loadNext(self):
    self.load(self.game_number+1)


  # ###########################################################
  # Lädt das nächste Spiel in der geöffneten Datei.
  def loadPrev(self):
    self.load(self.game_number-1)


  # ###########################################################
  # Aktualisiert die Statuszeile.
  def __StatusUpdate(self):
    szt=str(self.game_number+1)+" / "+str(self.file.getGameCount())+" - "+self.game_title+" / "+self.file_title
    self.parent.SetStatusText(szt, 0)

    if self.warning==True:  szt="warning"
    else:                   szt=""
    self.parent.SetStatusText(szt, 2)


  # ###########################################################
  # Aktualisiert den Statuszeilen-Bereich mit der Anzeige der
  # bisher ausgeführten Züge und ggf. Züge der Lösung.
  def showMovesCounter(self):
    szt=str(len(self.keyseq))+" / "+str(len(self.solution))+"  "+self.solvedBy
    self.parent.SetStatusText(szt, 1)


  # ###########################################################
  # Speichert die Konfiguration (aktuelles Spiel und
  # Fenster-Grösse + Position).
  def saveConfig(self):
    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    fc.Write("filename", self.file.getFilename())
    fc.WriteInt("gameidx", self.game_number)
    sp=self.parent.GetScreenPosition()
    ss=self.parent.GetSizeTuple()
    fc.WriteInt("pos_x",            sp[0])
    fc.WriteInt("pos_y",            sp[1])
    fc.WriteInt("size_x" ,          ss[0])
    fc.WriteInt("size_y" ,          ss[1])
    fc.WriteInt("use_mouse",        self.useMouseToo)
    fc.WriteInt("mark_dead",        self.markDeadBoxes)
    fc.WriteInt("show_moves_speed", self.showMovesSpeed)
    fc.Flush()


  # ###########################################################
  # Lädt die Konfiguration.
  def loadConfig(self):
    fc=wx.FileConfig(localFilename=CONFIG_FILE)
    self.filename=fc.Read("filename", "")
    self.game_number=fc.ReadInt("gameidx", 0)

    self.useMouseToo=fc.ReadInt("use_mouse", 1)
    self.mgame.Check(240, self.useMouseToo)

    self.markDeadBoxes=fc.ReadInt("mark_dead", 1)
    self.mgame.Check(245, self.markDeadBoxes)

    self.showMovesSpeed=fc.ReadInt("show_moves_speed", 50)

    if self.filename!="":
      if os.path.exists(self.filename)!=True:
        self.filename=""
        self.game_number=0

    self.col_dict={}
    for i in range(len(self.col)):
      cs=fc.Read(self.col[i][1], self.col[i][2])
      self.col_dict.update({self.col[i][1] : cs})



  # ###########################################################
  # Sucht nach einer Lösung für das aktuelle Spiel, indem alle
  # möglichen Spieler-Bewegungen ausgeführt werden. Effektlose
  # Züge und Tot-Stellungen werden nicht weiter verfolgt.
  def autoSolveBruteForceOnOneCore(self):
    wx.FutureCall(100, self.delayed_clearDC)
    self.resetGame()
    self.autosolveActive=True
    self.disableMenu()
    ct=time.clock()

    if self.navigationWin!=None:
      self.navigationWin.Close()
      navigationWinWasOpen=True
    else:
      navigationWinWasOpen=False

    solver=SokoAutoSolveV1.SokoAutoSolveV1()
    solver.setData(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.pg_zfl)
    solver.startSolver()

    isRunning, solution, keyLen, notd, nogtt, dictLen, count, killed, playerpos, pg_dynp=solver.getStatus()
    while isRunning==True:        # solange der Thread läuft...
      self.pg_dynp=pg_dynp        # eins der gerade getesteten Spiele laden und...
      self.playerpos=playerpos
      self.paint()                # ...anzeigen
      self.__StatusUpdateAS(keyLen, notd, nogtt, count, killed, dictLen)  # Statuszeile aktualisieren
      wx.Yield()

      time.sleep(0.5)
      isRunning, solution, keyLen, notd, nogtt, dictLen, count, killed, playerpos, pg_dynp=solver.getStatus()
      if self.autosolveActive==False:   # wenn Abbruch-Wunsch (ESC-Taste)...
        solver.cancelSolver()           # ...an Thread weitergeben

    # Thread ist beendet
    self.pg_dynp=pg_dynp        # Endstellung anzeigen
    self.playerpos=playerpos
    self.paint()

    if solution=="":
      self.dsp.showIsReady(2, keyLen)   # keine Lösung gefunden
    else:
      self.dsp.showIsReady(1)           # Lösung gefunden
      print self.game_md5, "AutoSolve", self.file_title, self.game_title, solution
      self.db.saveSolution(self.game_md5, "AutoSolve", self.file_title, self.game_title, solution)
      self.solutionUpdate()

      self.solution=solution      # als vorführbare Lösung speichern
      self.isDeadList=[]
      self.showSolutionMode=True  # und Vorführmodus einschalten
      self.showSolutionIdx=0

    self.resetGame()
    self.keyseq=""      
#    self.clearDC=True
    self.displayDirty=True
    self.autosolveActive=False
    self.enableMenu()

    print "secs needed:", time.clock()-ct

    if navigationWinWasOpen==True:
      self.MenuNavW(0)

  # ###########################################################
  # für autoSolveBruteForceOnOneCore()
  def delayed_clearDC(self):
    self.clearDC=True  


  # ###########################################################
  # Aktualisiert die Statuszeile während AutoSolve.
  def __StatusUpdateAS(self, curlen, akttests, tests, count, killed, dictLen):
      self.parent.SetStatusText("cur-len: "+str(curlen+1)+\
              "   tests: "+hlp.intToStringWithCommas(akttests)+\
              " / "+hlp.intToStringWithCommas(tests)+\
              "   total: "+hlp.intToStringWithCommas(count)+\
              "   removed: "+hlp.intToStringWithCommas(killed)+\
              "   dict: "+hlp.intToStringWithCommas(dictLen), 0)
      wx.Yield()





# ###########################################################
# Der Fenster-Rahmen für das Hauptfenster.
class SokobanFrame(wx.Frame):
  def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
    wx.Frame.__init__(self, None, wx.ID_ANY, "Dedes Sokoban v2.0", pos=pos, size=size)
    self.panel=SokobanPanel(self)


# ###########################################################
# Der Starter
if __name__=='__main__':
  app=wx.App(False)

  BASE_PATH=os.path.dirname(os.path.abspath(sys.argv[0]))
  HOME_PATH=os.environ['HOME']
  USERNAME =os.environ['USER']

  CONFIG_FILE=HOME_PATH+"/.soko2rc"
  DB_NAME    =HOME_PATH+"/soko2db.sqlite"

  fc=wx.FileConfig(localFilename=CONFIG_FILE)
  spx=fc.ReadInt("pos_x", -1)
  spy=fc.ReadInt("pos_y", -1)
  ssx=fc.ReadInt("size_x", -1)
  ssy=fc.ReadInt("size_y", -1)
  sp=(spx, spy) # (-1, -1) entspricht wx.DefaultPosition
  ss=(ssx, ssy) # (-1, -1) entspricht wx.DefaultSize
  fn=fc.Read("filename", "")
  if fn!="":
    BASE_PATH=os.path.dirname(fn)

  frame=SokobanFrame(None, pos=sp, size=ss)
  frame.Show(True)
  app.MainLoop()

