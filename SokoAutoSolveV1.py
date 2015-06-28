#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time

import Helper as hlp
import SokoMove


class SokoAutoSolveV1():

  def __init__(self):
    self.gnas={}            # Dict mit Relation "Spielfeld zu Bewegungs-String-Länge"
                            # "gnas" wird verwendet, um Effekt-lose Züge zu erkennen.
                            # Ergibt ein Bewegungs-String ein Spielfeld, das auch schon durch einen
                            # kürzeren Bewegungs-String entstanden ist, kann der längere
                            # Bewegungs-String ignoriert werden.
    self.gnas_inv=[{}, {}]  # Dict mit Relation "Bewegungs-String zu Spielfeld"
                            # "gnas_inv" wird verwendet, um einen Bewegungs-String schnell wieder
                            # in das zugehörige Spielfeld umsetzten zu können (ohne es neu
                            # durchspielen zu müssen). Es werden zwei Dicts verwendet, zwischen
                            # denen umgeschaltet wird - weil ja immer nur die um einen Zug
                            # kürzeren Spielfelder benötigt werden.
    self.sm=SokoMove.SokoMove()
    self.td={"l":0, "r":1, "u":2, "d":3, "L":0, "R":1, "U":2, "D":3}

  # ###########################################################
  # Stellt das zu lösende Spielfeld ein.
  def setData(self, pg_stat, pg_dof, pg_dynp, playerpos, zfl):
    self.pg_stat=pg_stat
    self.pg_dof=pg_dof
    self.pg_dynp=pg_dynp
    self.playerpos=playerpos
    self.pg_zfl=zfl


  # ###########################################################
  # Teil dem laufenden Thread den Abbruch-Wunsch mit.
  def cancelSolver(self):
    self.autosolveActive=False


  # ###########################################################
  # Startet den Solver-Thread.
  def startSolver(self):
    self.worker=threading.Thread(target=self.__runAsThread, name="SokoSolver")
    self.worker.setDaemon(True)

    self.autosolveActive=True
    self.solution=""
    self.isRunning=True
    self.count=0
    self.killed=0
    self.keyLength=0
    self.numberOfTestsDone=0
    self.numberOfGamesToTest=0
    self.dictLen=0
    self.playerpos_ss=self.playerpos
    self.pg_dynp_ss=hlp.copyList(self.pg_dynp)

    self.worker.start()


  # ###########################################################
  # Liefert Status-Informationen an die aufrufende Funktion.
  def getStatus(self):
    return( self.isRunning, \
            self.solution, \
            self.keyLength, \
            self.numberOfTestsDone, \
            self.numberOfGamesToTest, \
            self.dictLen, \
            self.count, \
            self.killed, \
            self.playerpos_ss, \
            self.pg_dynp_ss)


  # ###########################################################
  # Findet den Bewegungs-String zum aktuellen Spiel, indem alle
  # möglichen Bewegungs-Strings erzeugt und durchgespielt
  # werden. Bewegungs-Strings, die in einer Tot-Stellung enden,
  # werden gelöscht und nicht weiter verlängert. Auch werden
  # Effekt-lose Zug-Folgen erkannt und gelöscht.
  def __runAsThread(self):
    sl=[[""], []]
    i=0
    self.gnas_inv[i].update({"":self.hashable(self.playerpos, self.pg_dynp)})

    for s in range(1000): # alle Spiele mit bis zu 1000 Zügen testen
      self.keyLength=s

      # jede der alten Zugfolgen, die nicht zum Löschen vorgemerkt wurden, um
      # die vier möglichen Bewegungen verlängern.
      for a in range(len(sl[i])): # über alle bisherigen Bewegungs-Strings
        o=sl[i][a]  # aktuelle Zugfolge holen
        if o!="-":  # wenn Zugfolge nicht zum Löschen vorgemerkt...
          for m in ["l", "r", "u", "d"]:  # ...einen weiteren Zug anhängen
            sl[i^1].append(o+m)           # ...und in neuer Liste ablegen

      sl[i]=[]  # die alte Liste wird nun nicht mehr benötigt
      i^=1      # Liste für die neuen Bewegungs-Strings togglen
      self.gnas_inv[i].clear()

      self.numberOfGamesToTest=len(sl[i])
      self.dictLen=len(self.gnas)

      # Alle Bewegungs-Strings in sl[j] durchspielen.
      sol=self.autoSolveProcessMoveList(sl[i], i)   # in i^1 ist die gnas_inv mit den "alten" Daten

      if sol>-1:  # wenn sl[i] eine Lösung enthält...
        self.solution=sl[i][sol]
        self.pg_dynp_ss=hlp.copyList(self.pg_dynp)
        self.playerpos_ss=self.playerpos
        
        self.isRunning=False
        return

      if self.autosolveActive==False: # wenn von Extern ein Abbruch angemeldet wurde...
        break                         # ...abbrechen
    self.isRunning=False


  # ###########################################################
  # Spielt alle Lösungs-Strings in "lst". War ein Lösungs-
  # String illegal, wird er aus "lst" gelöscht.
  # War kein String in "lst" eine Lösung, wird -1 geliefert.
  # Ansonsten wird der Index der ersten Lösung geliefert.
  def autoSolveProcessMoveList(self, lst, gnas_inv_idx):
    t=time.clock()
    i=0
    lenlst=len(lst)

    for i in range(lenlst):   # über alle Lösungs-Strings...
      rc, keyseq=self.autoSolveProcessOneMoveString(lst[i], gnas_inv_idx)  # ...spiele aktuellen Lösungs-String

      if self.autosolveActive==False:   # wenn von Extern ein Abbruch angemeldet wurde...
        return(-1)                      # ...abbrechen

      if (i%1000)==0:                       # alle 1000 Durchläufe...
        self.numberOfGamesToTest=len(lst)   # ...Fortschritts-Infos ablegen
        self.numberOfTestsDone=i
        self.dictLen=len(self.gnas)

      self.count+=1
      lst[i]=keyseq
      if rc==0:         # wenn es einen illegalen oder unsinnigen Zug enthält...
        self.killed+=1
        lst[i]="-"      # ...String zum Löschen vormerken.
      elif rc==1:       # wenn es ein legaler Zug war, der noch nicht die Lösung ist...
        if (t+0.25)<time.clock():                     # ...dann jede 1/4 Sekunde...
          self.pg_dynp_ss=hlp.copyList(self.pg_dynp) # aktuelle Spielfeld merken
          self.playerpos_ss=self.playerpos
          t=time.clock()
      elif rc==2:       # wenn es eine Lösung war...
        return(i)       # ...Index in "lst" zurückliefern.
    return(-1)


  # ###########################################################
  # Liefert einen String zu pp und pgdp.
  def hashable(self, pp, pgdp):
    s=""
    s+=chr(pp[0])+chr(pp[1])
    for i in sorted(pgdp):
      s+=chr(i&0xFF)+chr(i>>8)
    return(s)


  # ###########################################################
  # Liefert pp und pgdp zu einem String.
  def unhash(self, h):
    pp=(ord(h[0]), ord(h[1]))
    pgdp=[]
    for i in range(2, len(h), 2):
      pgdp.append(ord(h[i])+(ord(h[i+1])<<8))
    return(pp, pgdp)


  # ###########################################################
  # Eine Bewegungs-Folge (in "keyseq") durchspielen.
  # Liefert ein Tupel aus Status und ggf. geänderter "keyseq".
  # Status==0, wenn letzter Zug illegal war.
  # Status==1, wenn letzter Zug eine legale Bewegung war.
  # Status==2, wenn das Spiel gelöst ist.
  def autoSolveProcessOneMoveString(self, keyseq, gnas_inv_idx):
      keyseqlen=len(keyseq)
      # Playground zum Bewegungs-String (ohne letzten Zug) holen
      opg=self.gnas_inv[gnas_inv_idx^1].get(keyseq[0:keyseqlen-1], "")

      if opg=="": # wenn nicht gefunden....ist was falsch....
        print "not in gnas_inv[", gnas_inv_idx^1, "]:", keyseq[0:keyseqlen-1]
        print "len(gnas_inv[...])=", len(self.gnas_inv[gnas_inv_idx^1])
        return((0, keyseq))
      self.playerpos, self.pg_dynp=self.unhash(opg) # ...Playground rekonstruieren

      # ...und letzten Zug (mit Dead-Checks) anhängen
      i=keyseq[keyseqlen-1]
      rc, ms, self.playerpos, bp, isdead=self.sm.movePlayer(self.pg_stat, self.pg_dof, self.pg_dynp, self.playerpos, self.td[i])
      # rc: 0=keine Bewegung, 1=nur Spieler bewegt, 2=Spieler+Box bewegt

      if rc==0:   # letzter Zug war illegal (z.B. gegen eine Wall oder zwei Boxen)
        # ...also killen
        return((0, keyseq))

      gnas=self.hashable(self.playerpos, self.pg_dynp)
      tst=self.gnas.get(gnas, 0)
      if tst>0:
        # genau dieses Spielfeld wurde auch schon mit weniger Zügen erreicht
        # ...also killen
        return((0, keyseq))

      if   rc==1: # letzter Zug war eine nur-Spieler-Bewegung
        self.gnas.update({gnas:keyseqlen})                # ...Zug merken...
        self.gnas_inv[gnas_inv_idx].update({keyseq:gnas}) # ...Spiel merken...
        return((1, keyseq))                               # ...und zurück
      
      # letzter Zug war eine Box-Bewegung
      if isdead==True:  # lokale Stellung ist tot
        # ...dann killen
        return((0, keyseq))

      if self.sm.isSolved(self.pg_stat, self.pg_dynp, self.pg_zfl)==True: # wenn das Spiel gelöst ist...
        # ...dann Fertigmeldung liefern
        return((2, keyseq))

      # der aktuelle Spielstand ist weder gelöst noch tot
      # also Spiel merken
      self.gnas.update({gnas:keyseqlen})
      self.gnas_inv[gnas_inv_idx].update({keyseq:gnas})
      return((1, keyseq))

