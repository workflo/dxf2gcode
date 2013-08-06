#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#travelling_salesman_problem_1.py
#Programmer: Christian Kohloeffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohlöffel

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.numerix import arange, sin, pi
from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT,GROOVE
from Tkinter import Tk, Button, Frame
import sys


#Lines Class
class ClassLines:
    def __init__(self,num=None,lines=[]):
        self.num=num
        self.lines=lines

    def random_lines(self,num=5,max_pos=10,max_len=5):
        self.num=num
        for nr in range(self.num):
            self.lines.append(ClassLine())
            self.lines[-1].random_line(max_pos,max_len)
            
    def __str__(self):
        string=("\nLine count: %0.0f " % (self.num))
        for line in self.lines:
            string+=str(line)
        return string
        
#Line Class      
class ClassLine:
    def __init__(self,beg=None,end=None,lenght=0):
        self.beg=beg
        self.end=end
        self.lenght=lenght
        
    def random_line(self,max_pos=10,max_len=5):
        self.beg=ClassPoint()
        self.beg.random_stpoint(max_pos)
        self.end=ClassPoint()
        self.end.random_enpoint(self.beg,max_len)
        self.calc_length()
        
    def calc_length(self):
        from math import sqrt
        self.lenght=sqrt((self.beg.x-self.end.x)**2+(self.beg.y-self.end.y)**2)

    def plot_line(self,plot=[],style='-b'):
        hdl=plot.plot([self.beg.x,self.end.x],[self.beg.y,self.end.y],style)

    def add_text(self,plot=[],string='String'):
        plot.text (self.beg.x+0.1,self.beg.y+0.1,string,fontsize=8)
        
    def __str__(self):
        return ("\nLine Beg: %s; End: %s; Lenght %2.2f" % (self.beg,self.end,self.lenght))

#Point Class
class ClassPoint:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
        
    def random_stpoint(self,max_pos=10):
        from random import random
        self.x=random()*max_pos
        self.y=random()*max_pos
        
    def random_enpoint(self,start=None,max_len=5):
        from random import random
        self.x=start.x+(-0.5+random())*2*max_len
        self.y=start.y+(-0.5+random())*2*max_len
        
    def distance(self,other):
        from math import sqrt
        return sqrt((self.x-other.x)**2+(self.y-other.y)**2)
    
    def __str__(self):
        return ("X: %5.2f Y: %5.2f" % (self.x,self.y))

#Distance Matrix Class
class ClassDistanceMatrix:
    def __init__(self,matrix=[],size=[0,0]):
        self.matrix=matrix
        
    def generate_matrix(self,Lines):
        from copy import copy
        x_vals=range(Lines.num);
        self.matrix=[]
        for nr_y in range(Lines.num):
            for nr_x in range(Lines.num):
                x_vals[nr_x]=Lines.lines[nr_y].end.distance(Lines.lines[nr_x].beg)
            self.matrix.append(copy(x_vals[:]))
        self.size=[Lines.num,Lines.num]
        
    def __str__(self):
        string=("Distance Matrix; size: %i X %i" %(self.size[0],self.size[1]))
        for line_x in self.matrix:
            string+="\n"
            for x_vals in line_x:
                string+=("%8.2f" %x_vals)
        return string

