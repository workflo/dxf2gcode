#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_dxf_import
#Programmer: Christian Kohloeffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohloeffel
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


import Core.Globals as g

from Core.Point import Point
from DxfImport.Classes import ContourClass

from DxfImport.GeoentArc import GeoentArc
from DxfImport.GeoentCircle import GeoentCircle
from DxfImport.GeoentInsert import GeoentInsert
from DxfImport.GeoentLine import GeoentLine
from DxfImport.GeoentPolyline import GeoentPolyline
from DxfImport.GeoentSpline import GeoentSpline
from DxfImport.GeoentEllipse import GeoentEllipse
from DxfImport.GeoentLwpolyline import GeoentLwPolyline

#from tkMessageBox import showwarning
from PyQt4 import QtGui, QtCore

from copy import deepcopy, copy
from string import find, strip

import logging
logger=logging.getLogger("DxfImport.Import") 


class ReadDXF(QtCore.QObject):
    #Initialisierung der Klasse
    #Initialise the class
    def __init__(self, filename=None):
        QtCore.QObject.__init__(self)


        #Setting up logger
        #logger=g.logger.logger

        #Laden der Kontur und speichern der Werte in die Klassen
        #Load the contour and store the values in the classes
        str = self.Read_File(filename)

        self.line_pairs = self.Get_Line_Pairs(str)        

        #Debug Informationen 
        #logger.info(("\n\nFile has   %0.0f Lines" % len(str)), 1)
        #logger.info(("\nFile has   %0.0f Linepairs" % self.line_pairs.nrs), 1)

        logger.info(self.tr("Reading DXF Structure"))
        sections_pos = self.Get_Sections_pos()
        self.layers = self.Read_Layers(sections_pos)

        blocks_pos = self.Get_Blocks_pos(sections_pos)
        self.blocks = self.Read_Blocks(blocks_pos)
        self.entities = self.Read_Entities(sections_pos)

        #Aufruf der Klasse um die Konturen zur suchen
        #Schleife fï¿½r die Anzahl der Blï¿½cke und den Layern
        #Call the class to define the contours of search
        #Loop for the number of blocks and the layer
        for i in range(len(self.blocks.Entities)):
            # '\n'
            #print self.blocks.Entities[i]
            logger.info(self.tr("Creating Contours of Block Nr: %i") %i)
            self.blocks.Entities[i].cont = self.Get_Contour(self.blocks.Entities[i])

        logger.info(self.tr("Creating Contours of Entities"))
        self.entities.cont = self.Get_Contour(self.entities)
   
   
    def tr(self,string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("ReadDXF",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8)) 
   
   
    #Laden des ausgewï¿½hlten DXF-Files
    #Load the selected DXF files
    def Read_File(self, filename):
        file = open(filename, 'r')
        str = file.readlines()
        file.close()
        return str
    
    #Die Geladenene Daten in Linien Pare mit Code & Value umwandeln.
    #Convert the uploaded file to line pairs (code & Value).
    def Get_Line_Pairs(self, str):
        line = 0
        line_pairs = dxflinepairsClass([])
        #Start bei der ersten SECTION
        #Start at the first SECTION
        while (find(str[line], "SECTION") < 0):
            line += 1
        line -= 1

        #Durchlauf bis zum Ende falls kein Fehler auftritt. Ansonsten abbruch am Fehler
        #Continue to the end if no error occurs. Otherwise abort with error
        try:
            while line < len(str):
                line_pairs.line_pair.append(dxflinepairClass(int(strip(str[line])), strip(str[line + 1])))
                line += 2

        except:
            QtGui.QMessageBox.warning(g.window,self.tr("Warning reading linepairs"),
                self.tr("Failure reading line stopped at line %0.0f.\n Please check/correct line in dxf file") % (line))
            
            #showwarning("Warning reading linepairs", ("Failure reading line stopped at line %0.0f.\n Please check/correct line in dxf file" % (line)))
            #g.logger.logger.info(("\n!Warning! Failure reading lines stopped at line %0.0f.\n Please check/correct line in dxf file\n " % (line)))
            
        line_pairs.nrs = len(line_pairs.line_pair)
        return line_pairs
    
    #Suchen der Sectionen innerhalb des DXF-Files nï¿½tig um Blï¿½cke zu erkennen.
    #Search the sections in the DXF file to recognize Blocke.
    def Get_Sections_pos(self):
        sections = []
        
        start = self.line_pairs.index_both(0, "SECTION", 0)
        
        #Wenn eine Gefunden wurde diese anhï¿½ngen
        #If a has been found for this attach ???
        while (start != None):
            #Wenn eine Gefunden wurde diese anhï¿½ngen
            #If a has been found for this attach ???
            sections.append(SectionClass(len(sections)))
            sections[-1].begin = start
            name_pos = self.line_pairs.index_code(2, start + 1)
            sections[-1].name = self.line_pairs.line_pair[name_pos].value
            end = self.line_pairs.index_both(0, "ENDSEC", start + 1)
            #Falls Section nicht richtig beendet wurde
            #If section was not properly terminated
            if end == None:
                end = self.line_pairs.nrs - 1
                
            sections[-1].end = end
            
            start = self.line_pairs.index_both(0, "SECTION", end)
            
        #g.logger.logger.info(("\n\nSections found:"), 1)
        #for sect in sections:
            #g.logger.logger.info(str(sect), 1)
        
        return sections
    
    #Suchen der TABLES Section innerhalb der Sectionen diese beinhaltet die LAYERS
    #Search the TABLES section of the sections within this include LAYERS ???
    def Read_Layers(self, section):
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name, "TABLES") == 0):
                tables_section = section[sect_nr]
                break
        
        #Falls das DXF Bloecke hat diese einlesen
        #If the DXF block has this einlese???
        layers = []
        if vars().has_key('tables_section'):
            tables_section = section[sect_nr]
            start = tables_section.begin
            
            while (start != None):
                start = self.line_pairs.index_both(0, "LAYER", start + 1, tables_section.end)
                if(start != None):
                    start = self.line_pairs.index_code(2, start + 1)
                    layers.append(LayerClass(len(layers)))
                    layers[-1].name = self.line_pairs.line_pair[start].value
                    
        #g.logger.logger.info(("Layers found:"), 1)
        #for lay in layers:
            #g.logger.logger.info(str(lay), 1)
        
        return layers
        
        
    #Suchen der BLOCKS Section innerhalb der Sectionen
    #Search the BLOCKS section within sections
    def Get_Blocks_pos(self, section):
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name, "BLOCKS") == 0):
                blocks_section = section[sect_nr]
                break
        
        #Falls das DXF Bloecke hat diese einlesen
        #If the DXF block has read this ???
        blocks = []
        if vars().has_key('blocks_section'):
            start = blocks_section.begin
            start = self.line_pairs.index_both(0, "BLOCK", blocks_section.begin, blocks_section.end)
            while (start != None):
                blocks.append(SectionClass())
                blocks[-1].Nr = len(blocks)
                blocks[-1].begin = start
                name_pos = self.line_pairs.index_code(2, start + 1, blocks_section.end)
                blocks[-1].name = self.line_pairs.line_pair[name_pos].value
                end = self.line_pairs.index_both(0, "ENDBLK", start + 1, blocks_section.end)
                blocks[-1].end = end
                start = self.line_pairs.index_both(0, "BLOCK", end + 1, blocks_section.end)
        
        #g.logger.logger.info(("Blocks found:"), 1)
        #for bl in blocks:
            #g.logger.logger.info(str(bl), 1)
        
        return blocks
    
    #Lesen der Blocks Geometrien
    #Read the block geometries
    def Read_Blocks(self, blocks_pos):
        blocks = BlocksClass([])
        warning = 0
        for block_nr in range(len(blocks_pos)):
            logger.info("Reading Block %s; Nr: %i" %(blocks_pos[block_nr].name,block_nr))
            
            blocks.Entities.append(EntitiesClass(block_nr, blocks_pos[block_nr].name, []))
            #Lesen der BasisWerte fï¿½r den Block
            #Read the Baseline values for the block
            s = blocks_pos[block_nr].begin + 1
            e = blocks_pos[block_nr].end - 1
            lp = self.line_pairs
            #X value
            s = lp.index_code(10, s + 1, e)
            blocks.Entities[-1].basep.x = float(lp.line_pair[s].value)
            #Y value
            s = lp.index_code(20, s + 1, e)
            blocks.Entities[-1].basep.y = float(lp.line_pair[s].value)
            
            #Lesen der Geometrien
            #Read the geometries
            (blocks.Entities[-1].geo, warning) = self.Get_Geo(s, e, warning)
            
        if warning == 1:
            QtGui.QMessageBox.warning(g.window,self.tr("Import Warning"),
                self.tr("Found unsupported or only\npartly supported geometry.\nFor details see status messages!"))
            
        return blocks
    #Lesen der Entities Geometrien
    #Read the entities geometries
    def Read_Entities(self, sections):
        warning = 0
        for section_nr in range(len(sections)):
            if (find(sections[section_nr - 1].name, "ENTITIES") == 0):
                #g.logger.logger.info("Reading Entities", 1)
                entities = EntitiesClass(0, 'Entities', [])
                (entities.geo, warning) = self.Get_Geo(sections[section_nr - 1].begin + 1,
                                                    sections[section_nr - 1].end - 1,
                                                    warning)
        
        if warning == 1:
            QtGui.QMessageBox.warning(g.window,self.tr("Import Warning"),
                ("Found unsupported or only\npartly supported geometry.\nFor details see status messages!"))
            
        return entities
    
    #Lesen der Geometrien von Blï¿½cken und Entities
    #Read the geometries of Blocks and Entities
    def Get_Geo(self, begin, end, warning):
        geos = []
        self.start = self.line_pairs.index_code(0, begin, end)
        old_start = self.start
        
        while self.start != None:
            #Laden der aktuell gefundenen Geometrie
            #Load the currently found geometry
            name = self.line_pairs.line_pair[self.start].value         
            entitie_geo, warning = self.get_geo_entitie(len(geos), name, warning)
            
            #Hinzufï¿½gen der Werte Wenn es gerade gefunden wurde
            #Shortlist of values if it was just found
            if warning == 2:
                #Zurï¿½cksetzen zu Warnung allgemein
                #Reset warning ???
                warning = 1
            else:
                geos.append(entitie_geo)
            
            #Die nï¿½chste Suche Starten nach dem gerade gefundenen
            #Start the next search after one just found
            self.start = self.line_pairs.index_code(0, self.start, end)            

            #Debug Informationen anzeigen falls erwï¿½nscht
            #Show debugging information if desired
            #if self.start == None:
                #g.logger.logger.info(("Found %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                        #% (name, old_start, old_start * 2 + 4, end * 2 + 4)), 1)
            #else:
                #g.logger.logger.info(("Found %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                        #% (name, old_start, old_start * 2 + 4, self.start * 2 + 4)), 1)

            #if len(geos) > 0:
                #g.logger.logger.info(str(geos[-1]), 2)

            old_start = self.start
            
        del(self.start)
        return geos, warning

    #Verteiler fï¿½r die Geo-Instanzen
    # wird in def Get_Geo aufgerufen
    # fï¿½r einen Release kann der ganze Code gerne wieder in einer Datei landen.
    #Distributor for Geo instances ???
    # is called in def Get_Geo
    # For a release of the entire code can be happy again end up in a file. ???
    def get_geo_entitie(self, geo_nr, name, warning):
        #Entities:
        # 3DFACE, 3DSOLID, ACAD_PROXY_ENTITY, ARC, ATTDEF, ATTRIB, BODY
        # CIRCLE, DIMENSTION, ELLIPSE, HATCH, IMAGE, INSERT, LEADER, LINE,
        # LWPOLYLINE, MLINE, MTEXT, OLEFRAME, OLE2FRAME, POINT, POLYLINE,
        # RAY, REGION, SEQEND, SHAPE, SOLID, SPLINE, XT, TOLERANCE, TRACE,
        # VERTEX, VIEWPOINT, XLINE
        
        # Instanz des neuen Objekts anlegen und gleichzeitig laden
        # Create a new instance of the object and at the same load ???
        if(name == "POLYLINE"):
            geo = GeoentPolyline(geo_nr, self)
        elif (name == "SPLINE"):
            geo = GeoentSpline(geo_nr, self)
        elif (name == "ARC"):
            geo = GeoentArc(geo_nr, self)
        elif (name == "CIRCLE"):
            geo = GeoentCircle(geo_nr, self)
        elif (name == "LINE"):
            geo = GeoentLine(geo_nr, self)
        elif (name == "INSERT"):
            geo = GeoentInsert(geo_nr, self)
        elif (name == "ELLIPSE"):
            geo = GeoentEllipse(geo_nr, self)
        elif (name == "LWPOLYLINE"):
            geo = GeoentLwPolyline(geo_nr, self)
        else:  
            #g.logger.logger.info(("!!!!WARNING Found unsupported geometry: %s !!!!" % name))
            self.start += 1 #Eins hochzï¿½hlen sonst gibts ne dauer Schleife
            warning = 2
            return [], warning
            
        return geo, warning

    #Findet die Nr. des Geometrie Layers
    #Find the number of geometry layers
    def Get_Layer_Nr(self, Layer_Name):
        for i in range(len(self.layers)):
            if (find(self.layers[i].name, Layer_Name) == 0):
                layer_nr = i
                return layer_nr
        layer_nr = len(self.layers)
        self.layers.append(LayerClass(layer_nr))
        self.layers[-1].name = Layer_Name
        return layer_nr
    
    #Findet die Nr. des Blocks
    #Find the number of blocks
    def Get_Block_Nr(self, Block_Name):
        block_nr = -1
        for i in range(len(self.blocks.Entities)):
            if (find(self.blocks.Entities[i].Name, Block_Name) == 0):
                block_nr = i
                break  
        return block_nr
    
    #Findet die beste Kontur der zusammengesetzen Geometrien
    #Find the best contour the composite geometries
    def Get_Contour(self, entities=None):
        cont = []
        
        points = self.App_Cont_or_Calc_IntPts(entities.geo, cont)
        points = self.Find_Common_Points(points)
        #points=self.Remove_Redundant_Geos(points)
        
        cont = self.Search_Contours(entities.geo, points, cont)
        
        return cont
    
    #Berechnen bzw. Zuweisen der Anfangs und Endpunkte
    #Calculate and assign the start and end points
    def App_Cont_or_Calc_IntPts(self, geo=None, cont=None):
        
        tol = g.config.point_tolerance
        points = []
        warning = 0
        for i in range(len(geo)) :
            warning = geo[i].App_Cont_or_Calc_IntPts(cont, points, i, tol, warning)
        
        if warning:
            QtGui.QMessageBox.warning(g.window,self.tr("Short Elements"), self.tr("Length of some Elements too short!"\
                                               "\nLength must be greater then tolerance."\
                                               "\nSkipped Geometries"))
        
        return points
    
    #Suchen von gemeinsamen Punkten
    #Find common points
    def Find_Common_Points(self, points=None):
        #tol=self.config.points_tolerance.get()
        tol = g.config.point_tolerance
        
        p_list = []
        
        #Einen List aus allen Punkten generieren
        #Generate list of all points
        for p in points:
            p_list.append([p.Layer_Nr, p.be.x, p.be.y, p.point_nr, 0])
            p_list.append([p.Layer_Nr, p.en.x, p.en.y, p.point_nr, 1])
        
        #Sort the list
        p_list.sort()
        #print p_list
        
        #Eine Schleife fï¿½r die Anzahl der List Elemente durchlaufen
        #Start = wo die Suche der gleichen Elemente beginnen soll
        #Loop for number of list items
        #Start = where to begin the search of the same elements
        anf = []
        
        for l_nr in range(len(p_list)):
            inter = []
            #print ("Suche Starten fï¿½r Geometrie Nr: %i, Punkt %i" %(p_list[l_nr][3],l_nr))
            
            if type(anf) is list:
                c_nr = 0
            else:
                c_nr = anf
                
            anf = []
            
            #Schleife bis nï¿½chster X Wert Grï¿½ï¿½er ist als selbst +tol und Layer Grï¿½ï¿½er gleich
            #Loop until the next X value is greater than yourself and layer Gr + tol he same ???
            while (p_list[c_nr][0] < p_list[l_nr][0]) | \
                  (p_list[c_nr][1] <= (p_list[l_nr][1] + tol)):
                #print ("Suche Punkt %i" %(c_nr))
                
                #Erstes das ï¿½bereinstimmt is der nï¿½chste Anfang
                #First, the match is the next start
                if (type(anf) is list) & \
                   (p_list[c_nr][0] == p_list[l_nr][0]) & \
                   (abs(p_list[c_nr][1] - p_list[l_nr][1]) <= tol):
                    anf = c_nr
                    #print ("Nï¿½chste Suche starten bei" +str(anf))
                    
                #Falls gleich anhï¿½ngen
                #Attach if equal ???
                if  (p_list[c_nr][0] == p_list[l_nr][0]) & \
                    (abs(p_list[c_nr][1] - p_list[l_nr][1]) <= tol) & \
                    (abs(p_list[c_nr][2] - p_list[l_nr][2]) <= tol) & \
                    (c_nr != l_nr):
                    inter.append(c_nr)
                    #print ("Gefunden" +str(inter))
                c_nr += 1

                if c_nr == len(p_list):
                    break
            
            #Anhï¿½ngen der gefundenen Punkte an points
            #Append the found points
            for int_p in inter:
                #Common Anfangspunkt
                #Common starting point
                if p_list[l_nr][-1] == 0:
                    points[p_list[l_nr][-2]].be_cp.append(p_list[int_p][3:5])
                #Common Endpunkt
                #Common end point
                else:
                    points[p_list[l_nr][-2]].en_cp.append(p_list[int_p][3:5])
        
        return points
    
    def Remove_Redundant_Geos(self, geo=None, points=None):
        pass
