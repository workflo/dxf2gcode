#! /usr/bin/env python

##    hittest Copyright  (C)  2007 Donn.C.Ingle
##
##    Contact: donn.ingle@gmail.com - I hope this email lasts.
##
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##     ( at your option )  any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##

import pygtk
#pygtk.require('2.0')
import gtk
import gobject
import cairo
from gtk import gdk

# Create a GTK+ widget on which we will draw using Cairo
class Screen(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }

    def __init__(self):
        super(Screen,self).__init__()
        # gtk.Widget signals
        self.connect("button_press_event", self.button_press)
        self.connect("button_release_event", self.button_release)
        self.connect("motion_notify_event", self.motion_notify)
        # More GTK voodoo : unmask events
        self.add_events(gdk.BUTTON_PRESS_MASK |
                        gdk.BUTTON_RELEASE_MASK |
                        gdk.POINTER_MOTION_MASK)

    # Handle the expose-event by drawing
    def do_expose_event(self, event):

        # Create the cairo context
        cr = self.window.cairo_create()
        self.hitpath = None #Is set later

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())

    def makeHitPath(self,cairopath):
        ## Make a simpler list of tuples

        ##        Internally, a cairo path looks like this:
        ##        (0, (10.0, 10.0))
        ##        (1, (60.0, 10.0))
        ##        (1, (60.0, 60.0))
        ##        (1, (35.0, 60.0))
        ##        (1, (35.0, 35.0))
        ##        (1, (10.0, 35.0))
        ##        (1, (10.0, 60.0))
        ##        (1, (-40.0, 60.0))
        ##        (3, ()) #want to ignore this one
        ##        (0, (10.0, 10.0))        

        self.hitpath = []
        for sub in cairopath:
            if sub[1]: #kick out the close path () empty tuple
                self.hitpath.append(sub[1]) #list of tuples

    def draw(self, cr, width, height):
        # Fill the background with gray
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()

    def hitTest(self,*p):
        ## Code lifted from http://local.wasp.uwa.edu.au/~pbourke/geometry/insidepoly/
        ## converted to Python. I won't pretend I grok it at all, just glad it works!
        ## Not sure how well it works yet, it might have edge flaws.
        px = p[0]
        py = p[1]
        counter = i = xinters = 0
        p1 = p2 = ()

        p1 = self.hitpath[0]
        N = len(self.hitpath)

        # Mathemagic loop-de-loop
        for i in range(0,N):
            p2 = self.hitpath[i % N]
            if py > min( p1[1] , p2[1] ):
                if py <= max( p1[1], p2[1] ):
                    if px <= max( p1[0], p2[0] ):
                        if p1[1] != p2[1]:
                            xinters = ( py - p1[1] ) * ( p2[0] - p1[0] ) / ( p2[1] - p1[1] ) + p1[0]
                            if p1[0] == p2[0] or px <= xinters: counter += 1
            p1 = p2

        if counter % 2 == 0:
            return "outside"
        return "inside"

    def button_press(self,widget,event):
        pass
    def button_release(self,widget,event):
        pass
    def motion_notify(self,widget,event):
        pass

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(Widget):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    widget = Widget()
    widget.show()
    window.add(widget)
    window.present()
    gtk.main()

class Shapes(Screen):
    #Override the press event
    def button_press(self,widget,event):
        print self.hitTest(event.x, event.y)

    def draw(self, cr, width, height):
        x = y = 10
        sx = sy = 50
        cr.move_to(x,y)
        cr.line_to(x+sx,y)
        cr.line_to(x+sx,y+sy)
        cr.line_to(x+(sx/2),y+sy)
        cr.line_to(x+(sx/2),y+(sy/2))
        cr.line_to(x,y+(sy/2))
        cr.line_to(x,y+sy)
        cr.line_to(x-sx,y+sy)
        cr.close_path()
        cr.set_source_rgb(1,0,0)

        self.makeHitPath(cr.copy_path_flat()) #record the path to use as a hit area.

        cr.fill() #consumes the path, so get it before the fill


run(Shapes)
