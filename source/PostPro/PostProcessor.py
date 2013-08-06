#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_config.py
#Programmers:   Christian Kohloeffel
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

#About Dialog
#First Version of dxf2gcode Hopefully all works as it should
#Compiled with --onefile --noconsole --upx --tk dxf2gcode_b02.py

import os
import time

from math import degrees

from PyQt4 import QtGui, QtCore

import Core.constants as c
import Core.Globals as g

from Core.Point import Point
#from d2gexceptions import *

import logging
logger = logging.getLogger("PostPro.PostProcessor") 

from PostPro.PostProcessorConfig import MyPostProConfig


class MyPostProcessor(QtCore.QObject):
    """
    The PostProcessor Class includes the functions for getting the output
    variables from the PostProcessorConfig Classes and general function related
    to the export of the Code.
    """
    def __init__(self):
        """
        The initialisation of the Postprocessor class. This function is called
        during the initialisation of the Main Window. It checks during the
        initialization if a PostProcessor Config file exists and if not creates
        a new one.
        For the Save function it creates a list of all possible Postprocessor
        Config Files.
        """

        try:
            lfiles = os.listdir(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR))
            """
            FIXME Folder needs to be empty or valid config file within.
            """
            #logger.debug(lfiles)
        except:
    
            #If no Postprocessor File was found in folder create one
            logger.debug(self.tr("created default varspace"))
            PostProConfig=MyPostProConfig()
            PostProConfig.create_default_config()
            PostProConfig.default_config = True

            
            lfiles = os.listdir(PostProConfig.folder)
            
        
            
        #Only files ending with *.cfg will be accepted.
        self.postprocessor_files = []
        for lfile in lfiles:
            if os.path.splitext(lfile)[1] == '.cfg':
                self.postprocessor_files.append(lfile)
                
        if len(self.postprocessor_files)==0:
            PostProConfig=MyPostProConfig()
            PostProConfig.create_default_config()
            PostProConfig.default_config = True
            lfiles = os.listdir(PostProConfig.folder)
            
            self.postprocessor_files = []
            for lfile in lfiles:
                if os.path.splitext(lfile)[1] == '.cfg':
                    self.postprocessor_files.append(lfile)
                
        #Load all files to get the possible postprocessor configs to export
        self.get_output_vars()
        
    def tr(self,string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("MyPostProcessor",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8)) 
      
    def get_output_vars(self):
        """
        Reads all Postprocessor Config Files located in the PostProcessor Config
        Directory and creates a list of the possible output formats.
        """
        self.output_format = []
        self.output_text = []
        for postprocessor_file in self.postprocessor_files:
            
            PostProConfig=MyPostProConfig(filename=postprocessor_file)
            PostProConfig.load_config()
            
            self.output_format.append(PostProConfig.vars.General['output_format'])
            self.output_text.append(PostProConfig.vars.General['output_text'])

    def getPostProVars(self,file_index):
        """
        Get the parameters of the Postprocessor Config File
        @param file_index: The index of the file to read and write variables in
        self.vars. 
        """
        
        PostProConfig=MyPostProConfig(filename=self.postprocessor_files[file_index])
        PostProConfig.load_config()
        self.vars=PostProConfig.vars
        
    def exportShapes(self,load_filename,save_filename,LayerContents):
        """
        This is the function which performs the export to a file or to the
        stdout. It calls the following dedicated export functions and runs 
        though the list of layers to export after checking if there are shapes
        to export on these layers.
        @param load_filename: The name of the loaded dxf file. This name is
        written at the begin of the export
        @param save_filename: The name of the file which shall be created. 
        @param LayerContents: This is a list which includes the order of the 
        LayerContent to be exported and the LayerContent itself includes the 
        export parameters (e.g. mill depth) and the shapes to be exported. The
        shape order is also given in a list defined in LayerContent.
        """

        self.initialize_export_vars()

        exstr=self.write_gcode_be(load_filename)
        
        #Move Machine to retraction Area before continuing anything. Note: none of the changes done in the GUI can affect this height, only the config file can do so (intended)
        exstr+=self.rap_pos_z(g.config.vars.Depth_Coordinates['axis3_retract'])

        previous_tool = None
        #Do the export for each LayerContent in LayerContents List
        for LayerContent in LayerContents:
            logger.debug(self.tr("Beginning export of Layer Nr. %s, Name%s") 
                         %(LayerContent.LayerNr,LayerContent.LayerName))
            logger.debug(self.tr("Nr. of Shapes %s; Nr. of Shapes in Route %s") 
                         %(len(LayerContent.shapes),len(LayerContent.exp_order_complete)))
            
            
            #Perform export only for Layers which have at least 1 Shape to export
            if len(LayerContent.exp_order_complete):
                exstr+=self.commentprint("*** LAYER: %s ***" %(LayerContent.LayerName))
                
                #If tool has changed for this LayerContent, add it
                if LayerContent.tool_nr != previous_tool:
                    exstr+=self.chg_tool(LayerContent.tool_nr, LayerContent.speed)
                    previous_tool = LayerContent.tool_nr
            
                for shape_nr in LayerContent.exp_order_complete:
                    shape=LayerContent.shapes[shape_nr]
                    logger.debug(self.tr("Beginning export of  Shape Nr: %s") % shape.nr)
                    
                    exstr+=self.commentprint("* SHAPE Nr: %i *" %(shape.nr))
                    
                    exstr+=shape.Write_GCode(LayerContent=LayerContent,
                                             PostPro=self)

        #Move machine to the Final Position
        EndPosition=Point( x=g.config.vars.Plane_Coordinates['axis1_start_end'],
                           y=g.config.vars.Plane_Coordinates['axis2_start_end'])
        
        exstr += self.rap_pos_xy(EndPosition)  
        

        #Write the end G-Code at the end        
        exstr += self.write_gcode_en()
        
        """
        FIXME, Need to check this, don't know if it's correct here or not.
        """
        exstr=self.make_line_numbers(exstr)   
   
        #If the String shall be given to STDOUT
        if g.config.vars.General['write_to_stdout']:
            print(exstr)
            logger.info(self.tr("Export to STDOUT was successful"))
            self.close
    
        else:
            #Export Data to file
                try:
                    #Das File oeffnen und schreiben
                    #File open and write
                    f = open(save_filename, "w")
                    f.write(exstr)
                    f.close()
                    logger.info(self.tr("Export to FILE was successful"))    
                except IOError:
                    QtGui.QMessageBox.warning(g.window,self.tr("Warning during Export"),
                                              self.tr("Cannot Save the File"))
                   
            
    

    def initialize_export_vars(self):
        """
        This function is called to initialize all export variables. This will
        be done directly before the export starts.
        """
        
        #Initialization of the General Postprocessor parameters
        self.feed=0
        self.speed=0
        self.tool_nr=1
        self.comment=""
        
        self.abs_export=self.vars.General["abs_export"]
        
        self.Pe=Point( x=g.config.vars.Plane_Coordinates['axis1_start_end'],
                       y=g.config.vars.Plane_Coordinates['axis2_start_end'])

        self.Pa=Point( x=g.config.vars.Plane_Coordinates['axis1_start_end'],
                       y=g.config.vars.Plane_Coordinates['axis2_start_end'])

        self.lPe=Point( x=g.config.vars.Plane_Coordinates['axis1_start_end'],
                       y=g.config.vars.Plane_Coordinates['axis2_start_end'])
        
           
        self.IJ=Point( x=0.0,y=0.0)    
        self.O=Point( x=0.0,y=0.0)    
        self.r=0.0           
        self.a_ang=0.0      
        self.e_ang=0.0  
        
        self.ze=g.config.vars.Depth_Coordinates['axis3_retract']
        self.lz=self.ze
        
        self.keyvars={"%feed":'self.iprint(self.feed)',\
                   "%speed":'self.iprint(self.speed)',\
                   "%tool_nr":'self.iprint(self.tool_nr)',\
                   "%nl":'self.nlprint()',\
                   "%XE":'self.fnprint(self.Pe.x)',\
                   "%-XE":'self.fnprint(-self.Pe.x)',\
                   "%XA":'self.fnprint(self.Pa.x)',\
                   "%-XA":'self.fnprint(-self.Pa.x)',\
                   "%YE":'self.fnprint(self.Pe.y)',\
                   "%-YE":'self.fnprint(-self.Pe.y)',\
                   "%YA":'self.fnprint(self.Pa.y)',\
                   "%-YA":'self.fnprint(-self.Pa.y)',\
                   "%ZE":'self.fnprint(self.ze)',\
                   "%-ZE":'self.fnprint(-self.ze)',\
                   "%I":'self.fnprint(self.IJ.x)',\
                   "%-I":'self.fnprint(-self.IJ.x)',\
                   "%J":'self.fnprint(self.IJ.y)',\
                   "%-J":'self.fnprint(-self.IJ.y)',\
                   "%XO":'self.fnprint(self.O.x)',\
                   "%-XO":'self.fnprint(-self.O.x)',\
                   "%YO":'self.fnprint(self.O.y)',\
                   "%-YO":'self.fnprint(-self.O.y)',\
                   "%R":'self.fnprint(self.r)',\
                   "%AngA":'self.fnprint(degrees(self.a_ang))',\
                   "%-AngA":'self.fnprint(degrees(-self.a_ang))',\
                   "%AngE":'self.fnprint(degrees(self.e_ang))',\
                   "%-AngE":'self.fnprint(degrees(-self.e_ang))',\
                   "%comment":'self.sprint(self.comment)'}
        
    def write_gcode_be(self, load_filename):
        """
        Adding the begin to a new variable. If the exported file is from the
        type g-code in addition the dxf- filename, dxf2gcode version etc. is
        added to the code. Otherwise just the defined text in the PostProcessor
        file is added.
        @param load_filename: The name of the original dxf filename to append 
        it to the begin for information.
        @return: The Function returns the begin of the new string to be 
        exported.
        """
        if self.vars.General["output_type"] == 'g-code':
            exstr = self.tr("(Generated with: %s, Version: %s, Date: %s)\n") % (c.APPNAME, c.VERSION, c.DATE)
            exstr += self.tr("(Time: %s)\n") % time.asctime()
            exstr += self.tr("(Created from file: %s)\n") % load_filename
        elif self.vars.General["output_type"] == 'dxf':
            exstr = ''
            
        else:
            exstr = ''
                        
        exstr = (exstr.encode("utf-8"))
         
        # In addition the text defined in the PostProcessor Config file is 
        # added.
        exstr += ("%s\n" % self.vars.General["code_begin"])
        
        return exstr

    def write_gcode_en(self):
        """
        Return the text to be added at the end of the exported file.
        @return: The Function returns the string to be added.
        """
        return self.vars.General["code_end"]

    def make_line_numbers(self,exstr):
        """
        This Method checks if Line Numbers are required for the export and if 
        they are it adds them to the existing exstr.
        @param exstr: This is the string which shall be exported where the line 
        numbers are added.
        @return: It returns the string with line numbers added to it. 
        """
        use_line_nrs     = self.vars.Line_Numbers["use_line_nrs"]
        line_nrs_begin     = self.vars.Line_Numbers["line_nrs_begin"]
        line_nrs_step      = self.vars.Line_Numbers["line_nrs_step"]
        
        line_format = 'N%i ' 
        if use_line_nrs:
            nr = 0
            line_nr = line_nrs_begin
            exstr = ((line_format + '%s') % (line_nr, exstr))
            nr = self.string.find('\n', nr)
            while not(nr == -1):
                line_nr += line_nrs_step  
                exstr = (('%s' + line_format + '%s') % (self.string[0:nr + 1], \
                                                        line_nr, \
                                                        exstr[nr + 1:len(self.string)]))
                
                nr = exstr.find('\n', nr + len(((line_format) % line_nr)) + 2)
                          
        return exstr
            
    def chg_tool(self,tool_nr,speed):
        """
        This Method is called to change the tool.  It can change the tool or
        change the tool speed
        @param tool_nr: The tool_nr of the new tool
        @param speed: The speed for the tool
        """
        self.tool_nr=tool_nr
        self.speed=speed
        return self.make_print_str(self.vars.Program["tool_change"]) 
        
            
    def chg_feed_rate(self, feed):
        """
        This Method is called to change the feedrate
        @param feed: The new feedrate which shall be set
        @return: Returns the string which shall be added.
        """
        self.feed = feed
        return self.make_print_str(self.vars.Program["feed_change"]) 
        
    def set_cut_cor(self, cut_cor, Pe):
        """
        This function is called if the Cutter Correction is enabled.
        @param cut_cor=The new value of the cutter correction (41/42)
        @param Pe= This is a PointClass which gives the Endpoint
        """
        self.cut_cor = cut_cor

        if not(self.abs_export):
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        if cut_cor == 41:
            return self.make_print_str(self.vars.Program["cutter_comp_left"])
        elif cut_cor == 42:
            return self.make_print_str(self.vars.Program["cutter_comp_right"]) 

    def deactivate_cut_cor(self, Pe):
        """
        This function is called if the Cutter Correction is disabled.
        @param Pe= This is a PointClass which gives the Endpoint
        """
        if not(self.abs_export):
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe   
        return self.make_print_str(self.vars.Program["cutter_comp_off"])
            
    def lin_pol_arc(self, dir, Pa, Pe, a_ang, e_ang, R, O, IJ):
        """
        This function is called if an arc shall be cut.
        @param dir: The direction of the arc to be cut, can be cw or ccw
        @param Pa: The Start Point at which the Arc begins
        @param PE: The End Point at which the Arc is ended.
        @param a_ang: The angle at which the Startpoint Starts
        @param e_ang: The angle at which the Endpoint Ends
        @param R: The Radius or the Arc
        @param O: The Center of the Arc
        @param IJ: The distance to from Center to Start Point.
        """
        self.O = O
        self.IJ = IJ
        
        self.a_ang = a_ang
        self.e_ang = e_ang
        
        self.Pa = Pa
        self.r = R
        
        if not(self.abs_export):
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        if dir == 'cw':
            return self.make_print_str(self.vars.Program["arc_int_cw"])
        else:
            return self.make_print_str(self.vars.Program["arc_int_ccw"])

          
    def rap_pos_z(self, z_pos):
        """
        Code to be added if the machine shall be rapidly commanded to a new 
        3rd Axis Position.
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        if not(self.abs_export):
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos

        return self.make_print_str(self.vars.Program["rap_pos_depth"])        
         
    def rap_pos_xy(self, Pe):
        """
        Code to be added if the machine shall be rapidly commanded to a new 
        XY Plane Position.
        @param Pe: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        
        if not(self.abs_export):
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        return self.make_print_str(self.vars.Program["rap_pos_plane"])               
    
    def lin_pol_z(self, z_pos):
        """
        Code to be added if the machine shall be commanded to a new 
        3rd Axis Position.
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        if not(self.abs_export):
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos
            
        return self.make_print_str(self.vars.Program["lin_mov_depth"])   
        
    def lin_pol_xy(self, Pa, Pe):
        """
        Code to be added if the machine shall be rapidly commanded to a new 
        XY Plane Position.
        @param Pe: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        self.Pa = Pa
        if not(self.abs_export):
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        return self.make_print_str(self.vars.Program["lin_mov_plane"])   
    
    
    def write_pre_shape_cut(self):
        """
        Return the text to be added before a shape.
        @return: The Function returns the string to be added.
        """
        return self.make_print_str(self.vars.Program["pre_shape_cut"])
    
    def write_post_shape_cut(self):
        """
        Return the text to be added post a shape.
        @return: The Function returns the string to be added.
        """
        return self.make_print_str(self.vars.Program["post_shape_cut"])
    
    def commentprint(self,comment):
        """
        This function is called to print a comment.
        @return: Returns the comment 
        """
        self.comment=comment
        return self.make_print_str(self.vars.Program["comment"])   

    def make_print_str(self, keystr):
        """
        This is the main function which converts the Keyvalues given in the
        Postprocessor Configuration into the values.
        @param keystr: This is the string in which all keywords shall be 
        replaced by the variables etc.
        @return: Returns the string with replaced keyvars (e.g. %Z is replaced
        by the real Z value in the defined Number Format.
        """
        
        exstr = keystr
        for key_nr in range(len(self.keyvars.keys())):
            exstr = exstr.replace(self.keyvars.keys()[key_nr], \
                                  eval(self.keyvars.values()[key_nr]))
        return exstr

    #Funktion welche den Wert als formatierter integer zurueck gibt
    #Function which returns the given value as a formatted integer
    def iprint(self, interger):
        """
        This method is called to return a integer formatted as an string
        @param integer: The integer values which shall be returned as a string
        @return: The formatted integer as a string.
        """
        return ('%i' % interger)
    
    def sprint(self, string):
        """
        This method is called to return a string formatted as an string
        @param integer: The integer values which shall be returned as a string
        @return: The formatted integer as a string.
        """
        return ('%s' % string)

    
    
    def nlprint(self):
        """
        This function is used to generate a new line.
        @return: Returns the character set required to get a new line 
        """
        return '\n'
    
    def fnprint(self, number):
        """
        This function returns the given real values in the defined format. The
        format which shall be returned is defined in the postprocessor file.
        @param number: The number which shall be returned in a formatted string
        @return: The formatted string of the number.
        """
        
        pre_dec     = self.vars.Number_Format["pre_decimals"]
        post_dec    = self.vars.Number_Format["post_decimals"]
        dec_sep     = self.vars.Number_Format["decimal_seperator"]
        pre_dec_z_pad=self.vars.Number_Format["pre_decimal_zero_padding"]
        post_dec_z_pad=self.vars.Number_Format["post_decimal_zero_padding"]
        signed_val=self.vars.Number_Format["signed_values"]
        
        exstr = ''
        
        #+ or - sign if required. Also used for Leading Zeros
        if (signed_val)and(pre_dec_z_pad):
            numstr = (('%+0' + str(pre_dec + post_dec + 1) + \
                     '.' + str(post_dec) + 'f') % number)
        elif (signed_val == 0)and(pre_dec_z_pad):
            numstr = (('%0' + str(pre_dec + post_dec + 1) + \
                    '.' + str(post_dec) + 'f') % number)
        elif (signed_val)and(pre_dec_z_pad == 0):
            numstr = (('%+' + str(pre_dec + post_dec + 1) + \
                    '.' + str(post_dec) + 'f') % number)
        elif (signed_val == 0)and(pre_dec_z_pad == 0):
            numstr = (('%' + str(pre_dec + post_dec + 1) + \
                    '.' + str(post_dec) + 'f') % number)
            
        #Gives the required decimal format.           
        exstr += numstr[0:-(post_dec + 1)]
        
        exstr_end = dec_sep
        exstr_end += numstr[-(post_dec):]

        #Add's Zero's to the end if required
        if post_dec_z_pad == 0:
            while (len(exstr_end) > 0)and((exstr_end[-1] == '0')or(exstr_end[-1] == self.dec_sep)):
                exstr_end = exstr_end[0:-1]                
        return exstr + exstr_end
    
#    def __str__(self):
#
#        str = ''
#        for section in self.parser.sections(): 
#            str = str + "\nSection: " + section 
#            for option in self.parser.options(section): 
#                str = str + "\n   -> %s=%s" % (option, self.parser.get(section, option))
#        return str

