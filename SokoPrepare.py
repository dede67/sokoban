#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque
import hashlib

import Helper as hlp
import SokoGoodFloors

class SokoPrepare():
# Interface:
#   importPlayground(lines)   -> pg_stat, pg_schk, size, pg_dynp, pg_zfl, playerpos

  def __init__(self):
    #                 L         R         U         D
    self.rtg     =[(-1,  0), ( 1,  0), ( 0, -1), ( 0,  1)]
    self.msk_wall=[ 0x1FFC,     0x1FFC,     0x1FF3,     0x1FF3   ]
    self.msk_badF=[ 0x1FFE,     0x1FFD,     0x1FFB,     0x1FF7   ]

  # ###########################################################
  # Erzeugt aus einem Spielfeld, das in "lines" als Liste von
  # Zeilen übergeben wurde, die interne Spielfeld-Struktur.
  def importPlayground(self, lines):
    minspc, maxlen=self.__getPlaygroundSize(lines)

    self.pg_stat=[]    # das statische Spielfeld als Matrix (Zeichenvorrat: "#", " ", ".", "u", "i", "_")
    self.pg_schk=[]    # wie pg_stat, allerdings nur mit dem Zeichenvorrat "Hindernis" ("#") und "überquerbar" (" ")
    self.pg_zfl=[]     # Koordinaten-Liste der Zielfelder
    self.pg_dynp=[]    # das dynamische Spielfeld als gepackte Koordinaten-Liste von Boxen
    self.playerpos=()  # die Koordinaten der Spielfigur
    self.size=()       # die Abmessungen des Spielfeldes (breite, höhe)

    lines_new=[]
    y=0
    for l in lines:   # über alle Zeilen
      ln=[]
      x=0
      l+=" "*maxlen # Zeilen verlängern
      lines_new.append(l[minspc:maxlen].rstrip())
      for c in l[minspc:maxlen]:  # über alle Spalten der jew. Zeile
        # Zeile als Liste von Characters aufbauen
        if c in ("#", " ", "."):  # Mauer, Boden, Zielfeld
          ln.append(c)
        if c in ("*", "+"):       # Box/Spielfigur auf Zielfeld
          ln.append(".")
          self.pg_zfl.append((x, y))
        if c==".":                # Zielfeld
          self.pg_zfl.append((x, y))
        if c in ("@", "$"):       # Spielfigur oder Box
          ln.append(" ")

        if c in ("@", "+"):       # Spielfigur [auf Zielfeld]
          self.playerpos=(x, y)

        if c in ("$", "*"):       # Box [auf Zielfeld]
          self.pg_dynp.append(hlp.ppack(x, y))

        x+=1
      self.pg_stat.append(ln)
      y+=1
    self.size=(x, y)
    self.__markUnreachableFloors()

    gf=SokoGoodFloors.SokoGoodFloors(self.pg_stat, self.pg_dynp, self.pg_zfl, self.playerpos)
    goodfloors=gf.findGoodFloors()

    # Spielfeld in ein weiteres kopieren, das nur Walls und Floors enthält.
    # Zusätzlich noch badFloors im Haupt-Spielfeld markieren.
    for y in range(self.size[1]):
      ln=[]
      for x in range(self.size[0]):
        if self.pg_stat[y][x] in ("#", "i", "u"):
          ln.append("#")
        else:
          ln.append(" ")
        if self.pg_stat[y][x]==" " and (x, y) not in goodfloors:  # wenn Floor und nicht guter Floor...
          if hlp.ppack(x, y) not in self.pg_dynp:                 # ...und initial keine Box drauf steht...
            self.pg_stat[y][x]="_"                                # ...dann als badFloor markieren
      self.pg_schk.append(ln)

    self.pg_dof=self.degreeOfFreedom(self.pg_stat, self.size)