#Population Class
class ClassPopulation:
    def __init__(self,pop=[],rot=[],order=[],size=[0,0],mutate_rate=0.95):
        self.pop=pop
        self.rot=rot
        self.size=size
        self.mutate_rate=mutate_rate
        
    def ini_random_pop(self,size=[5,8],dmatrix=[]):
        from random import random
        from math import floor
        from copy import copy

        self.size=size
        self.pop=[]
        for pop_nr in range(size[1]):
            tour=[]
            tour.append(int(floor(random()*len(dmatrix[0]))))
            for tp_nr in range(len(dmatrix[0])-1):
                tour.append(self.heurestic_find_next(tour,dmatrix))
            self.pop.append(tour[:])
                
        for rot_nr in range(size[0] ):
            self.rot.append(0)  
            
    def heurestic_find_next(self,tour=[],dmatrix=[]):
        #Auswahl der Entfernungen des nächsten Punkts
        min_dist=1e99
        min_point=0
        darray=dmatrix[tour[-1]]
        
        for pnr in range(len(darray)):
            if not(pnr in tour):
                if (darray[pnr]<min_dist):
                    min_point=pnr
                    min_dist=darray[pnr]
        return min_point

    def genetic_algorithm(self,Result=[],mutate_rate=0.95):
        from random import random, shuffle
        from math import floor

        self.mutate_rate=mutate_rate        

        #Neue Population Matrix erstellen
        new_pop=[]
        for p_nr in range(self.size[1]):
            new_pop.append([])

        #Tournament Selection 1 between Parents (2 Parents remaining)
        ts_r1=range(self.size[1])
        shuffle(ts_r1)        
        winners_r1=[]
        tmp_fittness=[]
        for nr in range(self.size[1]/2):
            if Result.cur_fittness[ts_r1[nr*2]]\
               <Result.cur_fittness[ts_r1[(nr*2)+1]]:
                winners_r1.append(self.pop[ts_r1[nr*2]])
                tmp_fittness.append(Result.cur_fittness[ts_r1[nr*2]])
            else:
                winners_r1.append(self.pop[ts_r1[(nr*2)+1]])
                tmp_fittness.append(Result.cur_fittness[ts_r1[(nr*2)+1]])
        #print tmp_fittness

        #Tournament Selection 2 only one Parent remaining
        ts_r2=range(self.size[1]/2)
        shuffle(ts_r2)
        for nr in range(self.size[1]/4):
            if tmp_fittness[ts_r2[nr*2]]\
               <tmp_fittness[ts_r2[(nr*2)+1]]:
                winner=winners_r1[ts_r2[nr*2]]
            else:
                winner=winners_r1[ts_r2[(nr*2)+1]]
                
            #Schreiben der Gewinner in die neue Population Matrix
            #print winner
            for pnr in range(2):
                new_pop[pnr*self.size[1]/2+nr]=winner[:]

        
        #Crossover Gens from 2 Parents
        crossover=range(self.size[1]/2)
        shuffle(crossover)
        for nr in range(self.size[1]/4):
            #Parents sind die Gewinner der ersten Runde (Gentische Selektion!?)
            #child=parent2
            parent1=winners_r1[crossover[nr*2]][:]
            child=winners_r1[crossover[(nr*2)+1]][:]

            #Die Genreihe die im Kind vom parent1 ausgetauscht wird          
            indx=[int(floor(random()*self.size[0])),int(floor(random()*self.size[0]))]
            indx.sort()
            while indx[0]==indx[1]:
                indx=[int(floor(random()*self.size[0])),int(floor(random()*self.size[0]))]
                indx.sort()        
            gens=parent1[indx[0]:indx[1]+1]

            #Entfernen der auszutauschenden Gene
            for gen in gens:
                child.pop(child.index(gen))

            #Einfügen der neuen Gene an einer Random Position
            ins_indx=int(floor(random()*self.size[0]))
            new_children=child[0:ins_indx]+gens+child[ins_indx:len(child)]
            
            #Schreiben der neuen Kinder in die neue Population Matrix
            for pnr in range(2):
                new_pop[int((pnr+0.5)*self.size[1]/2+nr)]=new_children[:]
 
        #Mutieren der 2.ten Hälfte der Population Matrix
        mutate=range(self.size[1]/2)
        shuffle(mutate)
        num_mutations=int(round(mutate_rate*self.size[1]/2))
        for nr in range(num_mutations):
            #Die Genreihe die im Kind vom parent1 ausgetauscht wird          
            indx=[int(floor(random()*self.size[0])),int(floor(random()*self.size[0]))]
            indx.sort()
            while indx[0]==indx[1]:
                indx=[int(floor(random()*self.size[0])),int(floor(random()*self.size[0]))]
                indx.sort()
                
            #Zu mutierende Line
            mutline=new_pop[self.size[1]/2+mutate[nr]]
            if random() < 0.75: #Gen Abschnitt umdrehen
                cut=mutline[indx[0]:indx[1]+1]
                cut.reverse()
                mutline=mutline[0:indx[0]]+cut+mutline[indx[1]+1:len(mutline)]
            else: #2 Gene tauschen
                orgline=mutline[:]
                mutline[indx[0]]=orgline[indx[1]]
                mutline[indx[1]]=orgline[indx[0]]
            new_pop[self.size[1]/2+mutate[nr]]=mutline


        #Zuweisen der neuen Populationsmatrix            
        self.pop=new_pop

    def __str__(self):
        string=("\nPopulation size: %i X %i \nMutate rate: %0.2f \nRotation Matrix:\n%s \nPop Matrix:" \
                %(self.size[0],self.size[1],self.mutate_rate,self.rot))

        for line in self.pop:
            string+='\n'+str(line)
        return string
            
