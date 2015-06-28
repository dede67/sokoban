#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Helper as hlp

class SokoDeadTests():

  def __init__(self):
    # Objekt-Gruppen
    self.pm_pd={"W": ("#"),           \
                "b": ("$"),           \
                "B": ("$", "*"),      \
                "N": ("#", "$", "*"), \
                "F": (" "),           \
                "e": ("#", "$", "*", ".", " ", "@", "+", "i", "u")  }
    self.patternMemoKeys=[]
    self.patternMemo={}

    #                 L         R         U         D
    self.rtg     =[(-1,  0), ( 1,  0), ( 0, -1), ( 0,  1)]
    self.msk_box =[ 0x1FCF,    0x1FCF,    0x1F3F,    0x1F3F  ]

  # ###########################################################
  #
  def updateDegreeOfFreedom(self, dof, pgd):
    for y in range(len(dof)):
      for x in range(len(dof[y])):
        if dof[y][x]>=0x1000:     # wenn überquerbares Feld
          dof[y][x]&=0x1F0F                   # dynamischen DOF löschen
          dof[y][x]|=((dof[y][x]&0x000F)<<4)  # dynamischer DOF auf statischer DOF setzen
          for r in range(4):      # über die vier Nachbarfelder
            nx=x+self.rtg[r][0]
            ny=y+self.rtg[r][1]
            if hlp.ppack(nx, ny) in pgd:      # wenn auf dem Nachbarfeld eine Box steht
              dof[y][x]&=self.msk_box[r]

  # ###########################################################
  # Liefert True, wenn an einer horizontalen oder vertikalen
  # Wand mehr Boxen als Goal squares stehen.
  #
  #  z.B.:(0) #############  oder #############
  #           #     $     #       #  .  $  $  #
  #
  # oder: (1) #     $     #       #  .  $  $  #
  #           #############  oder #############
  #
  #         (2)    (3)
  # oder:   ##     ##
  #         #       #
  #         #$     $#
  #         #       #
  #         #$     $#
  #         #.     .#
  #         #       #
  #         ##     ##
  def isOnBorder(self, pgs, pgdp, (x, y)):
    rtgb=[(0, -1), (0, 1), (-1, 0), (1, 0)] # Rotation: Richtung zur Wall
    step=[(1, 0), (1, 0), (0, 1), (0, 1)]   # Rotation: Prüf-Richtung

    for m in range(4):  # vier Rotationen
      if pgs[y+rtgb[m][1]][x+rtgb[m][0]]!="#":
        continue  # Box nicht an entsprechender Wall

      sx=step[m][0]
      sy=step[m][1]
      goalcnt=0
      boxcnt=0
      if hlp.ppack(x, y) in pgdp and pgs[y][x]!=".":
        boxcnt=1 # bei Box auf GoalSquare kürzt es sich weg
      i=1
      o=pgs[y+sy*i][x+sx*i]
      while o!="#": # nach rechts bzw. unten
        if   o==".":                          goalcnt+=1  # GoalSquare
        if hlp.ppack(x+sx*i, y+sy*i) in pgdp: boxcnt+=1   # Box
        i+=1
        o=pgs[y+sy*i][x+sx*i]
      rp=i-1
      sx=-sx
      sy=-sy
      i=1
      o=pgs[y+sy*i][x+sx*i]
      while o!="#": # nach links bzw. oben
        if   o==".":                          goalcnt+=1  # GoalSquare
        if hlp.ppack(x+sx*i, y+sy*i) in pgdp: boxcnt+=1   # Box
        i+=1
        o=pgs[y+sy*i][x+sx*i]
      rm=i-1

      # auf durchgehende Wall prüfen
      sm=(x+rtgb[m][0])*step[m][0] + (y+rtgb[m][1])*step[m][1] - rm
      sp=sm+rm+rp
      for i in range(sm, sp+1):
        if step[m][0]==0:
          xw=x+rtgb[m][0]
          yw=i
        else:
          xw=i
          yw=y+rtgb[m][1]
        dc=False
        if pgs[yw][xw]!="#":
          dc=True # break + continue
          break
      if dc==True:
        continue
      if boxcnt>goalcnt:
        return(True)
    return(False)


  # ###########################################################
  # Liefert True, wenn die Box an Position (x, y) tot ist.
  def patternMatch(self, pgs, pgdp, pp, (x, y)):

    debug=False
    # [BB]
    # [BB]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNNN", (2, 2), 1, 0):
      if debug==True: print "NNNN"
      return(True)

    # [WBe]
    # [eBW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBeeBW", (3, 2), 2, 1):
      if debug==True: print "WBeeBW"
      return(True)

    #                       #  #    
    # [WBee]  #$      $#   $$  $$  
    # [eBBe]   $$    $$   $$    $$  
    # [eeBW]    $#  #$    #      #  
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBeeeBBeeeBW", (4, 3), 2, 1):
      if debug==True: print "WBeeeBBeeeBW"
      return(True)

    # [WBe]
    # [eBB]
    # [eeW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBeeBBeeW", (3, 3), 4, 1):
      if debug==True: print "WBeeBBeeW"
      return(True)

    # [BBe] ??    ??     ??  ??      ???  ???     ???  ???
    # [BFB] ? ?  ? ?    ? ?  ? ?     ? ?  ? ?     ? ?  ? ?
    # [WWW] ???  ???    ???  ???      ??  ??      ??    ??
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNeNFNNNN", (3, 3), 4, 0):
      if debug==True: print "NNeNFNNNN"
      return(True)

    # [e##]   ??   ??                       XX  ??      ???    ???   
    # [#FB]  ? ?   ? ?      ???    ???     ? X  ? ?     ?  ?  ?  ?    
    # [#FB]  ? ?   ? ?      X  X  X  X     ? X  ? ?      ???  ???     
    # [#Be]  ??     ??       ???  ???      ??    ??                   
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "eWWWFNWFNWNe", (3, 4), 2, 1):
      if debug==True: print "eWWWFNWFNWNe"
      return(True)

    # [BBe]   ??    ??                                
    # [BFB]   ? ?  ? ?                                
    # [eBB]    ??  ??                                
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNeNFNeNN", (3, 3), 2, 0):
      if debug==True: print "NNeNFNeNN"
      return(True)

    # [####]   ####
    # [BFFB]   $  $
    # [eBBe]    $$
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNNNNFFNeNNe", (4, 3), 4, 0):
      if debug==True: print "NNNNNFFNeNNe"
      return(True)

    # [##ee]   ##      ##      $#  #$                          
    # [#FBe]   # $    $ #     $ #  # $                          
    # [#FFB]   #  $  $  #    #  #  #  #                          
    # [####]   ####  ####    ####  ####                          
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNeeNFNeNFFNNNNN", (4, 4), 4, 0):
      if debug==True: print "NNeeNFNeNFFNNNNN"
      return(True)

    # [BBBe]  $$$
    # [BFBe]  $ $
    # [eBFB]   $ $
    # [e###]   ### 
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNNeNFNeeNFNeNNN", (4, 4), 4, 1):
      if debug==True: print "NNNeNFNeeNFNeNNN"
      return(True)


    # [BBBBe]   $$$$
    # [BFFFB]   $   $
    # [#####]   #####
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "NNNNeNFFFNNNNNN", (5, 3), 4, 1):
      if debug==True: print "NNNNeNFFFNNNNNN"
      return(True)

    # [eeBBe]     $$
    # [eBFBe]    $ $
    # [BFBFB]   $ $ $
    # [##B##]   $$$$$
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "eeNNeeNFNeNFNFNNNNNN", (5, 4), 4, 1):
      if debug==True: print "eeNNeeNFNeNFNFNNNNNN"
      return(True)

    # [WWWW]
    # [BFFW]
    # [eBFW]
    # [eBFW]
    # [WWWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WWWWBFFWeBFWeBFWWWWW", (4, 5), 4, 1):
      if debug==True: print "WWWWBFFWeBFWeBFWWWWW"
      return(True)

    # [WWWW]
    # [eBFW]
    # [BFFW]
    # [eBFW]
    # [WWWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WWWWeBFWBFFWeBFWWWWW", (4, 5), 4, 1):
      if debug==True: print "WWWWeBFWBFFWeBFWWWWW"
      return(True)


    # [eBW]
    # [WFW]
    # [eBW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "eBWWFWeBW", (3, 3), 4, 0):
      return(True)

    # [WeW]
    # [BBW]
    # [eBW]
    # [WWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WeWBBWeBWWWW", (3, 4), 4, 1):
      return(True)

    return(False)

