#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import Helper as hlp


class Display():
  def __init__(self, col_dict):
    self.col_dict=col_dict
    self.dspc=DisplayCache()

  # ###########################################################
  # Lädt Änderungen an den Farbeinstellungen in die Klasse.
  def re_init(self, col_dict):
    self.col_dict=col_dict

  # ###########################################################
  # Für den Editor: die auswählbaren Objekte darstellen.
  def editorShowSelectableObjects(self, dc, clearDC):
    self.dc=dc
    self.__resize((7, 1)) # sieben Objekte in einer Zeile

    self.dc.SetBackground(wx.Brush(self.col_dict["col_bg"]))
    if clearDC==True:
      self.dspc.clearCache()
      self.dc.Clear()

    self.cachedShowObject(" ", " ", 0, 0)
    self.cachedShowObject(".", " ", 1, 0)
    self.cachedShowObject(" ", "$", 2, 0)
    self.cachedShowObject("#", " ", 3, 0)
    self.cachedShowObject(" ", "@", 4, 0)
    self.cachedShowObject(".", "$", 5, 0)
    self.cachedShowObject(".", "@", 6, 0)
    # " ", ".", "$", "#", "@", "*", "+"


  # ###########################################################
  # Für den Editor: das eine ausgewählte Objekt darstellen.
  def editorShowSelectedObject(self, dc, clearDC, obj):
    self.dc=dc
    self.__resize((1, 1)) # ein einzelnes Objekt

    self.dc.SetBackground(wx.Brush(self.col_dict["col_bg"]))
    if clearDC==True:
      self.dspc.clearCache()
      self.dc.Clear()

    if   obj==" ":  self.cachedShowObject(" ", " ", 0, 0)
    elif obj=="@":  self.cachedShowObject(" ", "@", 0, 0)
    elif obj==".":  self.cachedShowObject(".", " ", 0, 0)
    elif obj=="$":  self.cachedShowObject(" ", "$", 0, 0)
    elif obj=="#":  self.cachedShowObject("#", " ", 0, 0)
    elif obj=="*":  self.cachedShowObject(".", "$", 0, 0)
    elif obj=="+":  self.cachedShowObject(".", "@", 0, 0)


  # ###########################################################
  # Für den Editor: das Spielfeld darstellen.
  def editorShowPlayground(self, dc, clearDC, playground, size):
    self.dc=dc
    self.__resize(size)

    self.dc.SetBackground(wx.Brush(self.col_dict["col_bg"]))
    if clearDC==True:
      self.dspc.clearCache()
      self.dc.Clear()

    for y in range(size[1]):
      for x in range(size[0]):
        obj=playground[y][x]
        if   obj==" ":  self.cachedShowObject(" ", " ", x, y)
        elif obj=="@":  self.cachedShowObject(" ", "@", x, y)
        elif obj==".":  self.cachedShowObject(".", " ", x, y)
        elif obj=="$":  self.cachedShowObject(" ", "$", x, y)
        elif obj=="#":  self.cachedShowObject("#", " ", x, y)
        elif obj=="*":  self.cachedShowObject(".", "$", x, y)
        elif obj=="+":  self.cachedShowObject(".", "@", x, y)


  # ###########################################################
  # Für den Editor: ein Objekt durch den Cache ausgeben.
  def cachedShowObject(self, obj_s, obj_d, x, y):
    if self.dspc.getCache(x, y)!=[obj_s, obj_d]: # wenn Änderung zu DisplayCache...
      self.showObject(obj_s, obj_d, x, y, True, False, -1, False, False)
      self.dspc.setCache(x, y, [obj_s, obj_d]) # Ausgaben im DisplayCache merken


  # ###########################################################
  # Zeigt das Spielfeld an.
  def showPlayground(self, dc, clearDC, pgs, dof, pgdp, pp, size, isDeadList, markDeadBoxes, sol_mode):
    self.dc=dc
    self.__resize(size)

    self.dc.SetBackground(wx.Brush(self.col_dict["col_bg"]))
    if clearDC==True:
      self.dspc.clearCache()
      self.dc.Clear()

    for y in range(size[1]):
      rand=False
      for x in range(size[0]):
        s=pgs[y][x]
        if s not in (" ", "_"):
          rand=True
        isdead=False
        debug=-1
