#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Helper as hlp
import SokoDeadTests
import SokoAreas

from collections import deque
#import wx


class SokoMove():
# Interface:
#   inverseMovePlayer(pgs, pgd, pp, d)        -> status(0-2), Playerpos
#   movePlayer(pgs, pgd, pp, d)               -> status(0-2), Bewegungsstring-Verlängerung, Playerpos, Boxpos
#   findPossiblePushes(pgs, pgdp, playerpos)  -> Liste von Pushes
#   findBestWayTo(pgs, pgdp, pp, dest_pos)    -> Bewegungsstring

  def __init__(self):
    #         L,  R,  U,  D
    self.mx=[-1,  1,  0,  0]  # mx/my = relative Position des Zielfeldes der Spielfigur
    self.my=[ 0,  0, -1,  1]
    self.bx=[-2,  2,  0,  0]  # bx/by = relative Position, auf die eine Box vom Zielfeld geschoben wird
    self.by=[ 0,  0, -2,  2]
    self.ix=[ 1, -1,  0,  0]  # ix/iy = relative Position, von der eine Box vom Startfeld gezogen wird
    self.iy=[ 0,  0,  1, -1]
    self.hx=[-3,  3,  0,  0]  # hx/hy = relative Position hinter der Box in Schiebe-Richtung
    self.hy=[ 0,  0, -3,  3]
    self.ss=["L", "R", "U", "D"]  # Zeichen für Lösungsstring

    self.rp=[(0, -1), (0, 1), (-1, 0), (1, 0)]   # relative Spieler-Koordinaten um die Box (hoch, runter, links, rechts)
    self.sr=[      3,      2,       1,      0]   # Schiebe-Richtungen vom Spieler zur Box (invers (DURL))
    self.sm=[ 0x0800, 0x0400, 0x0200,  0x0100]
    self.rt=[    "u",    "d",     "l",    "r"]
    self.pt=[(0, 1), (0, -1), (1, 0), (-1, 0)]   # Feld hinter der Box in Schiebe-Richtung

    self.deadTest=SokoDeadTests.SokoDeadTests()
    self.areas=SokoAreas.SokoAreas()

  # ###########################################################
  # Führt einen inversen Zug aus (die Box wird also gezogen).
  # pgd wird (beim Aufrufer) geändert.
  # Es macht keinen Unterschied, welche Version des statischen
  # Spielfeldes übergeben wird.
  def inverseMovePlayer(self, pgs, pgd, pp, d):
    np=(pp[0]+self.mx[d], pp[1]+self.my[d])     # Koordinaten Player-Zielfeld
    if pgs[np[1]][np[0]]!="#":                  # kein Wall auf dem Player-Zielfeld
      if hlp.ppackt(np) not in pgd:             # und keine Box auf dem Player-Zielfeld
        bp=hlp.ppack(pp[0]+self.ix[d], pp[1]+self.iy[d])   # Koordinaten Box-Startfeld
        if bp in pgd:                           # ziehbare Box am Player-Startfeld
          pgd.remove(bp)
          pgd.append(hlp.ppackt(pp))
          return((2, np))
        else:
          return((1, np))
    return((0, pp))


  # ###########################################################
  # Bewegt die Spielfigur (sofern möglich) in die angegebene
  # Richtung. Ggf. wird eine Box bewegt.
  # Aufruf-Parameter:
  #   Spielfeld-statisch,     Array[y][x] mit Zeichenvorrat " " und "#"
  #   Spielfeld-dynamisch,    Liste von gepackten Box-Koordinaten (x, y)
  #   Spielerposition,        Koordinaten (x, y)
  #   Bewegungsrichtung       0-3 ("L", "R", "U", "D")
  #   Tot-Status              True für tot
  # Rückgabe:
  #   Status (0=keine Bewegung/illegal, 1=nur-Spieler-Bewegung, 2=Box-Bewegung)
  #   anzuhängender Bewegungsstring     Character ("LRUDlrud")
  #   neue Spielerposition              Koordinaten (x, y)
  #   neue Koordinaten der geschobenen Box oder (), wenn nicht geschoben wurde
  #   isDead-Status
  #
  #   pgdp wird (beim Aufrufer) geändert
  def movePlayer(self, pgs, dof, pgdp, pp, d, deadCheck=True):
    np=(pp[0]+self.mx[d], pp[1]+self.my[d])     # Koordinaten Player-Zielfeld
    if pgs[np[1]][np[0]]!="#":                  # kein Wall auf dem Player-Zielfeld
      if hlp.ppackt(np) not in pgdp:            # keine Box auf dem Player-Zielfeld
        return(1, self.ss[d].lower(), np, (), False)
      else:                                     # Box auf dem Player-Zielfeld
        bp=(pp[0]+self.bx[d], pp[1]+self.by[d]) # Koordinaten Box-Zielfeld
        if pgs[bp[1]][bp[0]]!="#":              # kein Wall auf dem Box-Zielfeld
          if hlp.ppackt(bp) not in pgdp:        # keine Box auf dem Box-Zielfeld
            pgdp.remove(hlp.ppackt(np))
            pgdp.append(hlp.ppackt(bp))