class ClassFittness:
    def __init__(self,population=[],cur_fittness=[],best_fittness=[],best_route=[]):
        self.population=population
        self.cur_fittness=cur_fittness
        self.best_fittness=best_fittness
        self.best_route=best_route

    def calc_cur_fittness(self,matrix):
        for pop_nr in range(len(self.population.pop)):
            pop=self.population.pop[pop_nr]

            dis=matrix[pop[-1]][pop[0]]
            for nr in range(1,len(pop)):
                dis+=matrix[pop[nr-1]][pop[nr]]
            self.cur_fittness[pop_nr]=dis
            
        
    #Erste Möglichkeite um die Reihenfolge festzulegen (Straffunktion=Passiv)   
    def calc_constrain_fittness(self):
        for pop_nr in range(len(self.population.pop)):
            pop=self.population.pop[pop_nr]
            order_index=[]
            for val_nr in range(len(self.order)):
                oorder_index=self.get_pop_index_list(self.population.pop[pop_nr])
                if val_nr>0:
                    if order_index[-2]>order_index[-1]:
                        self.cur_fittness[pop_nr]=self.cur_fittness[pop_nr]*2
                        
    #2te Möglichkeit die Reihenfolge festzulegen (Korrekturfunktion=Aktiv)                
    def correct_constrain_order(self):
        for pop_nr in range(len(self.population.pop)):
            #Suchen der momentanen Reihenfolge
            order_index=self.get_pop_index_list(self.population.pop[pop_nr])
            #Momentane Reihenfolge der indexe sortieren
            order_index.sort()
            #Indexe nach soll Reihenfolge korrigieren
            for ind_nr in range(len(order_index)):
                self.population.pop[pop_nr][order_index[ind_nr]]=self.order[ind_nr]

    def get_pop_index_list(self,pop):
        pop_index_list=[]
        for val_nr in range(len(self.order)):
            pop_index_list.append(pop.index(self.order[val_nr]))
        return pop_index_list

    def select_best_fittness(self):      
        self.best_fittness.append(min(self.cur_fittness))
        self.best_route=self.cur_fittness.index(self.best_fittness[-1])
 
    def __str__(self):
        return ("\nBest Fittness: %s \nBest Route: %s \nBest Pop: %s" \
                %(self.best_fittness[-1],self.best_route,self.population.pop[self.best_route]))
          
class ClassPlotFigure:
    def __init__(self,master=None,iter=None):
        
        self.master=master
        self.iter=iter

        self.frame_o=Frame(height=50,relief = GROOVE,bd = 2)
        self.frame_o.pack(fill=BOTH, expand=1)

        self.but_update_plot=Button(master=self.frame_o,text='Start Animation',command=self.iter.start_animation)
        self.but_update_plot.pack(fill=BOTH,expand=1)
        
        self.figure = Figure(figsize=(6,7), dpi=100)
        
        # a tk.DrawingArea
        self.frame_c=Frame(relief = GROOVE,bd = 2)
        self.frame_c.pack(fill=BOTH, expand=1,)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_c)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_c)
        self.toolbar.update()
        self.canvas._tkcanvas.pack( fill=BOTH, expand=1)
        self.ini_plot()
     
    def ini_plot(self):
        self.plot1 = self.figure.add_subplot(211)
        self.plot1.set_title("Number of Lines: " +str(self.iter.Lines.num))

        self.plot2=self.figure.add_subplot(212)
        self.plot2.set_title(('Best Tour length: %0.1f ' %(self.iter.Fittness.best_fittness[-1])))
        self.plot2.set_xlabel('Interation')
        self.plot2.set_ylabel('Tour Lenght')        

        nr=0
        self.plot1.hold(True)
        for line in self.iter.Lines.lines:
            line.plot_line(self.plot1,'-ro')
            line.add_text(self.plot1,str(nr))
            nr+=1

        self.lines1=[]
        con_lines=self.gen_plot_route()
        for line in con_lines:
            line.plot_line(self.plot1,'-b')

        best_fittness=self.iter.Fittness.best_fittness
        self.line2=self.plot2.plot(range(len(best_fittness)),best_fittness,'r-')
        self.plot2.set_ylim(0,best_fittness[0]+5)
        self.canvas.show()


    def update_plot(self):
        con_lines=self.gen_plot_route()
        lines=self.plot1.get_lines()
        
        for line_nr in range(self.iter.Lines.num,len(lines)):
            cline_nr=line_nr-self.iter.Lines.num-1
            lines[line_nr].set_xdata([con_lines[cline_nr].beg.x,con_lines[cline_nr].end.x])
            lines[line_nr].set_ydata([con_lines[cline_nr].beg.y,con_lines[cline_nr].end.y])

        best_fittness=self.iter.Fittness.best_fittness
        self.line2[0].set_xdata(range(len(best_fittness)))
        self.line2[0].set_ydata(best_fittness)
        self.plot2.set_title(('Best Tour length: %0.1f ' %(self.iter.Fittness.best_fittness[-1])))
        self.plot2.set_xlim(0,len(best_fittness))
        self.canvas.show()

    def gen_plot_route(self):
        best_pop=self.iter.Population.pop[self.iter.Fittness.best_route]
        lines=self.iter.Lines.lines

        con_lines=[]
        con_lines.append(ClassLine())
        con_lines[-1].beg=lines[best_pop[-1]].end
        con_lines[-1].end=lines[best_pop[0]].beg

        for nr in range(1,len(best_pop)):
            con_lines.append(ClassLine())
            con_lines[-1].beg=lines[best_pop[nr-1]].end
            con_lines[-1].end=lines[best_pop[nr]].beg

        return con_lines        
 
    def quit(self):
        sys.exit()
        self.quit()
        self.destroy()
        