#        debug=dof[y][x]#&0x00FF
        d=""
        if hlp.ppack(x, y) in pgdp:
          d="$"
          if markDeadBoxes==True:
            isdead=(x, y) in isDeadList # nur Boxen können tot sein

        if pp==(x, y):
          d="@"
        if self.dspc.getCache(x, y)!=[s, d, isdead, debug, sol_mode]: # wenn Änderung zu DisplayCache...
          self.showObject(s, d, x, y, rand, isdead, debug, markDeadBoxes, sol_mode)
          self.dspc.setCache(x, y, [s, d, isdead, debug, sol_mode]) # Ausgaben im DisplayCache merken


  # ###########################################################
  # Liefert zu einer Fenster-Koordinate in Pixeln die
  # entsprechende Koordinate im Feld. Die zurückgelieferten
  # Koordinaten können auch ausserhalb des Spielfeldes liegen.
  def mousePosToPlaygroundPos(self, (xg, yg)):
    return((xg-self.objOffsetX)/self.objW, (yg-self.objOffsetY)/self.objH)


  # ###########################################################
  # Berechnet abhängig von der aktuellen Fenstergröße die
  # Größe eines Objekts und den Spielfeld-Offset.
  def __resize(self, size):
    dw, dh=self.dc.GetSizeTuple()
    if size[0]==0 or size[1]==0:
      w=h=1               # illegale Feld-Grösse
    else:
      w=int(dw//size[0])  # Display-Breite durch Objekt-Anzahl horizontal
      h=int(dh//size[1])  # Display-Höhe durch Objekt-Anzahl vertikal

    self.objW=self.objH=min(w, h) # es sollen Quadrate werden - also bestimmt der Kleinere die Größe
    self.objOffsetX=int((dw-(self.objW*size[0]))/2) # Leerraum links/rechts neben dem Spielfeld
    self.objOffsetY=int((dh-(self.objH*size[1]))/2) # Leerraum unter/über dem Spielfeld
    

  # ###########################################################
  # Liefert die Pixel-Grösse der Objekte und deren Offset.
  def getDimensions(self):
    return((self.objW, self.objH, self.objOffsetX, self.objOffsetY))


  # ###########################################################
  # Stellt ein Fragezeichen (ggf. plus Linie) auf einem
  # Objekt dar.
  # (sx, sy)  Start-Pos
  # (dx, dy)  Ziel-Pos
  # (px, py)  Player-Pos
  # "mark" darf folgende Werte enthalten:
  #   1 = Start-Pos nicht Box
  #   2 = Ziel-Pos nicht frei
  #   4 = kein Weg zum Start
  #   5 = kein Weg von Start nach Ziel
  def showMark(self, mark, (sx, sy), (dx, dy), (px, py)):
    if   mark==1:
      self.__line(sx, sy, dx, dy)
      self.__singleCharacter(sx, sy, "?")
    elif mark==2:
      self.__line(sx, sy, dx, dy)
      self.__singleCharacter(dx, dy, "?")
    elif mark==4:
      self.__line(px, py, sx, sy)
      self.__singleCharacter(px, py, "?")
      self.__singleCharacter(sx, sy, "?")
    elif mark==5:
      self.__line(sx, sy, dx, dy)
      self.__singleCharacter(sx, sy, "?")
      self.__singleCharacter(dx, dy, "?")


  # ###########################################################
  # Tot-Markierung zwischen zwei Objekten darstellen.
  def __line(self, x1, y1, x2, y2):
    self.dc.SetPen(wx.Pen(self.col_dict["col_mrks"]))
    self.dc.DrawLine( self.objOffsetX+x1*self.objW+self.objW/2, 
                      self.objOffsetY+y1*self.objH+self.objH/2, 
                      self.objOffsetX+x2*self.objW+self.objW/2, 
                      self.objOffsetY+y2*self.objH+self.objH/2)


  # ###########################################################
  # Ein einzelnes Zeichen auf einem Objekt darstellen.
  def __singleCharacter(self, x, y, c):
    self.dc.SetTextForeground(self.col_dict["col_mrks"])

    fnt=wx.Font(5, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    for s in range(5, 200, 5):
      fnt.SetPointSize(s)
      self.dc.SetFont(fnt)
      tw, th=self.dc.GetTextExtent(c)
      if th>self.objH-5:
        break;
    self.dc.DrawText(c, self.objOffsetX+x*self.objW+(self.objW-tw)/2,\
                        self.objOffsetY+y*self.objH)


  # ###########################################################
  # Objekt "obj" an den Feld-Koordinaten x, y anzeigen.
  # Bei Übergabe von "rand==True" wird das Objekt mit
  # Umrandung dargestellt.
  # Bei Übergabe von "isdead==True" wird eine Tot-Markierung
  # dargestellt.
  def showObject(self, obj_s, obj_d, x, y, rand, isdead, debug, markDeadBoxes, sol_mode):
    if rand==True:
      self.dc.SetPen(wx.Pen(self.col_dict["col_flrbdr"]))
    else:
      self.dc.SetPen(wx.Pen(self.col_dict["col_flrbdy"]))

    if obj_s=="_" and markDeadBoxes==True:
      self.dc.SetBrush(wx.Brush(self.col_dict["col_flrbad"]))
    else:
      self.dc.SetBrush(wx.Brush(self.col_dict["col_flrbdy"]))

    self.dc.DrawRectangle(self.objOffsetX+x*self.objW, 
                          self.objOffsetY+y*self.objH, 
                          self.objW, 
                          self.objH)

    if   obj_d=="$":  self.__box(x, y)

    if   obj_s=="#":  self.__wall(x, y)
    elif obj_s==".":  self.__goalSquare(x, y)
    elif obj_s=="u":  self.__floorUnreachable(x, y)
    elif obj_s=="i":  self.__anyOtherUnreachable(x, y)
    else:             self.__floor(x, y)
    
    if   obj_d=="@":
      self.__player(x, y)
      if sol_mode==True:
        self.__singleCharacter(x, y, "s")

    if debug>=0:
      self.dc.SetPen(wx.Pen(self.col_dict["col_txt"]))
      self.dc.SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, \
                                  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
      self.dc.DrawText(hex(debug)[2:].upper(),  self.objOffsetX+x*self.objW+20, \
                                                self.objOffsetY+y*self.objH+20)

    if isdead==True:
      self.__X(x, y)


  # ###########################################################
  # Tot-Markierung darstellen.
  def __X(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_mrks"]))
    self.dc.DrawLine( self.objOffsetX+x*self.objW, 
                      self.objOffsetY+y*self.objH, 
                      self.objOffsetX+x*self.objW+self.objW, 
                      self.objOffsetY+y*self.objH+self.objH)
    self.dc.DrawLine( self.objOffsetX+x*self.objW, 
                      self.objOffsetY+y*self.objH+self.objH, 
                      self.objOffsetX+x*self.objW+self.objW, 
                      self.objOffsetY+y*self.objH)


  # ###########################################################
  # Mauer darstellen.
  def __wall(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_wallbdr"]))
    self.dc.SetBrush(wx.Brush(self.col_dict["col_wall"]))
    self.dc.DrawRectangle(self.objOffsetX+x*self.objW, 
                          self.objOffsetY+y*self.objH, 
                          self.objW, 
                          self.objH)


  # ###########################################################
  # Spielfigur darstellen.
  def __player(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_plrbdr"]))
    self.dc.SetBrush(wx.Brush(self.col_dict["col_plrbdy"]))
    self.dc.DrawCirclePoint(( self.objOffsetX+x*self.objW+self.objW/2, 
                              self.objOffsetY+y*self.objH+self.objH/2), 
                              min(self.objW, self.objH)/2-5)
    self.dc.SetPen(wx.Pen(self.col_dict["col_plrrefbdr"]))
    self.dc.SetBrush(wx.Brush(self.col_dict["col_plrref"]))
    r=min(self.objW, self.objH)/10
    self.dc.DrawCirclePoint(( self.objOffsetX+x*self.objW+self.objW/2-2*r,
                              self.objOffsetY+y*self.objH+self.objH/2-2*r),
                              r)


  # ###########################################################
  # Kiste darstellen.
  def __box(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_boxbdr"]))
    self.dc.SetBrush(wx.Brush(self.col_dict["col_boxbdy"]))
    self.dc.DrawRoundedRectangle( self.objOffsetX+x*self.objW+5,
                                  self.objOffsetY+y*self.objH+5,
                                  self.objW-10,
                                  self.objH-10,
                                  5)


  # ###########################################################
  # Kiste auf Ablagefeld darstellen.
  def __box_ogs(self, x, y):
    self.__box(x, y)
    self.__goalSquare(x, y)


  # ###########################################################
  # Ablagefeld darstellen.
  def __goalSquare(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_gs1"]))
    self.dc.DrawRectangle(self.objOffsetX+x*self.objW+10,
                          self.objOffsetY+y*self.objH+10,
                          2, self.objH-20)
    self.dc.DrawRectangle(self.objOffsetX+x*self.objW+10,
                          self.objOffsetY+y*self.objH+10,
                          self.objW-20, 2)
    self.dc.SetPen(wx.Pen(self.col_dict["col_gs2"]))
    self.dc.DrawRectangle(self.objOffsetX+(x+1)*self.objW-10,
                          self.objOffsetY+y*self.objH+12,
                          2, self.objH-20)
    self.dc.DrawRectangle(self.objOffsetX+x*self.objW+12,
                          self.objOffsetY+(y+1)*self.objH-10,
                          self.objW-20, 2)


  # ###########################################################
  # Boden darstellen.
  def __floor(self, x, y):
    self.dc.SetBrush(wx.Brush(self.col_dict["col_flrbdy"]))


  # ###########################################################
  # Unerreichbaren Boden darstellen.
  def __floorUnreachable(self, x, y):
    self.dc.SetPen(wx.Pen(self.col_dict["col_flrunr"]))
    self.dc.SetBrush(wx.Brush(self.col_dict["col_flrunr"]))
    self.dc.DrawRectangle(self.objOffsetX+x*self.objW, 
                          self.objOffsetY+y*self.objH, 
                          self.objW, 
                          self.objH)


  # ###########################################################
  # Unerreichbares Irgendwas ("$", ".", "*") darstellen.
  def __anyOtherUnreachable(self, x, y):
    self.__floorUnreachable(x, y)
    self.__X(x, y)

    
  # ###########################################################
  # Zeigt eine Fertigmeldung auf dem Spielfeld an.
  def showIsReady(self, msg=0, cnt=1001):
    self.dc.SetTextForeground(self.col_dict["col_txt"])
    readytext=["solved !", "I got it !", "no solution in "+str(cnt)+" moves"]
    fnt=wx.Font(10, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    ww, wh=self.dc.GetSizeTuple()
    for s in range(10, 200, 1):
      fnt.SetPointSize(s)
      self.dc.SetFont(fnt)
      tw, th=self.dc.GetTextExtent(readytext[msg])
      if tw>ww-10:
        break
    self.dc.DrawText(readytext[msg], (ww-tw)/2, (wh-th)/2)






# ###########################################################
# Ein Display-Cache für langsame Grafikkarten.
class DisplayCache():
  def __init__(self):
    self.clearCache()

  def clearCache(self):
    self.cache={}

  def setCache(self, x, y, lst):
    self.cache.update({(x, y) : lst})


  def getCache(self, x, y):
    return(self.cache.get((x, y), []))

