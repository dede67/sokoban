#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os, sys


# ###########################################################
# Der Fenster-Rahmen für das Navigations-Fenster.
class NavigationArea(wx.Frame):
  def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
    wx.Frame.__init__(self, None, pos=pos, size=size, title="Navigation")

    self.parent=parent
    self.Bind(wx.EVT_CLOSE, self.onClose)
    self.BASE_PATH=os.path.dirname(os.path.abspath(sys.argv[0]))
    self.InitUI()
    self.Show()


  # ###########################################################
  # Bei close die aktuelle Fenster-Position ans Hauptprogramm
  # liefern.
  def onClose(self, event):
    sp=self.GetScreenPosition()
    ss=self.GetSizeTuple()
    self.parent.navcom.SetValue("close,"+str(sp[0])+","+str(sp[1])+","+str(ss[0])+","+str(ss[1]))
    self.Destroy()


  # ###########################################################
  # Der eigentliche Fensterinhalt
  def InitUI(self):
    panel=wx.Panel(self)

    self.up=wx.BitmapButton(panel,  1, wx.Bitmap(self.BASE_PATH+'/icons/go-up.png'),                (-1, -1), (50, 50))
    self.dn=wx.BitmapButton(panel,  2, wx.Bitmap(self.BASE_PATH+'/icons/go-down.png'),              (-1, -1), (50, 50))
    self.lt=wx.BitmapButton(panel,  3, wx.Bitmap(self.BASE_PATH+'/icons/go-previous.png'),          (-1, -1), (50, 50))
    self.rt=wx.BitmapButton(panel,  4, wx.Bitmap(self.BASE_PATH+'/icons/go-next.png'),              (-1, -1), (50, 50))
    self.ud=wx.BitmapButton(panel,  5, wx.Bitmap(self.BASE_PATH+'/icons/media-seek-backward.png'),  (-1, -1), (50, 50))
    self.rf=wx.BitmapButton(panel,  6, wx.Bitmap(self.BASE_PATH+'/icons/view-refresh.png'),         (-1, -1), (50, 50))
    self.fw=wx.BitmapButton(panel,  7, wx.Bitmap(self.BASE_PATH+'/icons/media-seek-forward.png'),   (-1, -1), (50, 50))
    self.rg=wx.BitmapButton(panel,  8, wx.Bitmap(self.BASE_PATH+'/icons/media-playback-stop.png'),  (-1, -1), (50, 50))
    self.pg=wx.BitmapButton(panel,  9, wx.Bitmap(self.BASE_PATH+'/icons/media-skip-backward.png'),  (-1, -1), (50, 50))
    self.ng=wx.BitmapButton(panel, 10, wx.Bitmap(self.BASE_PATH+'/icons/media-skip-forward.png'),   (-1, -1), (50, 50))

    self.up.SetToolTip(wx.ToolTip('move player up [cursor up]'))
    self.dn.SetToolTip(wx.ToolTip('move player down [cursor down]'))
    self.lt.SetToolTip(wx.ToolTip('move player left [cursor left]'))
    self.rt.SetToolTip(wx.ToolTip('move player right [cursor right]'))
    self.ud.SetToolTip(wx.ToolTip('undo last move [key="u"]'))
    self.rf.SetToolTip(wx.ToolTip('refresh/repaint playground [key="F5"]'))
    self.fw.SetToolTip(wx.ToolTip('next move (in solution) [key="s"]'))
    self.rg.SetToolTip(wx.ToolTip('restart game [key="ESC"]'))
    self.pg.SetToolTip(wx.ToolTip('goto previous game [key="BACKSPACE"]'))
    self.ng.SetToolTip(wx.ToolTip('goto next game [key="SPACE"]'))

    self.up.Bind(wx.EVT_BUTTON, self.up_klick)
    self.dn.Bind(wx.EVT_BUTTON, self.dn_klick)
    self.lt.Bind(wx.EVT_BUTTON, self.lt_klick)
    self.rt.Bind(wx.EVT_BUTTON, self.rt_klick)
    self.ud.Bind(wx.EVT_BUTTON, self.ud_klick)
    self.rf.Bind(wx.EVT_BUTTON, self.rf_klick)
    self.fw.Bind(wx.EVT_BUTTON, self.fw_klick)
    self.rg.Bind(wx.EVT_BUTTON, self.rg_klick)
    self.pg.Bind(wx.EVT_BUTTON, self.pg_klick)
    self.ng.Bind(wx.EVT_BUTTON, self.ng_klick)

    self.up.Bind(wx.EVT_CHAR, self.onChar)
    self.dn.Bind(wx.EVT_CHAR, self.onChar)
    self.lt.Bind(wx.EVT_CHAR, self.onChar)
    self.rt.Bind(wx.EVT_CHAR, self.onChar)
    self.ud.Bind(wx.EVT_CHAR, self.onChar)
    self.rf.Bind(wx.EVT_CHAR, self.onChar)
    self.fw.Bind(wx.EVT_CHAR, self.onChar)
    self.rg.Bind(wx.EVT_CHAR, self.onChar)
    self.pg.Bind(wx.EVT_CHAR, self.onChar)
    self.ng.Bind(wx.EVT_CHAR, self.onChar)

    sizer=wx.GridBagSizer(1, 1)
    border=2
    sizer.Add(self.up, (0, 1), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.lt, (1, 0), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.rt, (1, 2), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.dn, (1, 1), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(wx.StaticLine(panel), pos=(2, 0), span=(1, 3), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.ud, (3, 0), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.rf, (3, 1), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.fw, (3, 2), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(wx.StaticLine(panel), pos=(4, 0), span=(1, 3), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.rg, (5, 0), (1, 3), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(wx.StaticLine(panel), pos=(6, 0), span=(1, 3), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.pg, (7, 0), flag=wx.ALL|wx.GROW, border=border)
    sizer.Add(self.ng, (7, 2), flag=wx.ALL|wx.GROW, border=border)

    panel.SetSizer(sizer)
    sizer.Fit(self)
    self.up.SetFocus()

  # ###########################################################
  # Verarbeitet Tastatureingaben.
  def onChar(self, event):
    key=event.GetKeyCode()

    if   key==wx.WXK_LEFT:  # links
      self.parent.navcom.SetValue("lt")
      self.lt.SetFocus()
    elif key==wx.WXK_RIGHT: # rechts
      self.parent.navcom.SetValue("rt")
      self.rt.SetFocus()
    elif key==wx.WXK_UP:    # hoch
      self.parent.navcom.SetValue("up")
      self.up.SetFocus()
    elif key==wx.WXK_DOWN:  # runter
      self.parent.navcom.SetValue("dn")
      self.dn.SetFocus()
    elif key==ord("u"):     # undo
      self.parent.navcom.SetValue("ud")
      self.ud.SetFocus()
    elif key==ord("s"):     # solution step
      self.parent.navcom.SetValue("fw")
      self.fw.SetFocus()
    elif key==wx.WXK_ESCAPE:# Reload
      self.parent.navcom.SetValue("rg")
      self.rg.SetFocus()
    elif key==wx.WXK_SPACE: # next game
      self.parent.navcom.SetValue("ng")
      self.ng.SetFocus()
    elif key==wx.WXK_BACK:  # previos game
      self.parent.navcom.SetValue("pg")
      self.pg.SetFocus()
    elif key==wx.WXK_F5:    # refresh
      self.parent.navcom.SetValue("rf")
      self.rf.SetFocus()


  # ###########################################################
  # Die Button-Funktionen.
  def up_klick(self, event):    self.parent.navcom.SetValue("up")
  def dn_klick(self, event):    self.parent.navcom.SetValue("dn")
  def lt_klick(self, event):    self.parent.navcom.SetValue("lt")
  def rt_klick(self, event):    self.parent.navcom.SetValue("rt")

  def ud_klick(self, event):    self.parent.navcom.SetValue("ud")
  def rf_klick(self, event):    self.parent.navcom.SetValue("rf")
  def fw_klick(self, event):    self.parent.navcom.SetValue("fw")

  def rg_klick(self, event):    self.parent.navcom.SetValue("rg")

  def ng_klick(self, event):    self.parent.navcom.SetValue("ng")
  def pg_klick(self, event):    self.parent.navcom.SetValue("pg")