#            self.areas.findAreas(pgs, pgdp)
#            self.deadTest.updateDegreeOfFreedom(dof, pgdp)
#            self.__finalizeDegreeOfFreedom(pgs, dof, pgdp, pp)

            if deadCheck==True:
              isdead=self.__isDead(pgs, pgdp, pp, bp, (pp[0]+self.hx[d], pp[1]+self.hy[d]))
            else:
              isdead=False
#            print hlp.unpackMovList(self.findPossiblePushes(pgs, pgdp, np))
            return(2, self.ss[d].upper(), np, bp, isdead)
    return(0, "", pp, (), False)


  # ###########################################################
  #
  def __finalizeDegreeOfFreedom(self, pgs, dof, pgdp, pp):
    rlst=[]
    floors, bList=self.__findReachableBoxes(pgs, pgdp, pp)

    for b in bList:             # über alle erreichbaren Boxen
      bx, by=hlp.punpack(b)

      dof[by][bx]&=0x10FF
      for r in range(4):        # über alle Schiebe-Koordinaten
        x=bx+self.rp[r][0]
        y=by+self.rp[r][1]      # Player-Pos für aktuelle Schiebe-Richtung
        xyp=hlp.ppack(x, y)
        if xyp in floors:       # wenn Player-Pos innerhalb der erreichbaren Felder...
#          rlst.append(((bx, by), self.sr[r]))
#          dof[by][bx]|=self.sm[r]
          dof[by][bx]|=(self.sm[r] & ((dof[by][bx]&0x00F0)<<4))

#    print rlst