#        del_points=[]
#        for p_nr in range(len(points)):
#            if not(p_nr in del_points):
#                for be_p in points[p_nr].be_cp:
#                    for en_p in points[p_nr].en_cp:
#                        if be_p[0]==en_p[0]:
#                            del_points.append(be_p[0])
#                            print ('Gleiche Punkte in Anfang: %s und Ende %s' %(be_p,en_p))
#                    
#        #Lï¿½schen der ï¿½berflï¿½ssigen Punkte
#        #Delete the ? points ???
#        for p_nr in del_points:
#            for j in range(len(points)):
#                if p_nr==points[j].point_nr:
#                    del points[j]
#                    break
#        return points        
    
    #Suchen nach den besten zusammenhï¿½ngenden Konturen
    #Find the best continuous contours
    def Search_Contours(self, geo=None, all_points=None, cont=None):
        
        points = deepcopy(all_points)
        
        while(len(points)) > 0:
            #print '\n Neue Suche'
            #Wenn nichts gefunden wird dann einfach die Kontur hochzï¿½hlen
            #If nothing found then count up the contour
            if (len(points[0].be_cp) == 0) & (len(points[0].en_cp) == 0):
                #print '\nGibt Nix'
                cont.append(ContourClass(len(cont), 0, [[points[0].point_nr, 0]], 0))
            elif (len(points[0].be_cp) == 0) & (len(points[0].en_cp) > 0):
                #print '\nGibt was Rï¿½ckwï¿½rts (Anfang in neg dir)'
                new_cont_pos = self.Search_Paths(0, [], points[0].point_nr, 0, points)
                cont.append(self.Get_Best_Contour(len(cont), new_cont_pos, geo, points))
            elif (len(points[0].be_cp) > 0) & (len(points[0].en_cp) == 0):
                #print '\nGibt was Vorwï¿½rt (Ende in pos dir)'
                new_cont_neg = self.Search_Paths(0, [], points[0].point_nr, 1, points)
                cont.append(self.Get_Best_Contour(len(cont), new_cont_neg, geo, points))
            elif (len(points[0].be_cp)>0) & (len(points[0].en_cp)>0):
                #print '\nGibt was in beiden Richtungen'
                #Suchen der möglichen Pfade
                #Search the possible paths
                new_cont_pos=self.Search_Paths(0,[],points[0].point_nr,1,points)
                #Bestimmen des besten Pfades und übergabe in cont
                #Determine the best path and Xbergabe in cont ???
                cont.append(self.Get_Best_Contour(len(cont),new_cont_pos,geo,points))
                #points=self.Remove_Used_Points(cont[-1],points)
                
                #Falls der Pfad nicht durch den ersten Punkt geschlossen ist
                #If the path is not closed by the first point
                if cont[-1].closed==0:
                    #print '\nPfad nicht durch den ersten Punkt geschlossen'
                    cont[-1].reverse()
                    #print ("Neue Kontur umgedrejt %s" %cont[-1])
                    new_cont_neg=self.Search_Paths(0,[cont[-1]],points[0].point_nr,0,points)
                    cont[-1]=self.Get_Best_Contour(len(cont)-1,new_cont_neg+new_cont_pos,geo,points)
                    
            else:
                print 'FEHLER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            
            points = self.Remove_Used_Points(cont[-1], points)
            
            cont[-1] = self.Contours_Points2Geo(cont[-1], all_points)
        return cont
    
    #Suchen die Wege duch die Konturn !!! REKURSIVE SCHLEIFE WAR SAU SCHWIERIG
    #Search the paths through the Contour !!! RECURSIVE LOOP WAS DIFFICULT
    def Search_Paths(self, c_nr=None, c=None, p_nr=None, dir=None, points=None):
        
        #Richtung der Suche definieren (1= pos, 0=neg bedeutet mit dem Ende Anfangen)
        #Define the direction of the search (1 = positive, 0 = neg or reverse)
        
        #Wenn es der erste Aufruf ist und eine neue Kontur angelegt werden muss
        #If it is the first call a new contour is to be created
        if len(c) == 0:
            c.append(ContourClass(cont_nr=0, order=[[p_nr, dir]]))   
        
        #Suchen des Punktes innerhalb der points List (nï¿½tig da verwendete Punkte gelï¿½scht werden)
        #Search for the item within the list of points (ntig used as points gelscht) ???
        for new_p_nr in range(len(points)):
            if points[new_p_nr].point_nr == p_nr:
                break
        
        #Nï¿½chster Punkt abhï¿½ngig von der Richtung
        #Next point depending on the direction
        if dir == 0:
            weiter = points[new_p_nr].en_cp
        elif dir == 1:
            weiter = points[new_p_nr].be_cp
            
        #Schleife fï¿½r die Anzahl der Abzweig Mï¿½glichkeiten
        #Loop for the number of the branch can write ???
        for i in range(len(weiter)):
            #Wenn es die erste Mï¿½glichkeit ist Hinzufï¿½gen zur aktuellen Kontur
            #If it is the first possibility to add to the current contour
            if i == 0:
                if not(c[c_nr].is_contour_closed()):
                    c[c_nr].order.append(weiter[0])
                    
            #Es gibt einen Abzweig, es wird die aktuelle Kontur kopiert und dem
            #anderen Zweig gefolgt
            #There is a branch.  It is copied to the current contour and the
            #other branches follow
            elif i > 0:
                if not(c[c_nr].is_contour_closed()):
                    #print 'Abzweig ist mï¿½glich'
                    c.append(deepcopy(c[c_nr]))
                    del c[-1].order[-1]
                    c[-1].order.append(weiter[i])
                    
        for i in range(len(weiter)):
            #print 'I ist: ' +str(i)
            if i == 0:
                new_c_nr = c_nr
            else:
                new_c_nr = len(c) - len(weiter) + i
                
            new_p_nr = c[new_c_nr].order[-1][0]
            new_dir = c[new_c_nr].order[-1][1]
            if not(c[new_c_nr].is_contour_closed()):
                c = self.Search_Paths(copy(new_c_nr), c, copy(new_p_nr), copy(new_dir), points)        
        return c 
    #Sucht die beste Kontur unter den gefunden aus (Meiner Meinung nach die Beste)
    #Seek the best (in my opinion) contour
    def Get_Best_Contour(self, c_nr, c=None, geo=None, points=None):
        
        #Hinzufï¿½gen der neuen Kontur
        #Shortlist of the new contour
        best = None
        best_open = None
        #print ("Es wurden %0.0f Konturen gefunden" %len(c))
        for i in range(len(c)):
            #if len(c)>1:
                #print ("Kontur Nr %0.0f" %i)
                #print c[i]
                
            #Korrigieren der Kontur falls sie nicht in sich selbst geschlossen ist
            #The correct contour if it is not closed in on itself
            if c[i].closed == 2:
                c[i].remove_other_closed_contour()
                c[i].closed = 0
                c[i].calc_length(geo)
            #Suchen der besten Geometrie
            #Search for the best geometry
            if c[i].closed == 1:
                c[i].calc_length(geo)
                if best == None:
                    best = i
                else:
                    if c[best].length < c[i].length:
                        best = i
            elif c[i].closed == 0:
                c[i].calc_length(geo)
                if best_open == None:
                    best_open = i
                else:
                    if c[best_open].length < c[i].length:
                        best_open = i
            
            #Falls keine Geschschlossene dabei ist Beste = Offene
            #If no Geschschlossene is best = Open ???
        if best == None:
            best = best_open
        
        best_c = c[best]
        best_c.cont_nr = c_nr
        
        #print "Beste Kontur Nr:%s" %best_c

        return best_c
    
    #Alle Punkte im Pfad aus Points lÃ¶schen um nÃ¤chte Suche zu beschleunigen
    #All the points in the path from Point Clear to accelerate nights Search ???
    def Remove_Used_Points(self,cont=None,points=None):
        for p_nr in cont.order:
            
            #This has to be 2 separate loops, otherwise one element is missing
            for Point in points:
                if p_nr[0]==Point.point_nr:
                    del points[points.index(Point)]
            
            for Point in points:
                for be_cp in Point.be_cp:
                    if p_nr[0]==be_cp[0]:
                        del Point.be_cp[Point.be_cp.index(be_cp)]
                        break
                    
                for en_cp in Point.en_cp:
                    if p_nr[0]==en_cp[0]:
                        del Point.en_cp[Point.en_cp.index(en_cp)]
                        break
                
        #Rückgabe der Kontur
        #Return to the contour ???
        return points
    
    #Alle Punkte im Pfad aus Points lï¿½schen um nï¿½chte Suche zu beschleunigen
    #All the points in the path from Point Clear to accelerate nights Search ???
    def Contours_Points2Geo(self, cont=None, points=None):
        #print cont.order
        for c_nr in range(len(cont.order)):
            cont.order[c_nr][0] = points[cont.order[c_nr][0]].geo_nr
        return cont
        
