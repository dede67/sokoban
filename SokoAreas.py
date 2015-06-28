#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque

import Helper as hlp



class SokoAreas():

  def __init__(self):
    self.rp=[(0, -1), (0, 1), (-1, 0), (1, 0)]   # relative Spieler-Koordinaten um die Box (hoch, runter, links, rechts)

  # ###########################################################
  #
  def findAreas(self, pgs, pgdp):
    floorsList=[[]]
    boxesList=[[]]
    for y in range(len(pgs)):
      for x in range(len(pgs[y])):
        if pgs[y][x] in (" ", "_", ".") and hlp.ppack(x, y) not in pgdp:
          floorFound=False
          for l in floorsList:
            if hlp.ppack(x, y) in l:
              floorFound=True
              break
          if floorFound==False:
            floors, boxes=self.__findReachableBoxes(pgs, pgdp, (x, y))
            floorsList.append(floors)
            boxesList.append(boxes)

    for l in floorsList:
      o=[]
      for i in l:
        o.append(hlp.punpack(i))
      print sorted(o)

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


