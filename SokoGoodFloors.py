#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque
import SokoMove
import Helper as hlp

class SokoGoodFloors():
# Interface:
#   findGoodFloors()  -> good-floor-List  

  def __init__(self, pgs, pgdp, zfl, pp):
    self.pgs=pgs
    self.pgdp=pgdp
    self.zfl=zfl
    self.pp=pp
    self.bf=[]
    self.sm=SokoMove.SokoMove()
    
    self.pppi=[(-1,  0), ( 1,  0), ( 0, -1), ( 0,  1)]  # Player-Pull-Pos
    self.pdpi=[(-2,  0), ( 2,  0), ( 0, -2), ( 0,  2)]  # Player-Desination-Pos
    self.hrms=["L", "R", "U", "D"]


  # ###########################################################
  # Liefert eine gepackte Liste der möglichen Pulls an der
  # Box auf (x, y) ohne Berücksichtigung der Spielfigur-Position.
  def __pullableBordersForSingleBox(self, x, y):
    pbl=[]
    for i in range(4):
      if self.pgs[y+self.pppi[i][1]][x+self.pppi[i][0]]!="#":
        # das Feld, von dem der Player ziehen soll, ist frei
        if self.pgs[y+self.pdpi[i][1]][x+self.pdpi[i][0]]!="#":
          # das Feld, auf dem der Player landen soll, ist frei
          pbl.append(hlp.mpack((x+self.pppi[i][0], y+self.pppi[i][1]), i))
    return(pbl)


  # ###########################################################
  # Liefert True, wenn es einen Weg von pp nach dp gibt.
  # Es darf sich nur eine Box an den Koordinaten bp im
  # Spielfeld befinden. Der Inhalt des dynamischen Spielfeldes
  # in self.pgdp wird nicht berücksichtigt!  
  def __testPlayerWayToPos(self, pp, dp, bp):
    rc=self.__testPlayerWayToPosSubQueue(pp, dp, bp)
    return(rc!=None)


  # ###########################################################
  # Liefert in einem Spielfeld mit nur einer Box (auf bp) eine
  # Bewegungsfolge für den Weg von pp nach dp. Wird kein Weg
  # gefunden, wird "" geliefert.
  def __testPlayerWayToPosSubQueue(self, pp, dp, bp):
    queue=deque([(pp, "")])
    visited=[pp]
    while queue:
      ((x, y), rc)=queue.popleft()
      if (x, y)==dp:
        return(rc)
      for i in range(4):
        nx=x+self.pppi[i][0]
        ny=y+self.pppi[i][1]
        if (nx, ny) not in visited:
          if self.pgs[ny][nx]!="#" and (nx, ny)!=bp:
            queue.append(((nx, ny), rc+self.hrms[i]))
            visited.append((nx, ny))
    return(None)


  # ###########################################################
  # wie __testPlayerWayToPosSubQueue - taugt hier aber nix.
  # wird nicht genutzt!
  def __testPlayerWayToPosSubStack(self, rc, pp, dp, visited):
    if rc==True:
      return(True, visited)
    if pp==dp:
      return(True, visited)
    if self.pgs[pp[1]][pp[0]]=="#":
      return(False, visited)
    if pp in visited:
      return(False, visited)

    visited.append(pp)
    rc, visited=self.__testPlayerWayToPosSub(rc, (pp[0]-1, pp[1]), dp, visited)
    rc, visited=self.__testPlayerWayToPosSub(rc, (pp[0]+1, pp[1]), dp, visited)
    rc, visited=self.__testPlayerWayToPosSub(rc, (pp[0], pp[1]-1), dp, visited)
    rc, visited=self.__testPlayerWayToPosSub(rc, (pp[0], pp[1]+1), dp, visited)
    return(False, visited)


  # ###########################################################
  # Liefert eine Liste aller Floors, auf der eine Box stehen
  # kann, die von einem GoalSquare gezogen wurde.
  def findGoodFloors(self):
    good_floors=[]
    for gsx, gsy in self.zfl:     # für jedes Zielfeld...
      pgdpt=[hlp.ppack(gsx, gsy)] # ...eine Box drauf setzen
      rlst=self.__pullableBordersForSingleBox(gsx, gsy) # mögliche inverse Züge bestimmen
      # rlst kann 0 bis 4 Elemente enthalten
      for p in rlst:
        pgdpt=[hlp.ppack(gsx, gsy)] # neu setzen, weil pgdpt von __findGoodFloorsForSingleBox geändert wird
        good_floors=self.__findGoodFloorsForSingleBox(pgdpt, p, self.pp, good_floors)

    rc=[]
    for i in good_floors:     # aus der Liste mit Pulls eine Liste von Floors machen
      (dp, d)=hlp.munpack(i)
      if dp not in rc:
        rc.append(dp)
    return(rc)


  # ###########################################################
  # Durchläuft rekursiv alle möglichen Box-Positionen, die
  # durch Ziehen von einem GoalSquare erreicht werden können.
  # Mit good_floors wird eine Liste geführt, in der Box-Positionen
  # (und NICHT -wie sonst üblich- Player-Positionen) zusammen mit
  # einer Pull-Richtung stehen. Somit können Floors mehrfach (bis
  # zu viermal) besucht werden - mit je einer anderen Pull-Richtung.
  #
  # Verlängert ggf. good_floors und ändert pgdp.
  def __findGoodFloorsForSingleBox(self, pgdp, pull, pp, good_floors):
    bp=hlp.punpack(pgdp[0])   # derzeitige Box-Position(ungepackt) - ist ja nur eine drin
    dp, d=hlp.munpack(pull)   # Box-Ziel-Position (ungepackt)

    if hlp.mpack(bp, d) in good_floors: # wenn Pull schon ausgeführt wurde...
      return(good_floors)               # ...langt das

    if self.__testPlayerWayToPos(pp, dp, bp)==True: # wenn der Player die Pull-Position erreichen kann...
      pp=dp                                         # ...dann kann die Player-Pos auf Pull-Pos gesetzt werden
      good_floors.append(hlp.mpack(bp, d))          # ...und der Pull als gut und ausgeführt vermerkt werden

      rc, pp=self.sm.inverseMovePlayer(self.pgs, pgdp, pp, d) # Zug gemäß "pull" ausführen
      bp=hlp.punpack(pgdp[0])                                 # ggf. geänderte Box-Position holen
      rlst=self.__pullableBordersForSingleBox(bp[0], bp[1])   # mögliche Folge-Pulls ermitteln

      for p in rlst:          # über alle Folge-Pulls
        pgdpt=[pgdp[0]]       # neu setzen, weil pgdpt von __findGoodFloorsForSingleBox geändert wird
        good_floors=self.__findGoodFloorsForSingleBox(pgdpt, p, pp, good_floors)
    return(good_floors)