class dxflinepairClass:
    def __init__(self, code=None, value=None):
        self.code = code
        self.value = value
    def __str__(self):
        return 'Code ->' + str(self.code) + '\nvalue ->' + self.value
    
class dxflinepairsClass:
    def __init__(self, line_pair=[]):
        self.nrs = 0
        self.line_pair = line_pair
    def __str__(self):
        return 'Number of Line Pairs: ' + str(self.nrs)
    
    #Sucht nach beiden Angaben in den Line Pairs code & value
    #optional mit start und endwert fï¿½r die Suche
    #Search for information in the line pairs (both code & value)
    #Optional start and end values for the search
    def index_both(self, code=0, value=0, start=0, stop= -1):
        
        #Wenn bei stop -1 angegeben wird stop am ende der pairs
        #If stop==-1 then stop at the end of the pairs
        if stop == -1:
            stop = len(self.line_pair)
        
        #Starten der Suche innerhalb mit den angegeben parametern
        #Start the search within the specified parameters
        for i in range(start, stop):
            if (self.line_pair[i].code == code) & (self.line_pair[i].value == value):
                return i
        
        #Wenn nicht gefunden wird None ausgeben
        #If nothing found return "None"
        return None
    
    #Sucht nach Code Angaben in den Line Pairs code & value
    #optional mit start und endwert fï¿½r die Suche
    #Search for information in the Line Pairs (both code & value)
    #Optional start and end values for the search
    def index_code(self, code=0, start=0, stop= -1):
        
        #Wenn bei stop -1 angegeben wird stop am ende der pairs
        #If stop==-1 then stop at the end of the pairs
        if stop == -1:
            stop = len(self.line_pair)
            
        #Starten der Suche innerhalb mit den angegeben parametern
        #Start the search within the specified parameters
        for i in range(start, stop):
            if (self.line_pair[i].code == code):
                return i
            
        #Wenn nicht gefunden wird None ausgeben
        #If nothing found return "None"
        return None