#    print hlp.unpackMovList(rlst)


  # ###########################################################
  #
  def findAreas(self, pgs, pgdp):
    floorsList=[]
    boxesList=[]
    for y in range(len(pgs)):
      for x in range(len(pgs[y])):
        if pgs[y][x] in (" ", "_"):
          for l in floorsList:
            if hlp.ppack(x, y) not in l:
              floors, boxes=self.__findReachableBoxes(pgs, pgdp, (x, y))
              floorList.append(floors)
              boxesList.append(boxes)
    for l in floorsList:
      print l

  # ###########################################################
  # Liefert die Koordinaten aller von (x, y) aus
  # erreichbaren Boxen und Floors.
  # Rückgabe:
  # 1.) ein Dictionary mit den gepackten Koordinaten aller
  #     von (x, y) aus erreichbaren Böden.
  # 2.) eine Liste aller von (x, y) aus erreichbaren Boxen.
  def __findReachableBoxes(self, pgs, pgdp, (x, y)):
    bList=[]
    queue=deque([(x, y)]) # Startposition auf die Queue
    visited={hlp.ppack(x, y):1}
    while queue:            # über alle Einträge der Queue
      x, y=queue.popleft()  # aktuellen Eintrag entnehmen

      for i in range(4):    # über die vier Bewegungsrichtungen
        xn=x+self.rp[i][0]
        yn=y+self.rp[i][1]
        xynp=hlp.ppack(xn, yn)
        if xynp not in visited:       # wenn Koordinate noch nicht untersucht wurde...
          if xynp in pgdp:            # ...und wenn Box gefunden wurde...
            if xynp not in bList:     # ...und wenn sie noch nicht vermerkt wurde...
              bList.append(xynp)      # ...dann Koordinaten vermerken
          elif pgs[yn][xn]!="#":      # ansonsten: wenn etwas Betretbares gefunden wurde...
            queue.append((xn, yn))    # ...auf die Queue damit
            visited.update({xynp:1})
    return((visited, bList))


  # ###########################################################
  # Liefert eine Liste von allen derzeit möglichen Pushes.
  def findPossiblePushes(self, pgs, pgdp, playerpos):
    rlst=[]
    floors, bList=self.__findReachableBoxes(pgs, pgdp, playerpos)

    for b in bList:             # über alle erreichbaren Boxen
      bx, by=hlp.punpack(b)
      for r in range(4):        # über alle Schiebe-Koordinaten
        x=bx+self.rp[r][0]
        y=by+self.rp[r][1]      # Player-Pos für aktuelle Schiebe-Richtung
        xyp=hlp.ppack(x, y)
        if xyp in floors:       # wenn Player-Pos innerhalb der erreichbaren Felder...
          xh=bx+self.pt[r][0]   # x,y für schnellen Vortest, ob Zug legal sein wird....
          yh=by+self.pt[r][1]
          if pgs[yh][xh] not in ("#", "_"):
            # es wird nicht gegen eine Wall oder auf badFloor geschoben
            if hlp.ppack(xh, yh) not in pgdp:
              # es wird nicht gegen eine Box geschoben
              rlst.append((xyp<<2)+self.sr[r]) # also Zug zum weiteren testen vormerken
    return(rlst)


  # ###########################################################
  # Liefert den kürzesten [freien] Weg von (cur_x, cur_y) nach
  # (x_dest, y_dest). Der Weg wird als Bewegungs-String
  # geliefert.
  # Pseudocode abgehacked von: http://de.wikipedia.org/wiki/Breitensuche
  def findBestWayTo(self, pgs, pgdp, (cur_x, cur_y), (x_dest, y_dest)):
    queue=deque([(cur_x, cur_y, "")])
    visited=[(cur_x, cur_y)]
    while queue:
      cur_x, cur_y, ks=queue.popleft()
      if (cur_x, cur_y)==(x_dest, y_dest):
        return(ks)
      for i in range(4):
        nx=cur_x+self.rp[i][0]
        ny=cur_y+self.rp[i][1]
        if (nx, ny) not in visited:
          if pgs[ny][nx]!="#" and hlp.ppack(nx, ny) not in pgdp:
            queue.append((nx, ny, ks+self.rt[i]))
            visited.append((nx, ny))
    return("")


  # ###########################################################
  # Bewegt die Box auf box_from nach box_to.
  # Liefert Status und (bei ==0) dem Bewegungsstring.
  #
  # Status:
  # 0 = gut
  # 1 = Start-Pos nicht Box (kommt nicht vor)
  # 2 = Ziel-Pos nicht frei
  # 4 = kein Weg zum Start
  # 5 = kein Weg von Start nach Ziel
  def findBestPushTrackTo(self, pgs, dof, pgdp, pp, box_from, box_to):
    bfp=hlp.ppack(box_from[0], box_from[1])
    btp=hlp.ppack(box_to[0],   box_to[1])

    if bfp not in pgdp:                               # wenn auf der StartPos box_from keine Box steht...
      return(1, "")                                   # ...dann kommen wir hier nicht weiter
    if pgs[box_to[1]][box_to[0]]=="#" or btp in pgdp: # wenn die ZielPos box_to nicht frei ist...
      return(2, "")                                   # ...dann kommen wir hier nicht weiter

    # Hier wird eine Kopie des statischen Spielfeldes erzeugt, in der alle Boxen ausser
    # der zu schiebenden Box box_from als Walls enthalten sind.
    pgst=[]
    for y in range(len(pgs)):
      ln=[]
      for x in range(len(pgs[y])):
        c=pgs[y][x]
        if hlp.ppack(x, y) in pgdp:
          if box_from!=(x, y):
            c="#"
        ln.append(c)
      pgst.append(ln)

    queue=deque([])
    visited={}
    for d in range(4):
      if pgst[pp[1]+self.my[d]][pp[0]+self.mx[d]]!="#":
        queue.append((bfp, pp, d, ""))    # (BoxPosPacked, PlayerPos, Schieberichtung, Bewegungsstring)
        visited.update({(bfp, pp, d):1})  # (BoxPosPacked, PlayerPos, Schieberichtung)

    pushed=False
    while queue:
      pgdp, pp, d, ks=queue.popleft()
      pgdpl=[pgdp]
      rc, ms, pp, bp, isdead=self.movePlayer(pgst, dof, pgdpl, pp, d)
      pgdp=pgdpl[0] # ggf. geänderte BoxPos holen

      if rc==2:
        pushed=True

      if btp==pgdp:       # wenn Box das Zielfeld erreicht hat...
        return(0, ks+ms)  # ...fertig

      if rc!=0:                                                 # wenn der movePlayer einen legalen Zug meldet...
        for d in range(4):                                      # ...alle vier möglichen Folgezüge...
          if (pgdp, pp, d) not in visited:                      # ...testen, ob sie schon probiert wurden...
            if pgst[pp[1]+self.my[d]][pp[0]+self.mx[d]]!="#":   # ...und legal sind...
              queue.append((pgdp, pp, d, ks+ms))                # ...wenn ja, dann zum weiteren Testen auf die Queue
              visited.update({(pgdp, pp, d):1})

    if pushed==False:
      return(4, "")
    return(5, "")


  # ###########################################################
  # Liefert True (==Spiel gelöst), wenn 
  #   alle Goal squares belegt sind
  #  ODER
  #   alle Boxen auf einem Goal square stehen
  def isSolved(self, pgs, pgdp, zfl):
    if len(zfl)>len(pgdp):          # es gibt mehr Goal squares als Boxen
      for i in pgdp:
        if hlp.punpack(i) not in zfl:
          return(False)
    else:           # es gibt mehr Boxen als Goal squares oder gleich viele
      for i in zfl:
        if hlp.ppackt(i) not in pgdp:
          return(False)
    return(True)

  # ###########################################################
  # Liefert True, wenn die Box an Position box_pos tot ist.
  # box_push_pos sind die Koordinaten des Feldes hinter der Box
  # in Schiebe-Richtung.
  def __isDead(self, pgs, pgdp, pp, box_pos, (hx, hy)):
    if pgs[box_pos[1]][box_pos[0]]=="_":  # wenn Box auf BadFloor steht...
      return(True)                        # ...dann ist sie tot

    if self.deadTest.isOnBorder(pgs, pgdp, box_pos)==True:
      return(True)

    if self.deadTest.patternMatch(pgs, pgdp, pp, box_pos)==True:
      return(True)

    (x, y)=box_pos
    if y==hy: # horizontale Bewegung
      tst_lst=[(hx, hy), (x, y-1), (x, y+1), (hx, y-1), (hx, y+1)]
    else:     # vertikale Bewegung
      tst_lst=[(hx, hy), (x-1, y), (x+1, y), (x-1, hy), (x+1, hy)]
    if self.deadTest.isDeadAreaNew(pgs, pgdp, pp, tst_lst)==True:
      return(True)

#    if self.deadTest.isDeadArea(pgs, pgdp, pp, hx, hy)==True:    return(True)
#    if y==hy: # horizontale Bewegung
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x, y-1) ==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x, y+1) ==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, hx, y-1)==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, hx, y+1)==True: return(True)
#    else:     # vertikale Bewegung
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x-1, y) ==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x+1, y) ==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x-1, hy)==True: return(True)
#      if self.deadTest.isDeadArea(pgs, pgdp, pp, x+1, hy)==True: return(True)

    return(False)