#    for y in range(len(self.pg_dof)):
#      ln=[]
#      for x in range(len(self.pg_dof[y])):
#        ln.append("{0:09b}".format(self.pg_dof[y][x]))
#      print ln

    self.pg_dynp.sort()
    return(self.pg_stat, self.pg_schk, self.pg_dof, self.size, self.pg_dynp, self.pg_zfl, self.playerpos, lines_new)



  # ###########################################################
  # Liefert ein Array analog zu pgs, bei dem alle Floors mit
  # ihrem jeweiligen Freiheitsgrad vermerkt sind.
  # Die Bewegungsrichtungen sind im Low-Nibble kodiert.
  # Die Werte bedeuten:
  #  DURL
  #  0001 - nach links  schiebbar
  #  0010 - nach rechts schiebbar
  #  0100 - nach oben   schiebbar
  #  1000 - nach unten  schiebbar
  def degreeOfFreedom(self, pgs, size):
    dof=[]
    for y in range(size[1]):
      dof_line=[]
      for x in range(size[0]):
        o=pgs[y][x]
        if   o=="_":
          dof_line.append(0x1000) # BadFloor
        elif o in (" ", "."):
          dof_line.append(0x1F0F) # Floor oder GoalSquare
        else:
          dof_line.append(0x0000) # Wall bzw. unpassierbares Hindernis
      dof.append(dof_line)

    # In dof steht jetzt eine Kopie von pgs, bei der alle Floors den
    # Wert 0x100F, alle BadFloors 0x1000 und der Rest 0x0000 enthalten.
    # Nun werden bei Floors Bits ausgeblendet, abhängig von der
    # Nachbarschaft.
    for y in range(size[1]):
      for x in range(size[0]):
        if dof[y][x]>=0x1000:                       # wenns passierbar ist...
          for r in range(4):                        # ...über die vier Nachbarfelder...
            n=dof[y+self.rtg[r][1]][x+self.rtg[r][0]]
            if n==0x1000:                           # wenn Nachbar BadFloor ist...
              dof[y][x]&=self.msk_badF[r]           # ...BadFloor-Maske anwenden
            if n==0x0000:                           # wenn Nachbar Wall ist...
              dof[y][x]&=self.msk_wall[r]           # ...Wall-Maske anwenden
    return(dof)


  # ###########################################################
  # Liefert das Spielfeld in Rohform - allerdings mit
  # koorigiertem linken Rand (zur V1-kompatiblen MD5-Erzeugung).
  def getLines(self, lines):
    minspc, maxlen=self.__getPlaygroundSize(lines)

    lines_new=[]
    for l in lines:   # über alle Zeilen
      l+=" "*maxlen   # Zeilen verlängern
      lines_new.append(l[minspc:maxlen].rstrip())
    return(lines_new)

  # ###########################################################
  # Liefert die Breite und Höhe des Spielfeldes.
  def getSize(self, lines):
    y=0
    x=0
    for l in lines:
      y+=1
      x=max(x, len(l))
    return(x, y)

  # ###########################################################
  # Liefert die MD5-Summe für das Spielfeld.
  def getMD5(self, lines):
    strg=""
    for y in range(len(lines)):
      for x in range(len(lines[y])):
        strg+=lines[y][x]
      strg+="\n"
    return(hashlib.md5(strg).hexdigest())


  # ###########################################################
  # Liefert als ersten Rückgabewert die Anzahl von Leerzeichen,
  # die in jeder Zeile am linken Rand vorkommen und als zweiten
  # Rückgabewert die Länge der längsten Spielfeldzeile in
  # Characters (ohne Abzug des ersten Parameters).
  def __getPlaygroundSize(self, lines):
    minspc=len(lines[0])  # Init(Leerzeichenzähler) mit der Länge der ersten Zeile
    maxlen=0              # Init(längste Zeile) mit 0
    for l in lines:   # über alle Zeilen
      curspc=0
      maxlen=max(maxlen, len(l))
      for c in l:     # über alle Spalten der jew. Zeile
        if c==" ":    # wenn Leerzeichen...
          curspc+=1   # ...zählen
        else:
          break       # ...sonst fertig mit dieser Zeile
      minspc=min(minspc, curspc)
    return(minspc, maxlen)


  # ###########################################################
  # Ändert die Kennung von unerreichbaren Floors im statischen
  # Spielfeld. Dazu werden alle von der Player-Position aus
  # erreichbaren Felder bestimmt und dann der Rest markiert.
  # Werden im unerreichbaren Bereich GoalSquares oder Boxen
  # gefunden, werden diese mit der Kennung "i" (für illegal)
  # in das statische Spielfeld aufgenommen und die Listen
  # self.pg_zfl bzw. self.pg_dynp entsprechend gekürzt. Ansonsten
  # würde die IsSolved-Erkennung ggf. nicht mehr greifen.
  def __markUnreachableFloors(self):
    self.reachableFloors=self.__findReachableFloors(self.playerpos, [])
    for y in range(self.size[1]):
      for x in range(self.size[0]):
        if (x, y) not in self.reachableFloors:  # wenn Feld nicht erreichbar (oder Wall ist)...
          if self.pg_stat[y][x]=="#":
            continue

          if   self.pg_stat[y][x]==" ": # ...und Floor ist...
            self.pg_stat[y][x]="u"      # ...dann "u" als Kennung setzen
          elif self.pg_stat[y][x]==".": # ...und GoalSquare ist...
            self.pg_stat[y][x]="i"      # ...dann "i" als Kennung setzen
            self.pg_zfl.remove((x, y))  # ...dann aus self.pg_zfl entfernen

          if hlp.ppack(x, y) in self.pg_dynp:     # wenn es eine Box ist...
            self.pg_stat[y][x]="i"                # ...dann "i" als Kennung setzen
            self.pg_dynp.remove(hlp.ppack(x, y))  # ...und aus self.pg_dynp entfernen


  # ###########################################################
  # Liefert die Positionen von allen Böden, die direkt von
  # dem Boden aus erreichbar sind, dessen Koordinaten
  # übergeben wurden.
  #
  # Es werden rekursiv folgende Positionen geprüft.
  #          0,-1
  #  -1, 0  (x, y)  1, 1
  #          0, 1
  def __findReachableFloors(self, (x, y), floorList):
    if self.pg_stat[y][x]=="#":
      return(floorList)
    if (x, y) in floorList:
      return(floorList)

    floorList.append((x, y))
    floorList=self.__findReachableFloors((x  , y-1), floorList)
    floorList=self.__findReachableFloors((x-1, y  ), floorList)
    floorList=self.__findReachableFloors((x+1, y  ), floorList)
    floorList=self.__findReachableFloors((x  , y+1), floorList)
    return(floorList)