class LayerClass:
    def __init__(self, Nr=0, name=''):
        self.Nr = Nr
        self.name = name
    def __str__(self):
        # how to print the object
        return 'Nr ->' + str(self.Nr) + '\nName ->' + self.name
    def __len__(self):
        return self.__len__

class SectionClass:
    def __init__(self, Nr=0, name='', begin=0, end=1):
        self.Nr = Nr
        self.name = name
        self.begin = begin
        self.end = end  
    def __str__(self):
        # how to print the object
        return 'Nr ->' + str(self.Nr) + '\nName ->' + self.name + '\nBegin ->' + str(self.begin) + '\nEnd: ->' + str(self.end)
    def __len__(self):
        return self.__len__

class EntitiesClass:
    def __init__(self, Nr=0, Name='', geo=[], cont=[]):
        self.Nr = Nr
        self.Name = Name
        self.basep = Point(x=0.0, y=0.0)
        self.geo = geo
        self.cont = cont
        
    def __str__(self):
        # how to print the object
        return '\nNr:      %s' % (self.Nr) + \
                '\nName:    %s' % (self.Name) + \
                '\nBasep:   %s' % (self.basep) + \
                '\nNumber or Geometries: %i' % (len(self.geo)) + \
                '\nNumber of Contours:   %i' % (len(self.cont))
                
               
    def __len__(self):
        return self.__len__
    
    #Gibt einen List mit den Benutzten Layers des Blocks oder Entities zurï¿½ck
    #Is a List back to results with the use of block layer or Entities ???
    def get_used_layers(self):
        used_layers = []
        for i in range(len(self.geo)):
            if (self.geo[i].Layer_Nr in used_layers) == 0:
                used_layers.append(self.geo[i].Layer_Nr)
        return used_layers
    #Gibt die Anzahl der Inserts in den Entities zurï¿½ck
    #Returns the number of inserts back into the Entities ???
    def get_insert_nr(self):
        insert_nr = 0
        for i in range(len(self.geo)):
            if ("Insert" in self.geo[i].Typ):
                insert_nr += 1
        return insert_nr
    
class BlocksClass:
    def __init__(self, Entities=[]):
        self.Entities = Entities
    def __str__(self):
        # how to print the object
        s = 'Blocks:\nNumber of Blocks ->' + str(len(self.Entities))
        for entitie in self.ties:
            s = s + str(entitie)
        return s
