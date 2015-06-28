#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import zlib


class Database():
  def __init__(self, dbname):
    if os.path.isfile(dbname)==False:
      initDB=True
    else:
      initDB=False

    self.connection=sqlite3.connect(dbname)
    self.cursor=self.connection.cursor()

    if initDB==True:
      self.createDatabase()

  # ###########################################################
  # Legt die Tabelle an.
  def createDatabase(self):
    self.cursor.execute('CREATE TABLE "solutions" ' \
                        '("md5" VARCHAR PRIMARY KEY NOT NULL UNIQUE, ' \
                        '"solved_by" VARCHAR, ' \
                        '"game_file" VARCHAR NOT NULL, ' \
                        '"game_name" VARCHAR, ' \
                        '"sol_length" INTEGER, ' \
                        '"solution" BLOB)')
    self.connection.commit()

  # ###########################################################
  # Speichert die Lösung für ein Spiel. War es vorher schon
  # gelöst, wird nur eine bessere bzw. kürzere Lösung
  # gespeichert.
  def saveSolution(self, md5, usr, game_file, game_name, solution):
    if md5=="" or usr=="" or game_file=="" or game_name=="" or solution=="":
      return
    l=len(self.loadSolution(md5)[0])
    if l==0:  # wenn erstmalig gelöst
      self.cursor.execute('INSERT INTO solutions (md5, solved_by, game_file, game_name, sol_length, solution) ' \
                          'VALUES (?, ?, ?, ?, ?, ?)', \
                          (md5, usr, game_file, game_name, len(solution), sqlite3.Binary(zlib.compress(solution))))
      self.connection.commit()
    elif len(solution)<l:  # wenn kürzer
      self.cursor.execute('UPDATE solutions SET solved_by=?, sol_length=?, solution=? WHERE md5=?', \
                          (usr, len(solution), sqlite3.Binary(zlib.compress(solution)), md5))
      self.connection.commit()

  # ###########################################################
  # Liefert ein Tupel aus Lösung und Lösendem für das
  # aktuelle Spiel. Liefert ein Tupel mit Leerstrings,
  # wenn noch keine Lösung vorhanden ist.
  def loadSolution(self, md5):
    self.cursor.execute('SELECT solution, solved_by FROM solutions WHERE md5=?', (md5, ))
    c=self.cursor.fetchone()
    if c==None:
      return("", "")
    else:
      return(zlib.decompress(c[0]), c[1])

  # ###########################################################
  # Liefert nur die Länge der Lösung samt Lösendem für die
  # Anzeige des Lösungs-Status im Spiele-Auswahl-Dialog.
  def getSolutionLength(self, md5):
    self.cursor.execute('SELECT sol_length, solved_by FROM solutions WHERE md5=?', (md5, ))
    c=self.cursor.fetchone()
    if c==None:
      return("", "")
    else:
      return(c[0], c[1])

  # ###########################################################
  # Importiert aus einer anderen DB solche Sätze, bei denen 
  # für ein Spiel (bzw. MD5) eine kürzere Lösung existiert oder
  # ein bisher noch nicht gelöstes Spiel gefunden wird.
  def mergeDB(self, fn):
    connection=sqlite3.connect(fn)
    cursor=connection.cursor()

    ins_cnt=0
    upd_cnt=0
    cursor.execute('SELECT md5, solved_by, game_file, game_name, sol_length, solution FROM solutions')
    c=cursor.fetchall()
    # über alle Spiele der zu importierenden DB...
    for md5, solved_by, game_file, game_name, sol_length, solution in c:
      self.cursor.execute('SELECT solved_by, game_file, game_name, sol_length, solution ' \
                          'FROM solutions WHERE md5=?', (md5, ))
      cl=self.cursor.fetchone()

      if cl==None:  # wenn Lösung gefunden, für die hier keine Lösung existiert...
        print "new solution: ", game_file, game_name
        self.cursor.execute('INSERT INTO solutions (md5, solved_by, game_file, game_name, sol_length, solution) ' \
                            'VALUES (?, ?, ?, ?, ?, ?)', \
                            (md5, solved_by, game_file, game_name, sol_length, solution))
        self.connection.commit()
        ins_cnt+=1
      elif sol_length<cl[3]:  # wenn kürzere Lösung gefunden...
        print "better solution: ", game_file, game_name
        self.cursor.execute('UPDATE solutions SET solved_by=?, sol_length=?, solution=? WHERE md5=?', \
                            (solved_by, sol_length, solution, md5))
        self.connection.commit()
        upd_cnt+=1
    connection.close()
    return(ins_cnt, upd_cnt)

  # ###########################################################
  # Liefert True, wenn fn eine SokobanV2-DB-Datei ist.
  def isSokoV2DB(self, fn):
    sql='CREATE TABLE "solutions" ("md5" VARCHAR PRIMARY KEY NOT NULL UNIQUE, "solved_by" VARCHAR, ' \
        '"game_file" VARCHAR NOT NULL, "game_name" VARCHAR, "sol_length" INTEGER, "solution" BLOB)'

    connection=sqlite3.connect(fn)
    cursor=connection.cursor()

    try:
      cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" and name="solutions"')
    except:
      return(False)
    c=cursor.fetchone()
    if c!=None:
      if c[0]==sql:
        return(True)
    return(False)