class ClassIteration:
    def __init__(self,master=None):
        from math import ceil
        
        self.line_nrs=40
        self.iterations=int(self.line_nrs*50)
        self.line_max_pos=10
        self.line_max_len=4
        self.pop_nr=int(ceil(self.line_nrs/10)*4)

        self.mutate_rate=0.95
        self.order=[]#[7,14,4,12,5,34,23]
 
        #Creating Lines    
        self.Lines=ClassLines()
        self.Lines.random_lines(num=self.line_nrs,max_pos=self.line_max_pos,max_len=self.line_max_len)

        #Generating the Distance Matrix
        self.DistanceMatrix=ClassDistanceMatrix()
        self.DistanceMatrix.generate_matrix(self.Lines)

        #Generation Population 
        self.Population=ClassPopulation()
        self.Population.ini_random_pop(size=[self.line_nrs,self.pop_nr],dmatrix=self.DistanceMatrix.matrix)

        #Initialisieren der Result Class
        self.Fittness=ClassFittness(population=self.Population,cur_fittness=range(self.Population.size[1]))
        self.Fittness.order=self.order

        #Korrektur Funktion um die Reihenfolge der Elemente zu korrigieren
        self.Fittness.correct_constrain_order()
        
        #Erstellen der ersten Ergebnisse
        self.Fittness.calc_cur_fittness(self.DistanceMatrix.matrix)
        self.Fittness.select_best_fittness()

        #Initialisieren des Plots
        self.plot=ClassPlotFigure(master,self)

    def start_animation(self):
        for nr in range(self.iterations):
            self.calc_next_iteration()

            if ((nr)%(self.iterations/20))==0:
                self.plot.update_plot()
        print self
        print self.Fittness
                
    def calc_next_iteration(self):
        #Algorithmus ausfürhen
        self.Population.genetic_algorithm(Result=self.Fittness,mutate_rate=self.mutate_rate)
        #Korrektur Funktion um die Reihenfolge der Elemente zu korrigieren
        self.Fittness.correct_constrain_order()
        #Fittness der jeweiligen Routen ausrechen
        self.Fittness.calc_cur_fittness(self.DistanceMatrix.matrix)
        #Straffunktion falls die Route nicht der gewünschten Reihenfolge entspricht
        #self.Fittness.calc_constrain_fittness(self.Population)
        #Beste Route auswählen
        self.Fittness.select_best_fittness()

    def __str__(self):
        res=self.Population.pop
        return ("iterations:    %i" %self.iterations) +\
               ("\nline_nrs:      %i" %self.line_nrs) +\
               ("\nline_max_pos:  %i" %self.line_max_pos) +\
               ("\nline_max_len:  %i" %self.line_max_len) +\
               ("\npop_nr:        %i" %self.pop_nr) +\
               ("\nmutate_rate:   %0.2f" %self.mutate_rate) +\
               ("\norder:          %s" %self.order)
    
master = Tk()
master.title("Genetic Algorithm in Python")
#import profile     
#profile.run('ClassPlotFigure(master)',sort='cumulative')
ClassIteration(master)
master.mainloop()

 
