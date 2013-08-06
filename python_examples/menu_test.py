'''
dynamic cascaded submenus

Created on 25.11.2009

@author: mah
'''

from Tkinter import *
import pprint 

# http://www.astro.washington.edu/users/rowen/TkinterSummary.html#CallbackShims
class SimpleCallback:
    """Create a callback shim. Based on code by Scott David Daniels
    (which also handles keyword arguments).
    """
    def __init__(self, callback, *firstArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs
    
    def __call__(self, *args):
        return self.__callback (*(self.__firstArgs + args))


def apply_export(inst):
    print "export ",inst

def apply_delete(inst):
    if inst in instances:
        instances.remove(inst)
        rebuild_menu()
        print "delete ",inst
    
def add_instance(tag):
    global counter
    counter += 1
    name = "%s-%d" %(tag,counter)
    print "add %s" % (name)
    instances.append(name)
    rebuild_menu()


def rebuild_menu():

    dyn_menu = Menu(menu)
    dyn_menu.add_command(label="single entry")
    dyn_menu.add_separator()
    print instances
    print dir(menu)
    print dir(Menu)
    for i in range(len(instances)):
        print i
        name = instances[i]
        sm= Menu(dyn_menu)
        sm.add_command(label = "export shape with %s" %(name),command=SimpleCallback(apply_export,name))
        sm.add_command(label = "close %s" %(name),command=SimpleCallback(apply_delete,name))
        dyn_menu.add_cascade(label=name,menu=sm)
    menu.entryconfigure(3,label="Apply", menu=dyn_menu)

def dump(arg):
    print "instances:"
    pp.pprint(instances)


pp = pprint.PrettyPrinter(indent=4)


counter = 0
entries = ['good','bad','ugly']
dyn_menu = None
instances = []

root=Tk() 
menu = Menu(root)
root.config(menu=menu)

list_menu = Menu(menu) 
list_menu.add_command(label="show instances",command=SimpleCallback(dump,1))
menu.add_cascade(label="Dump", menu=list_menu)


create_menu = Menu(menu) 
for k in entries:
    create_menu.add_command(label=k,command=SimpleCallback(add_instance,k))
menu.add_cascade(label="Create", menu=create_menu)

menu.add_cascade(label="Apply")
menu.entryconfigure(3,label="Sowas", menu=dyn_menu)
#rebuild_menu()
root.mainloop() 
