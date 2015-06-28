#!/usr/bin/env python
# -*- coding: utf-8 -*-

import SokoDB         # Klasse= Database()

import wx
import os, sys

import threading
import subprocess


# ###########################################################
# Der Fenster-Rahmen für das HostSelect-Fenster.
class HostSelect(wx.Dialog):
  def __init__(self, parent, CONFIG_FILE, DB_NAME, db_obj):
    super(HostSelect, self).__init__(parent=parent, title="manage remote sokoban hosts")

    self.parent=parent
    self.CONFIG_FILE=CONFIG_FILE
    self.DB_NAME=DB_NAME
    self.db=db_obj

    self.MenueErstellen()

    self.InitUI()
    self.load_from_config_file()
    self.Show()


  # ###########################################################
  # Der eigentliche Fensterinhalt
  def InitUI(self):
    vsizer=wx.BoxSizer(wx.VERTICAL)

    txt1=wx.StaticText(self, label="  host:")
    self.host=wx.TextCtrl(self, size=(100, -1))
    txt2=wx.StaticText(self, label="  path:")
    self.path=wx.TextCtrl(self, size=(200, -1))
    txt3=wx.StaticText(self, label="  file:")
    self.file=wx.TextCtrl(self, size=(100, -1), style=wx.TE_READONLY)
    self.file.SetValue(os.path.basename(self.DB_NAME))
    self.file.Enable(False)
    self.addBut=wx.Button(self, label="&Add", size=(50 , -1))
    self.addBut.Bind(wx.EVT_BUTTON, self.addBut_Pressed)

    sb1=wx.StaticBox(self, 1, " add new host")
    nh_sizer=wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
    nh_sizer.Add(txt1,           0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(self.host,      0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(txt2,           0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(self.path,      0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(txt3,           0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(self.file,      0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    nh_sizer.Add(self.addBut,    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
    vsizer.Add(nh_sizer, 0, wx.ALL|wx.EXPAND, 5)

    ha_sizer=wx.BoxSizer(wx.HORIZONTAL)
    img=wx.StaticBitmap(self, bitmap=wx.ArtProvider_GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX, (20, 20)))
    txt4=wx.StaticText(self, label="Don't forget the key exchange! The scp must work without passwords.")
    ha_sizer.Add(img, 0, wx.ALL|wx.EXPAND, 5)
    ha_sizer.Add(txt4, 0, wx.ALL|wx.EXPAND, 5)
    vsizer.Add(ha_sizer, 0, wx.ALL|wx.EXPAND, 5)

    self.pingBut=wx.Button(self, size=(50, -1), label="&check\nonline")
    self.hostlist=wx.ListCtrl(self, size=(550, 200), style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
    self.hostlist.InsertColumn(0, "host", width=150)
    self.hostlist.InsertColumn(1, "path", width=250)
    self.hostlist.InsertColumn(2, "file", width=100)
    self.hostlist.InsertColumn(3, "online", width=50)
    self.hostlist.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
    self.pingBut.Bind(wx.EVT_BUTTON, self.pingBut_Pressed)
    self.hostlist.SetToolTip(wx.ToolTip('use context menu'))

    sb2=wx.StaticBox(self, 1, " previously defined hosts")
    hl_sizer=wx.StaticBoxSizer(sb2, wx.HORIZONTAL)
    hl_sizer.Add(self.hostlist, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
    hl_sizer.Add(self.pingBut, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
    vsizer.Add(hl_sizer, 0, wx.ALL|wx.EXPAND, 5)

    self.closeBut=wx.Button(self, wx.ID_CANCEL, label="Close", size=(100 , -1))
    vsizer.Add(self.closeBut, 0, wx.ALL|wx.ALIGN_RIGHT, 5)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.host.SetFocus()


  # ###########################################################
  # CheckOnline-Button wurde betaetigt -> pro Eintrag im
  # ListCtrl einen Ping-Thread starten.
  def pingBut_Pressed(self, event):
    for i in range(self.hostlist.GetItemCount()):
      self.hostlist.SetStringItem(i, 3, "")
      host=self.hostlist.GetItem(i, 0).GetText()
      worker=threading.Thread(target=self.__pinger, name="Pinger"+str(i), args=(i, host, ))
      worker.start()


  # ###########################################################
  # Den Host "host" (mit dem Index "idx" im ListCtrl) anpingen
  # und bei Antwort des Hosts dessen Index an __after_pinger
  # weitergeben.
  def __pinger(self, idx, host):
    ret=subprocess.call("ping -c 1 {host}".format(host=host), shell=True,
                         stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if ret==0:
      wx.CallAfter(self.__after_pinger, idx)


  # ###########################################################
  # Aus einem Thread sollen keine wx-Funktionen aufgerufen
  # werden. Daher hier via CallAfter.
  def __after_pinger(self, idx):
    self.hostlist.SetStringItem(idx, 3, "online")


  # ###########################################################
  # Add-Button wurde betaetigt
  def addBut_Pressed(self, event):
    if self.host.GetValue()!="" and self.path.GetValue()!="":
      # wenn beide Werte belegt sind...
      fnd=False
      # ...prüfen, ob schon in der Liste vorhanden
      for i in range(self.hostlist.GetItemCount()):
        if self.host.GetValue()==self.hostlist.GetItem(i, 0).GetText() and \
           self.path.GetValue()==self.hostlist.GetItem(i, 1).GetText():
          fnd=True
          break
      if fnd==False:
        # wenn noch nicht vorhanden -> zufügen
        self.hostlist.Append((self.host.GetValue(), self.path.GetValue(), self.file.GetValue()))
        self.write_to_config_file(self.host.GetValue(), self.path.GetValue())


  # ###########################################################
  # Stellt das Kontext-Menue dar, sofern in dem ListCtrl eine
  # Zeile selektiert ist.
  def OnContextMenu(self, event):
    if self.hostlist.GetFirstSelected()>=0:
      self.PopupMenu(self.menue)


  # ###########################################################
  # Legt das Kontext-Menue an.
  def MenueErstellen(self):
    self.menue=wx.Menu()
    self.menue.Append(100, 'merge solutions from this host:path')
    self.menue.AppendSeparator()
    self.menue.Append(101, 'delete host:path')

    self.Bind(wx.EVT_MENU, self.sync, id=100)
    self.Bind(wx.EVT_MENU, self.delete_host, id=101)


  # ###########################################################
  # Kopiert von selektierten host:path die DB-Datei nach /tmp/
  # und importiert danach [bessere] Lösungen daraus.
  def sync(self, event):
    sel=self.hostlist.GetFirstSelected()
    if sel>=0: # doppelt pruefen schadet nix
      host=self.hostlist.GetItem(sel, 0).GetText()
      path=self.hostlist.GetItem(sel, 1).GetText()
      filename=self.hostlist.GetItem(sel, 2).GetText()
      cmd="scp -B {host}:{path}/{filename} /tmp".format(host=host, path=path, filename=filename)
      ret=subprocess.call(cmd, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
      if ret!=0:
        wx.MessageBox('An error occured while executing the following command:\n\t'+cmd+ \
                      '\n\nReturncode was '+str(ret), 'Error', wx.OK | wx.ICON_ERROR)
      else:
        fn="/tmp/"+filename
        if self.db.isSokoV2DB(fn)==True:
          ins_cnt, upd_cnt=self.db.mergeDB(fn)
          wx.MessageBox("Imported solutions: "+str(ins_cnt)+\
                        "  Updated solutions: "+str(upd_cnt), "Result", wx.OK | wx.ICON_INFORMATION)


  # ###########################################################
  # Verarbeitet das Loeschen eines Hosts im ListCtrl und im
  # Config-File.
  def delete_host(self, event):
    sel=self.hostlist.GetFirstSelected()
    if sel>=0: # doppelt pruefen schadet nix
      host=self.hostlist.GetItem(sel, 0).GetText()
      path=self.hostlist.GetItem(sel, 1).GetText()
      self.hostlist.DeleteItem(sel) # aus Liste loeschen

      # aus CONFIG_FILE loeschen und ggf. keys umbenennen
      fc=wx.FileConfig(localFilename=self.CONFIG_FILE)
      sync_host_cnt=fc.ReadInt("sync_host_cnt", 0)
      ren=False
      # ueber alle gespeicherten Hosts
      for i in range(1, sync_host_cnt+1):
        h, p=fc.Read("sync_host_"+str(i), "").split(":", 1)
        if ren==True:
          # wenn ein Host geloescht wurde, die folgenden Hosts
          # bzgl. Nummerierung um eins "ranziehen"
          fc.RenameEntry("sync_host_"+str(i), "sync_host_"+str(i-1))
        if h==host and p==path:
          # der zu loeschende Host ist gefunden
          fc.DeleteEntry("sync_host_"+str(i))
          ren=True
      # counter korrigieren
      fc.WriteInt("sync_host_cnt", sync_host_cnt-1)
      fc.Flush()


  # ###########################################################
  # Laedt die im Config-File abgelegten Hosts ins ListCtrl.
  def load_from_config_file(self):
    fc=wx.FileConfig(localFilename=self.CONFIG_FILE)    
    sync_host_cnt=fc.ReadInt("sync_host_cnt", 0)
    for i in range(1, sync_host_cnt+1):
      host, path=fc.Read("sync_host_"+str(i), "").split(":", 1)
      filename=self.file.GetValue()
      self.hostlist.Append((host, path, filename))


  # ###########################################################
  # Schreibt einen neu zugefuegten Host ins Config-File.
  def write_to_config_file(self, host, path):
    fc=wx.FileConfig(localFilename=self.CONFIG_FILE)
    sync_host_cnt=fc.ReadInt("sync_host_cnt", 0)+1
    fc.WriteInt("sync_host_cnt", sync_host_cnt)
    fc.Write("sync_host_"+str(sync_host_cnt), host+":"+path)
    fc.Flush()

