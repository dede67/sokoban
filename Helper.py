#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Position [ent]packen
ppack  =lambda x, y : x+(y<<8)                # x, y packen
ppackt =lambda xy   : xy[0]+(xy[1]<<8)        # (x, y) packen
punpack=lambda xy   : ((xy&0xFF), (xy>>8))    # xy entpacken nach (x, y)

# Zug [ent]packen
mpack  =lambda (x, y), d  : (x<<2)+(y<<10)+d                              # (x, y), d packen
munpack=lambda xyd        : (((xyd>>2)&0xFF, (xyd>>10)&0xFF), xyd&0x03)   # xyd entpacken nach (x, y), d

# gepackte Spieler-Position aus gepacktem Zug extrahieren
mpack2ppack=lambda xyd  : xyd>>2              # xyd wandeln nach xy
mpack2pdir =lambda xyd  : xyd&0x03            # xyd wandeln nach d

# ###########################################################
# Liefert die ungepackte BoxPos, an dem ein gepackter Push
# (bzw. Zug) wirkt.
def pushedBoxForPackedMove(pm):
  (x, y), d=munpack(pm)
  if   d==0:  return((x-1, y))
  elif d==1:  return((x+1, y))
  elif d==2:  return((x, y-1))
  else     :  return((x, y+1))

# ###########################################################
# Liefert die Zahl x mit Tausender-Trenn-Punkten
def intToStringWithCommas(x):
  if type(x) is not int and type(x) is not long:
    raise TypeError("Not an integer!")
  if x<0:
    return('-'+intToStringWithCommas(-x))
  elif x<1000:
    return(str(x))
  else:
    return(intToStringWithCommas(x/1000)+'.'+'%03d'%(x%1000))


# ###########################################################
# Liefert eine Kopie der Liste "list2copy".
def copyList(list2copy):
  to_l=[]
  for i in list2copy:
    to_l.append(i)
  return(to_l)


# debugging

def unpackPosList(lst):
  os=[]
  for i in lst:
    os.append(punpack(i))
  return(os)

def unpackMovList(lst):
  os=[]
  for i in lst:
    os.append(munpack(i))
  return(os)