# temp
    # [WBeee] WBeeeWFBBWWFFFWWWWWW
    # [WFBBW]
    # [WFFFW]
    # [WWWWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBeeeWFBBWWFFFWWWWWW", (5, 4), 4, 1):
      return(True)

    # [WBBBe] WBBBeWFFBWWFFFWWWWWW
    # [WFFBW]
    # [WFFFW]
    # [WWWWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBBBeWFFBWWFFFWWWWWW", (5, 4), 4, 1):
      return(True)

    # [WBBeBFW]   WBBeBFWWFFBWWWWFFFWeeWWWWWee
    # [WFFBWWW]
    # [WFFFWee]
    # [WWWWWee]
#    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBBeBFWWFFBWWWWFFFWeeWWWWWee", (7, 4), 4, 1):
#      return(True)

    # [WBBBBFW]   WBBBBFWWeeeWWWWFFFWeeWWWWWee
    # [WeeeWWW]
    # [WFFFWee]
    # [WWWWWee]
#    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBBBBFWWeeeWWWWFFFWeeWWWWWee", (7, 4), 4, 1):
#      return(True)

    # [WBBBe] WBBBeWeBeWWFFFWWWWWW
    # [WeBeW]
    # [WFFFW]
    # [WWWWW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WBBBeWeBeWWFFFWWWWWW", (5, 4), 4, 1):
      return(True)

    # [WWWW]  WWWWWFFBWFBeWFBeWWee
    # [WFFB]
    # [WFBe]
    # [WFBe]
    # [WWee]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WWWWWFFBWFBeWFBeWWee", (4, 5), 4, 1):
      return(True)


    # [WWWWe] WWWWeWFFWWeBeFWeeBBW
    # [WFFWW]
    # [eBeFW]
    # [eeBBW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WWWWeWFFWWeBeFWeeBBW", (5, 4), 4, 1):
      return(True)

    # [WWWWe] WWWWeWFFWWBeeFWBBBBW
    # [WFFWW]
    # [BeeFW]
    # [BBBBW]
    if self.__PatternMatch(pgs, pgdp, pp, x, y, "WWWWeWFFWWBeeFWBBBBW", (5, 4), 4, 1):
      return(True)

    return(False)


  # ###########################################################
  # Mappt jede Box im Pattern auf (ox, oy) und prüft, ob alle
  # anderen Objekte im Pattern zu den Spielfeld-Objekten 
  # relativ zu (ox, oy) passen. Das Pattern kann bis zu 4x
  # rotiert werden und nach jeder Rotation gespiegelt werden.
  def __PatternMatch(self, pgs, pgdp, pp, ox, oy, pattern, (pw, ph), rotate=1, mirror=0):
    # Memoisierung der rotierten/gespiegelten Pattern
    if pattern not in self.patternMemoKeys:
      self.patternMemoKeys.append(pattern)
      for rl in range(rotate):
        if rl==0:
          pr=pattern
          pwn=pw
          phn=ph
        else:
          pr=self.__RotatePattern(pr, (pwn, phn))
          tmp=pwn
          pwn=phn
          phn=tmp
        for ml in range(mirror+1):
          if ml==0:
            prm=pr
          else:
            prm=self.__MirrorPattern(pr, (pwn, phn))

          if self.IsValueAlreadyInDict((0, prm, pwn, phn))==True:
            # unnötige Rotationen/Spiegelungen ausblenden
            self.patternMemo.update({(pattern, rl, ml):(1, prm, pwn, phn)})
          else:
            self.patternMemo.update({(pattern, rl, ml):(0, prm, pwn, phn)})

    for rl in range(rotate):
      for ml in range(mirror+1):
        ign, prm, pwn, phn=self.patternMemo[(pattern, rl, ml)]
        if ign==True:
          continue
        if self.__PatternMatch2Sub1(pgs, pgdp, pp, ox, oy, prm, (pwn, phn))==True:
          return(True)  # beim ersten Treffer Match==True melden
    return(False)


  # ###########################################################
  # Liefert True, wenn "value" schon als Key in
  # self.patternMemo vorhanden ist.
  def IsValueAlreadyInDict(self, value):
    for v in self.patternMemo.values():
      if v==value:
        return(True)
    return(False)


  # ###########################################################
  # Rotiert das Pattern gegen den Uhrzeigersinn.
  def __RotatePattern(self, pattern, (pw, ph)):
    p=""
    for x in range(pw-1, -1, -1): # pw==3 -> 2, 1, 0
      for y in range(ph):         # ph==3 -> 0, 1, 2
        p+=pattern[y*pw+x]
    return(p)


  # ###########################################################
  # Spiegelt das Pattern in der waagerechten.
  def __MirrorPattern(self, pattern, (pw, ph)):
    p=""
    for y in range(ph):
      for x in range(pw):
        p+=pattern[y*pw+pw-x-1]
    return(p)


  # ###########################################################
  # Ruft für alle Boxen im Pattern __PatternMatch2Sub() auf.
  def __PatternMatch2Sub1(self, pgs, pgdp, pp, ox, oy, pattern, (pw, ph)):
    for y in range(ph):
      for x in range(pw):   # über alle Boxen im Pattern
        idx=y*pw+x
        pc=pattern[idx]
        if pc in ("b", "B", "N"):
          rc=self.__PatternMatch2Sub2(pgs, pgdp, pp, ox, oy, pattern, (pw, ph), (x, y))
          if rc==True:    # sobald das gesamte Pattern passt...
            return(True)  # ...Match==True melden
    return(False)


  # ###########################################################
  # Prüft das Pattern gegen das Spielfeld, wobei das
  # Spielfeld-Objekt auf (ox, oy) auf die Box auf (pxy, pyr)
  # im Pattern gemappt wird.
  # Wenn alle Objekte im Spielfeld auf das Pattern passen und
  # mindestens eine Box nicht auf Goal square steht, wird True
  # geliefert.
  def __PatternMatch2Sub2(self, pgs, pgdp, pp, ox, oy, pattern, (pw, ph), (pxr, pyr)):
    bnogs=False
    for y in range(ph):
      for x in range(pw):
        idx=y*pw+x
        pc=pattern[idx:idx+1] # aktuelles Character im Pattern
        o=self.GetObj(pgs, pgdp, pp, ox-pxr+x, oy-pyr+y)
        if o=="$":              # wenn Box nicht auf Goal square steht...
          if pc in ("b", "B", "N"):  # ...und Box gefordert war...
            bnogs=True          # ...merken
        if o not in self.pm_pd[pc]: # sobald erstes Character nicht passt...
          return(False)             # ...Match==False melden
    # bnogs==True, wenn mindestens eine Box nicht auf Goal square stand.
    # bnogs==False, wenn alle Boxen auf Goal squares standen (obwohl das Pattern ansonsten passte).
    return(bnogs)


  # ###########################################################
  # Liefert das Objekt an der Position (x, y).
  def GetObj(self, pgs, pgdp, pp, x, y):
    if   y>=len(pgs)    or y<0:  rc="u" # ausserhalb des Spielfeldes ist alles Wall
    elif x>=len(pgs[0]) or x<0:  rc="u" # nicht alle Zeilen müssen die volle Länge haben
    else:                        rc=pgs[y][x]

    if rc=="_":
      rc=" "

    if (x, y)==pp:                # wenn der Player auf dieser Position steht...
      if rc==".":   rc="+"        # ...wenn es ein Goal square ist, liefere Player on Goal square
      else:         rc="@"        # ...wenn es Floor ist, liefere Player
    elif hlp.ppack(x, y) in pgdp: # wenn an der Position etwas dynamisches steht...
      if   rc==".": rc="*"        # ...wenn es ein Goal square ist, liefere Box on Goal square
      elif rc==" ": rc="$"        # ...wenn es Floor ist, liefere Box
    return(rc)


  # ###########################################################
  # Liefert True, wenn einer der Floors aus pos_lst zu einem
  # Floor-Bereich gehört, der komplett aus badFloors besteht
  # und vollständig von Boxen vom restlichen Spielfeld
  # abgetrennt wird, die Boxen nicht alle auf Goal squares
  # stehen und keine Box einen Freiheitsgrad hat, der anzeigt,
  # dass sie vom Floor-Bereich weggeschoben werden könnte.
  def isDeadAreaNew(self, pgs, pgdp, pp, pos_lst):
    while pos_lst!=[]:
      x, y=pos_lst.pop(0)
      fList, bList=self.findJointFloor(pgs, pgdp, pp, x, y)
      if fList==None or fList==[]:
        continue # der gefundene Floor-Bereich passt nicht -> dieser Test geht nicht

      for i in pos_lst:     # zu testende Felder, die in
        if i in fList:      # der Ergebisliste enthalten sind,
          pos_lst.remove(i) # brauchen nicht mehr getestet werden

      cfl=True
      for i in fList:
        if pgs[i[1]][i[0]]!="_":
          cfl=False
          break # der Floor-Bereich besteht nicht komplett aus badFloors -> unsicher
      if cfl==False:
        continue

      # der Floor-Bereich in fList besteht nur aus badFloors
      abogs=True
      for i in bList:
        if pgs[i[1]][i[0]]!=".":
          abogs=False
          break
      if abogs==True:
        continue # alle angrenzenden Boxen stehen auf Goal squares

      aid=True
      for i in bList:   # über alle am Floor-Bereich angrenzenden Boxen
        dof=self.__degreeOfFreedomSubLocal(pgs, pgdp, pp, i[0], i[1], fList)
        if (dof&0x0f)==0x0f or (dof&0xf0)==0xf0:
          aid=False
          break
      if aid==True:
        return(True)
    return(False)

  # ###########################################################
  # Alte Version von isDeadAreaNew()
  # Brauchte 5 Aufrufe und somit auch 5 Aufrufe
  # von findJointFloor()
  def isDeadArea(self, pgs, pgdp, pp, x, y):
    fList, bList=self.findJointFloor(pgs, pgdp, pp, x, y)
    if fList==None or fList==[]:
      return(False) # der gefundene Floor-Bereich passt nicht -> dieser Test geht nicht

    for i in fList:
      if pgs[i[1]][i[0]]!="_":
        return(False) # der Floor-Bereich besteht nicht komplett aus badFloors -> unsicher

    # der Floor-Bereich in fList besteht nur aus badFloors
    abogs=True
    for i in bList:
      if pgs[i[1]][i[0]]!=".":
        abogs=False
        break
    if abogs==True:
      return(False) # alle angrenzenden Boxen stehen auf Goal squares

    for i in bList:   # über alle am Floor-Bereich angrenzenden Boxen
      dof=self.__degreeOfFreedomSubLocal(pgs, pgdp, pp, i[0], i[1], fList)
      if (dof&0x0f)==0x0f or (dof&0xf0)==0xf0:
        return(False)
    return(True)


  # ###########################################################
  # Liefert die Positionen von allen Floors, die direkt von
  # dem Floor aus erreichbar sind, dessen Koordinaten x,y
  # übergeben wurden.
  # Weiterhin wird eine Liste aller Positionen der Boxen
  # geliefert, die direkt am Floor-Bereich liegen.
  # Wurde der Player oder ein Goal square innerhalb des 
  # zusammenhängenden Floor-Bereiches gefunden, wird eine
  # leere Liste geliefert.
  #
  # Es werden rekursiv folgende Positionen geprüft.
  #          0,-1
  #  -1, 0  (x, y)  1, 1
  #          0, 1
  #
  def findJointFloor(self, pgs, pgdp, pp, x, y):
    return(self.__findJointFloor(pgs, pgdp, pp, x, y, [], []))
  def __findJointFloor(self, pgs, pgdp, pp, x, y, fList, bList):
    if fList==None:          # wenn Abbruch-Kennung...
      return((fList, bList)) # ...Abbruch-Kennung an rekursiven Aufstieg weitergeben
    o=self.GetObj(pgs, pgdp, pp, x, y)
    if o in ("@", "+", "."): # wenn Player [on Goal square] oder Goal square...
      return((None, None))   # ...Abbruch
    if o in ("#", "u", "i"): # wenn Wall...
      return((fList, bList)) # ...Fertig
    if o in ("$", "*"):      # wenn Box [on Goal square]...
      if (x, y) not in bList:
        bList.append((x, y)) # ...in bList merken...
      return((fList, bList)) # ...und Fertig
    if (x, y) in fList:      # wenn Feld schon verarbeitet wurde...
      return((fList, bList)) # ...Fertig

    # hier ist (x, y) entweder Floor oder Goal square
    fList.append((x, y))
    fList, bList=self.__findJointFloor(pgs, pgdp, pp, x  , y-1, fList, bList)
    fList, bList=self.__findJointFloor(pgs, pgdp, pp, x-1, y  , fList, bList)
    fList, bList=self.__findJointFloor(pgs, pgdp, pp, x+1, y  , fList, bList)
    fList, bList=self.__findJointFloor(pgs, pgdp, pp, x  , y+1, fList, bList)
    return((fList, bList))


  # ###########################################################
  # Liefert den einfachen Freiheitsgrad der Box an den
  # Koordinaten x, y.
  # Der einfache Freiheitsgrad beachtet lediglich das
  # Vorhandensein von Hindernissen und setzt die Freiheits-Bits
  # folgendermassen:
  #      01           00 - Wall (sicher)
  #   67 XX 45        01 - Box  (offen)
  #      23           11 - frei (sicher)
  #
  # _0 0000  oben und unten an Wall         vertikal tot
  # _1 0001  oben an Box, unten an Wall     vertikal tot
  # _3 0011  oben frei, unten an Wall       vertikal tot
  # _4 0100  oben an Wall, unten an Box     vertikal tot
  # _5 0101  oben und unten an Box          offen
  # _7 0111  oben frei, unten an Box        offen
  # _C 1100  oben an Wall, unten frei       vertikal tot
  # _D 1101  oben an Box, unten frei        offen
  # _F 1111  oben und unten frei            vertikal frei
  #
  # 0_ 0000  rechts und links an Wall       horizontal tot
  # 1_ 0001  rechts an Box, links an Wall   horizontal tot
  # 3_ 0011  rechts frei, links an Wall     horizontal tot
  # 4_ 0100  rechts an Wall, links an Box   horizontal tot
  # 5_ 0101  rechts und links an Box        offen
  # 7_ 0111  rechts frei, links an Box      offen
  # C_ 1100  rechts an Wall, links frei     horizontal tot
  # D_ 1101  rechts an Box, unten frei      offen
  # F_ 1111  rechts und links frei          horizontal frei
  def __degreeOfFreedomSubLocal(self, pgs, pgdp, pp, x, y, badFloorsList=[]):
    r=0
    r+= self.__objBorderFreedom(pgs, pgdp, pp, x,   y-1, badFloorsList)
    r+=(self.__objBorderFreedom(pgs, pgdp, pp, x,   y+1, badFloorsList)<<2)
    r+=(self.__objBorderFreedom(pgs, pgdp, pp, x+1, y,   badFloorsList)<<4)
    r+=(self.__objBorderFreedom(pgs, pgdp, pp, x-1, y,   badFloorsList)<<6)
    return(r)


  # ###########################################################
  # Liefert den einfachen Freiheitsgrad einer Koordinate x, y.
  # Wird "badFloorsList" mit !=[] übergeben, werden badFloors
  # wie Walls gewertet.
  def __objBorderFreedom(self, pgs, pgdp, pp, x, y, badFloorsList):
    obj=self.GetObj(pgs, pgdp, pp, x, y)
    if   obj in ("$", "*"):
      r=0x01
    elif obj in (".", " ", "@", "+"):
      if badFloorsList!=[] and obj==" " and (x, y) in badFloorsList:
        r=0x00
      else:
        r=0x03
    else:
      r=0x00
    return(r)

