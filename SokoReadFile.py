#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
import os

class SokoReadFile():
# Interface:
#   openFile(filename)  -> Erfolgsstatus.Bool
#   loadGame(game_idx)  -> Liste von Strings
#   nextGame()          -> Liste von Strings
#   previousGame()      -> Liste von Strings
#   listGameNames()     -> Liste von Strings
#   getFileTitle()      -> String

  def __init__(self):
    self.filename=""  # der Dateiname der geladenen Datei
    self.isFromClipboard=False
    self.game_idx=-1  # der Index des aktuellen Spieles in der Datei
    self.filedata=""  # die gesamte Datei
    self.fdlst=[]     # die gesamte Datei zeilenweise zerlegt
    self.gametype=-1  # -1=illegal, 0=XML, 1=Namen vor dem Spielfeld, 2=Namen hinter dem Spielfeld


  # ###########################################################
  # Öffnet eine Sokoban-Spiele-Datei (bei Übergabe von cb_strg
  # werden die Daten nicht aus einer Datei, sondern aus
  # cb_strg übernommen).
  # Liefert True, wenn die Datei geöffnet wurde.
  def openFile(self, filename, cb_strg=""):
    self.filename=filename

    if cb_strg!="":
      self.isFromClipboard=True
      self.filedata=cb_strg
    else:
      self.isFromClipboard=False
      try:
        fl=open(filename, "r")
      except:
        return(False)
      self.filedata=fl.read()
      fl.close()

    self.fdlst=self.filedata.split("\n")
    self.gametype=self.__getType()
    return(True)


  # ###########################################################
  # Liefert den Dateinamen.
  def getFilename(self):
    return(self.filename)


  # ###########################################################
  # Liefert die Anzahl der Spiele in der Datei.
  def getGameCount(self):
    return(len(self.listGameNames()))


  # ###########################################################
  # Liefert das Spielfeld mit dem Index "game_idx" als
  # Liste aus Spielfeld-Zeilen - oder [].
  def loadGame(self, game_idx):
    pg=[]
    if self.gametype==0:
      root=etree.fromstring(self.filedata)
      fndColl=root.find("LevelCollection")  # LevelCollection anfahren
      if fndColl!=None:
        fndlst=fndColl.findall("Level")     # alle zugehörigen Level holen
        if fndlst!=None:
          if game_idx<0 or game_idx>=len(fndlst):
            return([])
          ll=fndlst[game_idx].findall("L")
          for l in ll:
            pg.append(l.text)
    elif self.gametype in (1, 2):
      cnt=-1      # Spielezähler
      pgo=False   # Spiel ist offen
      for ln in self.fdlst:   # über alle Zeilen
        lns=ln.strip()
        if lns!="":           # Leerzeilen ausblenden
          if self.__isLegalGameRow(lns)==True:  # wenn Spiel erkannt wurde...
            if pgo==False:                      # ...und noch nicht gezählt wurde...
              cnt+=1                            # ...dann zählen
            if cnt==game_idx:                   # wenn der gesuchte Index erreicht wurde...
              pg.append(ln.rstrip())            # ...Spielfeld speichern
            if cnt>game_idx:                    # Abbruch, wenn gesuchter Index bereits überschritten
              break
            pgo=True
          else:
            pgo=False
    if pg!=[]:
      if self.__checkIsOkay(pg)==True:
        self.game_idx=game_idx  # merken für next- oder previousGame()
      else:
        pg=[]
    return(pg)


  # ###########################################################
  # Liefert True, wenn das Spielfeld den Minimalanforderungen
  # entspricht.
  def __checkIsOkay(self, pg):
    if len(pg)<3:
      return(False) # weniger als drei Zeilen geht nicht

    players=0
    playerpos=()
    goalsquares=0
    boxes=0

    # Objekte zählen
    for y in range(len(pg)):
      for x in range(len(pg[y])):
        if   pg[y][x]=="@":
          players+=1
          playerpos=(x, y)
        elif pg[y][x]=="+":
          players+=1
          playerpos=(x, y)
          goalsquares+=1
        elif pg[y][x]=="$":
          boxes+=1
        elif pg[y][x]=="*":
          boxes+=1
          goalsquares+=1
        elif pg[y][x]==".":
          goalsquares+=1

    if players==0 or goalsquares==0 or boxes==0:
      return(False) # etwas fehlt

    if self.__findOpenBorders(playerpos, pg, False, [])==True:
      return(False) # Spielfeld ist nicht geschlossen

    return(True)


  # ###########################################################
  # Liefert True, wenn das Spielfeld nicht geschlossen ist.
  def __findOpenBorders(self, (x, y), pg, rc, floorList):
    if rc==True:
      return(rc)
    if y<0 or y>=len(pg) or x<0 or x>=len(pg[y]):
      return(True)

    if pg[y][x]=="#":
      return(False)
    if (x, y) in floorList:
      return(False)

    floorList.append((x, y))
    rc=self.__findOpenBorders((x  , y-1), pg, rc, floorList)
    rc=self.__findOpenBorders((x-1, y  ), pg, rc, floorList)
    rc=self.__findOpenBorders((x+1, y  ), pg, rc, floorList)
    rc=self.__findOpenBorders((x  , y+1), pg, rc, floorList)
    return(rc)


  # ###########################################################
  # Liefert das nächste Spielfeld.
  def nextGame(self):
    return(self.loadGame(self.game_idx+1))


  # ###########################################################
  # Liefert das vorige Spielfeld.
  def previousGame(self):
    return(self.loadGame(self.game_idx-1))


  # ###########################################################
  # Liefert eine Liste mit den Namen aller Spiele in der 
  # geladenen Datei - oder [].
  def listGameNames(self):
    if self.gametype==0:
      return(self.__getLevelNameList_XML())
    elif self.gametype==1:
      return(self.__getLevelNameList_NameBefore())
    elif self.gametype==2:
      return(self.__getLevelNameList_NameAfter())
    else:
      return([])


  # ###########################################################
  # Liefert den Namen des Spiels.
  def getGameTitle(self, idx):
    lst=self.listGameNames()
    if idx>=0 and idx<len(lst):
      return(lst[idx])
    return("")


  # ###########################################################
  # Liefert den Namen der Spiele-Datei.
  def getFileTitle(self):
    if self.gametype==0:
      root=etree.fromstring(self.filedata)
      tit=root.find("Title")
      if tit!=None:
        rc=tit.text
      else:
        rc="???"
      return(rc + " / " + self.__getShortFilename())
    elif self.gametype in (1, 2):
      return(self.__getShortFilename())
    return("<<<no file>>>")


  # ###########################################################
  # Liefert den Dateinamen ohne Pfad und Extension.
  def __getShortFilename(self):
    if self.isFromClipboard==True:
      return(self.filename)
    nex=os.path.splitext(self.filename)[0]
    return(os.path.split(nex)[1])


  # ###########################################################
  # Liefert True, wenn "ln" nur Spielfeld-Symbole enthaelt.
  def __isLegalGameRow(self, ln):
    for i in ln:
      if i not in ("#", "@", "+", "$", "*", ".", " "):
        return(False)
    return(True)


  # ###########################################################
  # Liefert den Typ der Datei. Es bedeuten:
  #  0 : XML
  #  1 : Namen vor dem Spielfeld
  #  2 : Namen hinter dem Spielfeld
  def __getType(self):
    if self.__testXML()==True:
      return(0)
    if self.__fileEndsWithPlayground()==True:
      return(1)
    return(2)


  # ###########################################################
  # Liefert True, wenn nach dem letzten Spielfeld in der
  # geladenen Datei höchstens noch Leerzeilen folgen.
  def __fileEndsWithPlayground(self):
    ll=len(self.fdlst)-1          # letzte Zeile
    for t in range(ll, -1, -1):   # Datei rückwärts durchlaufen
      sgs=self.fdlst[t].strip()
      if sgs!="":                 # Leerzeilen ignorieren
        return(self.__isLegalGameRow(sgs))  # letzte nicht-Leerzeile


  # ###########################################################
  # Liefert True, wenn die geladene Datei im XML-Format
  # vorliegt.
  def __testXML(self):
    try:
      root=etree.fromstring(self.filedata)
    except:
      return(False)
    if root.tag!="SokobanLevels":
      return(False)
    if root.find("LevelCollection")==None:
      return(False)
    return(True)


  # ###########################################################
  # Liefert beim XML-Format die Level-Namen als Liste.
  def __getLevelNameList_XML(self):
    lnl=[]
    root=etree.fromstring(self.filedata)
    fndColl=root.find("LevelCollection")
    if fndColl!=None:
      lvl=fndColl.findall("Level")
      for i in lvl:
        lnl.append(str(i.attrib["Id"]))
      return(lnl)
    return(None)


  # ###########################################################
  # Liefert die Level-Namen als Liste bei Dateien mit dem
  # Namen vor dem Spielfeld.
  def __getLevelNameList_NameBefore(self):
    lnl=[]
    lnm=""      # Zeilen-Merker
    nwz=False   # Flag: Name wurde zugefügt
    for ln in self.fdlst:
      lns=ln.strip()
      if lns!="":
        if self.__isLegalGameRow(lns)==True:
          if nwz==False:
            lnl.append(lnm.lstrip(";").strip())
            nwz=True
        else:
          lnm=lns
          nwz=False
    return(lnl)


  # ###########################################################
  # Liefert die Level-Namen als Liste bei Dateien mit dem
  # Namen nach dem Spielfeld.
  def __getLevelNameList_NameAfter(self):
    lnl=[]
    swe=False # Flag: Spielfeld wurde erkannt
    for ln in self.fdlst:
      lns=ln.strip()
      if lns!="":
        if self.__isLegalGameRow(lns)==True:
          swe=True
        else:
          if swe==True:
            lnl.append(ln.lstrip(";").strip())
            swe=False
    return(lnl)

