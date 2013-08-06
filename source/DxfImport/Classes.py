#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
#Programmers:   Christian Kohlöffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


#from Canvas import Oval, Arc, Line

class PointsClass:
    #Initialisieren der Klasse
    #Initialise the class
    def __init__(self, point_nr=0, geo_nr=0, Layer_Nr=None, be=[], en=[], be_cp=[], en_cp=[]):
        self.point_nr = point_nr
        self.geo_nr = geo_nr
        self.Layer_Nr = Layer_Nr
        self.be = be
        self.en = en
        self.be_cp = be_cp
        self.en_cp = en_cp
        
    
    #Wie die Klasse ausgegeben wird.
    #???
    def __str__(self):
        # how to print the object
        return '\npoint_nr ->' + str(self.point_nr) + '\ngeo_nr ->' + str(self.geo_nr) \
               + '\nLayer_Nr ->' + str(self.Layer_Nr)\
               + '\nbe ->' + str(self.be) + '\nen ->' + str(self.en)\
               + '\nbe_cp ->' + str(self.be_cp) + '\nen_cp ->' + str(self.en_cp)

class ContourClass:
    #Initialisieren der Klasse
    #Initialise the class
    def __init__(self, cont_nr=0, closed=0, order=[], length=0):
        self.cont_nr = cont_nr
        self.closed = closed
        self.order = order
        self.length = length

    #Komplettes umdrehen der Kontur
    #Reverse the contour
    def reverse(self):
        self.order.reverse()
        for i in range(len(self.order)):
            if self.order[i][1] == 0:
                self.order[i][1] = 1
            else:
                self.order[i][1] = 0
        return

    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    #If contour is closed return 1
    def is_contour_closed(self):

        #Immer nur die Letzte überprüfen da diese neu ist
        #Check as this is new...
        for j in range(len(self.order) - 1):
            if self.order[-1][0] == self.order[j][0]:
                if j == 0:
                    self.closed = 1
                    return self.closed
                else:
                    self.closed = 2
                    return self.closed
        return self.closed


    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    #If the contour is closed return 1
    def remove_other_closed_contour(self):
        for i in range(len(self.order)):
            for j in range(i + 1, len(self.order)):
                #print '\ni: '+str(i)+'j: '+str(j)
                if self.order[i][0] == self.order[j][0]:
                    self.order = self.order[0:i]
                    break
        return 
    #Berechnen der Zusammengesetzen Kontur Länge
    #Calculate the contour length
    def calc_length(self, geos=None):        
        #Falls die beste geschlossen ist und erste Geo == Letze dann entfernen
        #If the best is closed and first geo == last then remove
        if (self.closed == 1) & (len(self.order) > 1):
            if self.order[0] == self.order[-1]:
                del(self.order[-1])

        self.length = 0
        for i in range(len(self.order)):
            self.length += geos[self.order[i][0]].length
        return

    #Neuen Startpunkt an den Anfang stellen
    #New starting point, set to the beginning
    def set_new_startpoint(self, st_p):
        self.order = self.order[st_p:len(self.order)] + self.order[0:st_p]
        
    #Wie die Klasse ausgegeben wird.
    #???
    def __str__(self):
        # how to print the object
        return '\ncont_nr ->' + str(self.cont_nr) + '\nclosed ->' + str(self.closed) \
               + '\norder ->' + str(self.order) + '\nlength ->' + str(self.length)
