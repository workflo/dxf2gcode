# -*- coding: ISO-8859-1 -*-
from Point import PointClass
from base_geometries import  LineGeo, ArcGeo 
from bounding_box import BoundingBoxClass
from shape import ShapeClass

from copy import deepcopy 
from math import sin, cos, atan2, sqrt, pow, pi, degrees

# based on an article of X.-Z Liu et al. /Computer in Industry 58(2007)
#
# WED 20.4.09

DEBUG = 1        
        
class ShapeOffsetClass:
    """ 
    Main Class to do the Cutter Compensation for a shape. It produces the 
    Offset curve defined by radius and direction.
    """
    def __init__(self, tol=0.01):
        """ 
        Standard method to initialize the class
        """ 
        self.tol = 0.01
        self.shape=ShapeClass()
        self.pretshape = ShapeClass()
        self.radius = 10
        self.dir = 42
        
    def do_compensation(self, shape=None, radius=10, direction=41, shape_nr=1):
        """ 
        Does the Cutter Compensation for the given Shape
        @param shape: The shape which shall be used for cutter correction
        @param radius: The offset to be used for correction
        @param direction: The Direction of compensation 41 for left and 42 for right
        """ 
        self.shape = shape
        self.radius = radius
        self.dir = direction
        self.shape_nr=shape_nr
        
        joinedshape=self.joinshapepoints(self.shape)
        
        #Pretreatment of the shapes to have no LSIP
        self.pretshape = self.pretreatment(joinedshape)      
        rawoffshape = self.make_raw_offsett(self.pretshape)
        untroffshape = self.make_untrimmed_offset(rawoffshape)
        clippedshapes = self.do_clipping(untroffshape)
        
        return clippedshapes
        #return [untroffshape]
        
    def joinshapepoints(self,shape):
        """ 
        The pretreatment searches for local self intersection points (LSIP) 
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        
        If Local self intersections exist the Elements will be split into new
        elements at their intersection Point.
        """ 

        joinedshape = ShapeClass(parent=shape.parent,
                           cut_cor=40,
                           nr=shape.nr,
                           closed=shape.closed,
                           plotoption=0,
                           geos=[],
                           geos_hdls=[])
        
        joinedshape.BB = shape.BB
        
        for geo in shape.geos:
            #Generate new Geometry copied from previous one
            if geo==shape.geos[0]:
                Pa=geo.Pa
                Pe=geo.Pe
            elif geo==shape.geos[-1] and shape.closed:
                Pa=joinedshape.geos[-1].Pe
                Pe=joinedshape.geos[0].Pa 
            else:
                Pa=joinedshape.geos[-1].Pe
                Pe=geo.Pe
                
            if geo.type == "LineGeo" or geo.type == "CCLineGeo":
                ccgeo=CCLineGeo(Pa=Pa,Pe=Pe)
            else:
                ccgeo=CCArcGeo(Pa=Pa, Pe=Pe, r=geo.r, O=geo.O,
                               direction=geo.ext)
            joinedshape.geos.append(ccgeo)
        
        return joinedshape

    def pretreatment(self, joinedshape):
        """ 
        The pretreatment searches for local self intersection points (LSIP) 
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        
        If Local self intersections exist the Elements will be split into new
        elements at their intersection Point.
        """ 

        pretshape = ShapeClass(parent=joinedshape.parent,
                           cut_cor=40,
                           nr=joinedshape.nr,
                           closed=joinedshape.closed,
                           plotoption=0,
                           geos=[],
                           geos_hdls=[])
        
        pretshape.BB = joinedshape.BB
        
        #Do for all Geometries -1 (if closed for all)
        for geo_nr in range(len(joinedshape.geos)+\
                            (joinedshape.closed)):

            #If there are more then one geometries find self intersection 
            #geometries 
            if geo_nr<len(joinedshape.geos):
                pretshape.geos += [joinedshape.geos[geo_nr]] 
            if geo_nr>=1:
                
                #Difference for normal shape and if it is the last shape
                if not(geo_nr==len(joinedshape.geos)):
                    geo1=pretshape.geos[-2]
                    geo2=pretshape.geos[-1]
                else:
                    geo1=pretshape.geos[-1]
                    geo2=pretshape.geos[0]
                
                #An intersection may only occur if the Bounding Boxes have an
                #intersection too
                intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
                    
                if intersect:
                    points = geo1.find_inter_points(geo2, tol=self.tol)
                    #Check if the Point is in tolerance with the last Point of geo1
                    #If not it is a Local Self Intersecting Point per Definition 2 
                    #and the element has to be separated into 2 elements. this will
                    #result in a not self intersecting element. 
                               
                    for Point in points:
                        #print geo1
                        #print geo2
                        #print Point
                        #There can be only one Local Self Intersection Point.
                        if Point.isTIP(geo1, self.tol, 'inside'):
                            
                            if not(geo_nr==len(self.shape.geos)):
                                pretshape.geos.pop()
                            pretshape.geos.pop()
                            pretshape.geos += geo1.split_into_2geos(Point)
                            if not(geo_nr==len(self.shape.geos)):
                                pretshape.geos += [geo2]
                                            
        return pretshape 
        
    def make_raw_offsett(self, pretshape):
        """ 
        Generates the raw offset curves of the pretreated shape, which has no
        local self intersections. 
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        @param pretshape: The pretreated shape with not LSIP.
        @return: Returns the raw offset shape which is not trimmed or joined.
        """ 
        
        rawoffshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           closed=self.shape.closed,
                           plotoption=0,
                           geos=[],
                           geos_hdls=[])
        
        rawoffshape.BB = self.shape.BB
        
        for geo in pretshape.geos:
            rawoffshape.geos+=geo.rawoffset(radius=self.radius,
                                            direction=self.dir)  
        return rawoffshape
   
    def make_untrimmed_offset(self, rawoffshape):
        """ 
        The untrimmed offset shape is generated according to para 3.2. It 
        searches the intersection points and dependent on the type of 
        intersection it used the rules for trimming and joining.
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        @param rawoffshape: The untrimmed / unjoined offset shape
        @return: Returns the joined untrimmed offset shape.
        """  
    
        untroffshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           plotoption=1,
                           closed=self.shape.closed,
                           geos=[],
                           geos_hdls=[])
         
        #Return nothing if there is no geo in shape
        if len(rawoffshape.geos)==0:
            return untroffshape
        
        newPa = deepcopy(rawoffshape.geos[0].Pa)
        
        #Loop for all geometries in the shape
        for geo_nr in range(1, len(rawoffshape.geos)):
            geo1 = rawoffshape.geos[geo_nr - 1]
            #If the for loop is at the last geometry the first one is the 2nd
            if len(rawoffshape.geos) <= 1:
                break
            geo2 = rawoffshape.geos[geo_nr]
            
            orgPe=self.pretshape.geos[geo_nr-1].Pe #DAS STIMMT NICHT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DA BRAUCH IHC DIE ORGINA KURVE
            #THE WRONG !!!! INCE THE ORIGINAL HOT I CURVE !!! ???
           
            #Call the trim join algorithms for the elements.
            untroffshape.geos += geo1.trim_join(geo2, newPa,
                                                 orgPe, self.tol)
            
            if len(untroffshape.geos):
                newPa = untroffshape.geos[-1].Pe
        
        #Add the last geometry Case 3 according to para 3.2
        if len(rawoffshape.geos)==1:
            untroffshape.geos.append(rawoffshape.geos[0])
            return untroffshape
        if len(untroffshape.geos)==0:
            return untroffshape
        else:
            if not(untroffshape.closed):
                if geo2.type=='CCLineGeo':
                    untroffshape.geos.append(CCLineGeo(newPa,deepcopy(geo2.Pe)))
                else:
                    untroffshape.geos.append(CCArcGeo(Pa=newPa,
                                                      Pe=deepcopy(geo2.Pe),
                                                    O=geo2.O, 
                                                    r=geo2.r,
                                                    direction=geo2.ext))
            else:
                geo1 = rawoffshape.geos[-1]
                geo2 = rawoffshape.geos[0]
                
                orgPe=geo1.Pe
                #Call the trim join algorithms for the elements.
                untroffshape.geos += geo1.trim_join(geo2, newPa, 
                                                    orgPe, self.tol)
                if geo2.type=='CCLineGeo':
                    untroffshape.geos[0].Pa=untroffshape.geos[-1].Pe
                    untroffshape.geos[0].calc_bounding_box()
                    
                else:
                    modgeo=untroffshape.geos[0]
                    modgeo.Pa=untroffshape.geos[-1].Pe
                    modgeo.s_ang = modgeo.O.norm_angle(modgeo.Pa)
                    modgeo.ext=modgeo.dif_ang(modgeo.Pa, modgeo.Pe, modgeo.ext)
                    untroffshape.geos[0].calc_bounding_box()
        
        return untroffshape
    
    def do_clipping(self, untroffshape):
        """ 
        The clipping partly according to Para 4.
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        @param untroffshape: The untrimmed / unjoined offset shape
        @return: Returns the final offset shapes.
        """
        
        #First add a nr to the geomety in a list and sort them


        BBListPa=[]
        BBListPe=[]
        
        geo_nrs=len(untroffshape.geos)
        
        for geo_nr in range(len(untroffshape.geos)):
            geo=untroffshape.geos[geo_nr]
            geo.Nr=geo_nr
            
        BBListPa=untroffshape.geos[:]
        BBListPe=untroffshape.geos[:]
        
        BBListPa.sort(self.cmp_Pa)
        BBListPe.sort(self.cmp_Pe)
        
        
        while len(BBListPe):
            geo1=BBListPe[0]
            geo2_index=0
            while 1:
                geo2=BBListPa[geo2_index]
               
                #If intersection
                if (geo1.BB.Pe.x<geo2.BB.Pa.x):
                    BBListPe.pop(0)
                    BBListPa.pop(BBListPa.index(geo1))
                    break
                #intersection with itself or the next element have to be not counted.
                elif geo2.Nr in range(geo1.Nr-1, geo1.Nr+2):
                    pass
                elif geo1.Nr==geo_nrs\
                        and geo2.Nr==0\
                        and untroffshape.closed==1:
                    pass
                elif geo1.Nr==0\
                        and geo2.Nr==geo_nrs\
                        and untroffshape.closed==1:
                    pass
                else:
                    
                    intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
                    
                    if intersect:
                        points = geo1.find_inter_points(geo2)  
                        for Point in points:
                             
                            if Point.isTIP(geo1, self.tol, 'all') and \
                             Point.isTIP(geo2, self.tol, 'all'):
    #                            print 'Intersection'
    #                            print geo1
    #                            print geo2
                                
                                geo1.inters.append(Point)
                                geo2.inters.append(Point)
                
                geo2_index+=1
                if geo2_index==len(BBListPa):
                    BBListPe.pop(0)
                    break
##    
##  
##        #pretshape.BB = self.shape.BB
##        
##        #Find all intersection points between the geometries of the untrimmed 
##        #offset shape and append them to geo.inters.
##        #Do for all Geometries -1 (if closed for all)
##        for geo_nr1 in range(len(untroffshape.geos)):
##            for geo_nr2 in range(geo_nr1+2,len(untroffshape.geos)):
##                
##                geo1=untroffshape.geos[geo_nr1]
##                geo2=untroffshape.geos[geo_nr2]
##                                             
##                intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
##                
##                if intersect:
##                    points = geo1.find_inter_points(geo2)  
##                    for Point in points:
###                        print geo1
###                        print geo2
###                        print Point
##                        #print geo1.isTIP(Point, self.tol, 'all')
##                        #print geo2.isTIP(Point, self.tol, 'all')
##                         
##                        if Point.isTIP(geo1, self.tol, 'all') and \
##                         Point.isTIP(geo2, self.tol, 'all'):
##                            #if not(Point.isintol(geo1.Pe, self.tol))and \
##                            #not(Point.isintol(geo2.Pa, self. tol)):
##                            geo1.inters.append(Point)
##                            geo2.inters.append(Point)

                           
        #Sort the intersection Points in ascending order and then splits the 
        #shape at the intersection points into new shapes.
        clippedshapes=[]
        clippedshapes.append(self.return_new_clippedshape())       
        for geo in untroffshape.geos:
            if len(geo.inters)==0:
                clippedshapes[-1].geos.append(geo)
            else:
                geo.sort_inters_asscending()
                geo2=geo
                for inter in geo.inters:
                    [geo1,geo2]=geo2.split_geo_at_point(inter)
                    if not(inter.isintol(geo1.Pa,self.tol)):
                        clippedshapes[-1].geos.append(geo1)
                    clippedshapes.append(self.return_new_clippedshape())
                if not(inter.isintol(geo2.Pe,self.tol)):
                    clippedshapes[-1].geos.append(geo2)
          
        #First:
        #Find all intersection points between the geometries of the untrimmed 
        #offset shape and the initial geos of shape and delete them from the 
        #returned shape list.
        
        #Second:
        #Find all Closest Points between the Geometries if the Closest Distance 
        #is smaller then the offset distance also delete them from the returned 
        #shape list.
        
        
        del_shapes=[]
        for s_nr in range(len(clippedshapes)):
            
            BBListPe1=clippedshapes[s_nr].geos[:]
            BBListPa2=self.pretshape.geos[:]
            
            BBListPe1.sort(self.cmp_Pe)
            BBListPa2.sort(self.cmp_Pa)
                  
            break_l=1
        
            while break_l and len(BBListPe1):
                geo1=BBListPe1[0]
                geo2_index=0
                
                while break_l:
                    geo2=BBListPa2[geo2_index]
                    
#                    #Break if no further distance lower the radius is possible
                    if (geo1.BB.Pe.x+self.radius+self.tol)<(geo2.BB.Pa.x):
                        #print "Abbruch 1"
                        BBListPe1.pop(0)
                        break
                    
                    #A distance lower then radius is general possible
                    if geo1.BB.hasintersection(geo2.BB, self.tol+self.radius):
                        #There is a true intersection
                        #print geo1.distance_to_geo(geo2)
               
                        if geo1.distance_to_geo(geo2)<(self.radius-self.tol):
#                            print geo1
#                            print geo2
#                            print geo1.distance_to_geo(geo2)
                            del_shapes.append(clippedshapes[s_nr])
                            break_l=0
                            break
                        
                    geo2_index+=1
                    if geo2_index==len(BBListPa2):
                        BBListPe1.pop(0)
                        break
##                    
##        
##        print del_shapes
##        
##        del_shapes=[]
##        for s_nr in range(len(clippedshapes)):
##            break_l=0
##            for geo_nr1 in range(len(clippedshapes[s_nr].geos)):
##                if break_l==1:
##                    break
##                for geo_nr2 in range(len(self.pretshape.geos)):
##                    if break_l==1:
##                        break
##                    geo1=clippedshapes[s_nr].geos[geo_nr1]
##                    geo2=self.pretshape.geos[geo_nr2]
##                                             
##                    intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
##                
##                    if intersect:
##                        points = geo1.find_inter_points(geo2)  
##                        for Point in points:
##                         
##                            if Point.isTIP(geo1, self.tol) and \
##                             Point.isTIP(geo2, self.tol):
##                                #print geo1
##                                #print geo2
##                                #print Point
##                                del_shapes.append(clippedshapes[s_nr])
##                                break_l=1
##                                break
##                    
##                    if not(len(del_shapes)) or \
##                    not(clippedshapes[s_nr]==del_shapes[-1]):
##                        intersect = geo1.BB.hasintersection(geo2.BB, 
##                                                            self.radius+self.tol)
##                        if intersect:
##                            
##                            
##                            if geo1.distance_to_geo(geo2)<self.radius-self.tol:
##                                #print geo1
##                                #print geo2
##                                #print geo1.distance_to_geo(geo2)
##                                del_shapes.append(clippedshapes[s_nr])
##                                break_l=1
                                    
        for del_shape in del_shapes:
            clippedshapes.pop(clippedshapes.index(del_shape))
              
        for clippedshape in clippedshapes:
            clippedshape.nr=self.shape_nr
            self.shape_nr+=1
             
        return clippedshapes
                    
    def return_new_clippedshape(self):
        clippedshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape_nr,
                           closed=self.shape.closed,
                           plotoption=1,
                           geos=[],
                           geos_hdls=[])
        return clippedshape
       
    def cmp_Pa(self,geo1,geo2):
        """
        Compare Function for the sorting
        """  
        if geo1.BB.Pa.x<geo2.BB.Pa.x:
            return -1
        elif geo1.BB.Pa.x>geo2.BB.Pa.x:
            return 1
        else:
            return 0
        #return geo1.BB.Pa.x<=geo2.BB.Pa.x

    def cmp_Pe(self,geo1,geo2):
        """
        Compare Function for the sorting
        """
        if geo1.BB.Pe.x<geo2.BB.Pe.x:
            return -1
        elif geo1.BB.Pe.x>geo2.BB.Pe.x:
            return 1
        else:
            return 0
        #return geo1.BB.Pe.x<=geo2.BB.Pe.x    
          
class CCArcGeo(ArcGeo):
    def __init__(self, Pa=None, Pe=None, O=None, r=1,
                         s_ang=None, e_ang=None, direction=1, Nr=None):
        """
        Standard Method to initialise the CCArcGeo
        """
            
        ArcGeo.__init__(self, Pa=Pa, Pe=Pe, O=O, r=r,
                         s_ang=s_ang, e_ang=e_ang, direction=direction)
        
        self.type = 'CCArcGeo'
        self.col = 'Blue'
        self.inters=[]
        self.Nr=Nr
        self.calc_bounding_box()
        

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nCCArcGeo") + \
               ("\nNr : %s" % (self.Nr)) + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\nBB : %s" % self.BB) + \
               ("\ninters : %s" % self.inters) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))

    def calc_bounding_box(self):
        """
        Calculate the BoundingBox of the geometry and save it into self.BB
        """
        
        Pa = PointClass(x=self.O.x - self.r, y=self.O.y - self.r)
        Pe = PointClass(x=self.O.x + self.r, y=self.O.y + self.r)
        
        #Do the calculation only for arcs have positive extend => switch angles
        if self.ext >= 0:
            s_ang = self.s_ang
            e_ang = self.e_ang
        elif self.ext < 0:
            s_ang = self.e_ang
            e_ang = self.s_ang
                 
        #If the positive X Axis is crossed
        if not(self.wrap(s_ang, 0) >= self.wrap(e_ang, 1)):
            Pe.x = max(self.Pa.x, self.Pe.x)

        #If the positive Y Axis is crossed 
        if not(self.wrap(s_ang - pi / 2, 0) >= self.wrap(e_ang - pi / 2, 1)):
            Pe.y = max(self.Pa.y, self.Pe.y)

        #If the negative X Axis is crossed
        if not(self.wrap(s_ang - pi, 0) >= self.wrap(e_ang - pi, 1)):
            Pa.x = min(self.Pa.x, self.Pe.x)

        #If the negative Y is crossed 
        if not(self.wrap(s_ang - 1.5 * pi, 0) >= 
                self.wrap(e_ang - 1.5 * pi, 1)):
            Pa.y = min(self.Pa.y, self.Pe.y)
       
        self.BB = BoundingBoxClass(Pa=Pa, Pe=Pe)
        
    def wrap(self, angle, isend=0):
        """
        Wraps the given angle into a range between 0 and 2pi
        @param angle: The angle to be wrapped
        @param isend: If the angle is the end angle or start angle, this makes a
        difference at 0 or 2pi.
        @return: Returns the angle between 0 and 2 *pi
        """ 
        wrap_angle = angle % (2 * pi)
        if isend and wrap_angle == 0.0:
            wrap_angle += 2 * pi
        elif wrap_angle == 2 * pi:
            wrap_angle -= 2 * pi
            
        return wrap_angle

    def find_inter_points(self, other=[], tol=0.01):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "CCLineGeo":
            IPoints=other.find_inter_point_l_a(self)
            for IPoint in IPoints:
                v1_temp=IPoint.v1
                geo1_temp=IPoint.geo1
                IPoint.v1=IPoint.v2
                IPoint.geo1=IPoint.geo2
                IPoint.v2=v1_temp
                IPoint.geo2=geo1_temp
            return IPoints
        elif other.type == "CCArcGeo":
            return self.find_inter_point_a_a(other,tol=tol)
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_a_a(self, other, tol=0.01):
        """
        Find the intersection between 2 CCArcGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """   
        O_dis = self.O.distance(other.O)
        
        #If self circle is surrounded by the other no intersection 
        #EVENTUELL MIT TOL WIEDER????????????????????????????????????????????????
        #MAY CONTAIN TOL AGAIN ??? 
        if(O_dis < abs(self.r - other.r)-tol):
            return []

        #If other circle is surrounded by the self no intersection
        if(O_dis < abs(other.r - self.r)-tol):
            return []
        
        #If both circles have the same center and radius
        if abs(O_dis) < tol/2 and abs(self.r-other.r) < tol/2:
            Pi1=IPointClass(x=self.Pa.x,y=self.Pa.y,
                         v1=0.0, v2=-1.0,
                        geo1=self, geo2=other)
            
            Pi2=IPointClass(x=self.Pe.x,y=self.Pe.y,
                         v1=1.0, v2=0.0,
                        geo1=self, geo2=other)
            
            
            #return [self.Pa, self.Pe]
            return [Pi1, Pi2]

        #The following algorithm was found on :
        #http://www.sonoma.edu/users/w/wilsonst/Papers/Geometry/circles/default.htm
        
        root = ((pow(self.r + other.r , 2) - pow(O_dis, 2)) * 
                  (pow(O_dis, 2) - pow(other.r - self.r, 2)))
        
        #If the Line is a tangent the root is 0.0.
        if root<=0.0:
            root=0.0
        else:  
            root=sqrt(root)
        
        xbase = (other.O.x + self.O.x) / 2 + \
        (other.O.x - self.O.x) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        ybase = (other.O.y + self.O.y) / 2 + \
        (other.O.y - self.O.y) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        Pi1 = IPointClass(x=xbase + (other.O.y - self.O.y) / \
                          (2 * pow(O_dis, 2)) * root,
                    y=ybase - (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root,
                    geo1=self, geo2=other,
                    v1=0.0,v2=0.0)
        
        Pi1.v1 = self.dif_ang(self.Pa, Pi1, self.ext)/self.ext
        Pi1.v2 = other.dif_ang(other.Pa, Pi1, other.ext)/other.ext

        Pi2 = IPointClass(x=xbase - (other.O.y - self.O.y) / \
                         (2 * pow(O_dis, 2)) * root,
                    y=ybase + (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root,
                    geo1=self, geo2=other,
                    v1=0.0,v2=0.0)
        Pi2.v1 = self.dif_ang(self.Pa, Pi2, self.ext)/self.ext
        Pi2.v2 = other.dif_ang(other.Pa, Pi2, other.ext)/other.ext
        
        
        if Pi1.distance(Pi2) == 0.0:
            return [Pi1]
        else:
            return [Pi1, Pi2]
        
    def distance_to_geo(self, other=[]):
        """
        Find the distance between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        return 1e99


#    def isTIP(self, Point=PointClass, tol=0.01, type='all'):
#        """
#        Checks if the Point is a Local Self Intersection Point of the CCArcGeo
#        @param Point: The Point which shall be checked
#        @return: Returns true or false
#        """
#        
#        if type=='inside':
#            if (self.Pa.isintol(Point,tol) or self.Pe.isintol(Point,tol)):
#                return False
#        else:
#            #The linear tolerance in angle
#            atol = tol / 2 / pi / self.r
#            pang = self.O.norm_angle(Point)
#             
#            if self.ext >= 0.0:
#                return self.angle_between(self.s_ang - atol, self.e_ang + tol, pang)
#            else:
#                return self.angle_between(self.e_ang - atol, self.s_ang + tol, pang)
        
    def sort_inters_asscending(self):
        """
        Sorts the intersection points in self.inters in ascending order
        """       
        self.inters.sort(self.cmp_asscending)
          
    def cmp_asscending(self,P1,P2):
        """
        Compare Function for the sorting
        """  
        
        #The angle between startpoint and where the intersection occurs
        d_ang1 = (self.O.norm_angle(P1)-self.s_ang )%(2*pi)
        d_ang2 = (self.O.norm_angle(P2)-self.s_ang)%(2*pi)
        
        #Correct by 2*pi if the direction is wrong
        if self.ext<0.0:
            d_ang1-=2*pi
            d_ang2-=2*pi
                
        if d_ang1>d_ang2:
            return 1
        elif d_ang1==d_ang2:
            return 0
        else:
            return -1
        
    def split_into_2geos(self, ipoint=PointClass()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be split between ipoint and Pe.
        @param ipoint: The Point where the intersection occurs
        @return: A list of 2 CCArcGeo's will be returned.
        """
       
        #The angle between endpoint and where the intersection occurs
        d_e_ang = self.e_ang - self.O.norm_angle(ipoint)
        
        #Correct by 2*pi if the direction is wrong
        if d_e_ang > self.ext:
            d_e_ang -= 2 * pi
            
        #The Point where the geo will be split
        spoint = self.O.get_arc_point(ang=degrees(self.e_ang - d_e_ang / 2),
                                      r=self.r)
        
        return self.split_geo_at_point(spoint)
        
    def split_geo_at_point(self,spoint):
        """
        Splits the given geometry into 2 geometries. The
        geometry will be split at Point spoint.
        @param ipoint: The Point where the intersection occurs
        @return: A list of 2 CCArcGeo's will be returned.
        """
        
        #Generate the 2 geometries and their bounding boxes.
        Arc1 = CCArcGeo(Pa=self.Pa, Pe=spoint, r=self.r,
                       O=self.O, direction=self.ext)
        
        Arc2 = CCArcGeo(Pa=spoint, Pe=self.Pe, r=self.r,
                       O=self.O, direction=self.ext)
        
        return [Arc1, Arc2]
    
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: The offset geometry
        """  
        
        
        #For Arcs in ccw direction
        if self.ext < 0.0 and direction == 41:
            offr = self.r + radius
        elif self.ext < 0.0 and direction == 42:
            offr = self.r - radius
        elif self.ext >= 0 and direction == 41:
            offr = self.r - radius
        else:
            offr = self.r + radius
            
        #If the radius of the new element is smaller then 0.0 return nothing 
        #and therefore ignore this geom.
        if offr <= 0.0:
            return []
                    
        offPa = self.O.get_arc_point(ang=degrees(self.s_ang), r=offr)
        offPe = self.O.get_arc_point(ang=degrees(self.e_ang), r=offr)
              
        offArc = CCArcGeo(Pa=offPa, Pe=offPe, O=self.O, r=offr, direction=self.ext)
        offArc.calc_bounding_box()
        
        return [offArc]
    
    def trim_join(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        if other.type == "CCLineGeo":
            return self.trim_join_al(other, newPa, orgPe, tol)
        else:
            return self.trim_join_aa(other, newPa, orgPe, tol)
            
        
            #print 'Hab ich noch nicht' 
            
    def trim_join_al(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
        
        #Fast Case 1a
        if self.Pe.isintol(other.Pa,tol):
            geos.append(CCArcGeo(Pa=newPa, Pe=other.Pa, O=self.O,
                                   r=self.r, direction= self.ext))
            return geos
        
        points = self.find_inter_points(other)
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            
            isTIP1 = ipoint.isTIP(self, tol, 'all')
            isTIP2 = ipoint.isTIP(other, tol, 'all')
            
#            print ipoint
#            print isTIP1
#            print isTIP2
            
            #Case 1 a
            if isTIP1 and isTIP2:
                geos.append(CCArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe,
                                   r=r, direction=direction))
                
            #Case 1 c & d
            else:
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCLineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=direction, 
                               r=r))
            
        return geos
    
    
    def trim_join_aa(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        geos = [] 
        
        #Fast Case 1a
        #if self.Pe.isintol(other.Pa,tol):
        #    geos.append(CCArcGeo(Pa=newPa, Pe=other.Pa, O=self.O,
        #                           r=self.r, direction= self.ext))
        #    return geos
        
        points = self.find_inter_points(other, tol=abs(tol))
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = ipoint.isTIP(self, tol, 'all')
            isTIP2 = ipoint.isTIP(other, tol, 'all')
            
#            print ipoint
#            print isTIP1
#            print isTIP2
            
            #Case 1 a
            if (isTIP1 and isTIP2) or (not(isTIP1) and not(isTIP2)):
                
                geos.append(CCArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                                 
            #Case 1 b########################################################################################FALSCH############
            else:
                direction=self.get_arc_direction(orgPe)
                r=self.Pe.distance(orgPe)
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=-direction,
                               r=r))
                
        #Case 2
        else: 
            direction=self.get_arc_direction(orgPe)
            r=self.Pe.distance(orgPe)
          
            geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=-direction,
                               r=r))
            
        return geos
    
    def get_arc_direction(self,newO):
        """ 
        Calculate the arc direction given from the Arc and O of the new Arc.
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        """ 
        
        a1= self.e_ang - pi/2 * self.ext / abs(self.ext)
        a2=self.Pe.norm_angle(newO)
        direction=a2-a1
        
        if direction>pi:
            direction=direction-2*pi
        elif direction<-pi:
            direction=direction+2*pi
            
        #print ('Die Direction ist: %s' %direction)
        
        return direction
    
class CCLineGeo(LineGeo):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa, Pe):
        """
        Standard Method to initialise the CCLineGeo
        """
        
        LineGeo.__init__(self, Pa=Pa,Pe=Pe)
        
        self.type = "CCLineGeo"
        self.col = 'Black'
        self.inters=[]
        self.calc_bounding_box()
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nCCLineGeo") + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe) + \
               ("\nBB : %s" % self.BB) + \
               ("\ninters : %s" % self.inters) + \
               ("\nlength: %0.5f" % self.length)   
    def calc_bounding_box(self):
        """
        Calculate the BoundingBox of the geometry and save it into self.BB
        """
        Pa = PointClass(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = PointClass(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))
        
        self.BB = BoundingBoxClass(Pa=Pa, Pe=Pe)
        
    def find_inter_points(self, other=[], tol=0.01):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "CCLineGeo":
            inters=self.find_inter_point_l_l(other)
            #print inters
            return inters
        elif other.type == "CCArcGeo":
            inters=self.find_inter_point_l_a(other)
            #for inter in inters:
                #print inter
            return inters
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_l_l(self, L2):
        """
        Find the intersection between 2 CCLineGeo elements. There can be only one
        intersection between 2 lines. Returns also FIP which lay on the ray.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """

        dx1 = self.Pe.x - self.Pa.x
        dy1 = self.Pe.y - self.Pa.y
        
        dx2 = L2.Pe.x - L2.Pa.x
        dy2 = L2.Pe.y - L2.Pa.y

        dax = self.Pa.x - L2.Pa.x
        day = self.Pa.y - L2.Pa.y

        #Return nothing if one of the lines has zero length
        if (dx1 == 0 and dy1 == 0) or (dx2 == 0 and dy2 == 0):
            return []
        
        #Possible check needed for parallel lines (Not sure on that)
        if atan2(dy1, dx1) == atan2(dy2, dx2):
            return []
        
        #To avoid division by zero.
        try:
            if(abs(dx2) >= abs(dy2)):
                v1 = (day - dax * dy2 / dx2) / (dx1 * dy2 / dx2 - dy1)
                v2 = (dax + v1 * dx1) / dx2    
            else:
                v1 = (dax - day * dx2 / dy2) / (dy1 * dx2 / dy2 - dx1)
                v2 = (day + v1 * dy1) / dy2
        except:
            return []
            
        return [IPointClass(x=self.Pa.x + v1 * dx1,
                          y=self.Pa.y + v1 * dy1,
                          v1=v1,
                          v2=v2,
                          geo1=self,
                          geo2=L2)]
    
    def find_inter_point_l_a(self, Arc):
        """
        Find the intersection between 2 CCLineGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        Ldx = self.Pe.x - self.Pa.x
        Ldy = self.Pe.y - self.Pa.y
       
        #Mitternachtsformel zum berechnen der Nullpunkte der quadratischen 
        #Gleichung 
        #Formula to compute the zeros of the quadratic equation
        a = pow(Ldx, 2) + pow(Ldy, 2)
        b = 2 * Ldx * (self.Pa.x - Arc.O.x) + 2 * Ldy * (self.Pa.y - Arc.O.y)
        c = pow(self.Pa.x - Arc.O.x, 2) + pow(self.Pa.y - Arc.O.y, 2) - pow(Arc.r, 2)
        root = pow(b, 2) - 4 * a * c
       
        #If the value under the sqrt is negative there is no intersection.
        if root < 0 or a==0.0:
            return []
        

        v1 = (-b + sqrt(root)) / (2 * a)
        v2 = (-b - sqrt(root)) / (2 * a)
        
        Pi1 = IPointClass(x=self.Pa.x + v1 * Ldx,
                       y=self.Pa.y + v1 * Ldy,
                       geo1=self, geo2=Arc,
                       v1=v1, v2=0.0)
        
        Pi1.v2 = Arc.dif_ang(Arc.Pa, Pi1, Arc.ext)/Arc.ext
         
        #If the root is zero there is only one solution and the line is a tangent.
        if(root == 0):
            return [Pi1] 
            
        Pi2 = IPointClass(x=self.Pa.x + v2 * Ldx,
                       y=self.Pa.y + v2 * Ldy,
                       geo1=self, geo2=Arc,
                       v1=v2, v2=0.0)
        Pi2.v2 = Arc.dif_ang(Arc.Pa, Pi2, Arc.ext)/Arc.ext
        
        return [Pi1, Pi2]
    
    def sort_inters_asscending(self):
        """
        Sort the intersection points in self.inters in ascending order
        """       
        self.inters.sort(self.cmp_asscending)
          
    def cmp_asscending(self,P1,P2):
        """
        Compare Function for the sorting
        """  
        d1= P1.distance(self.Pa)
        d2= P2.distance(self.Pa)
              
        if d1>d2:
            return 1
        elif d1==d2:
            return 0
        else:
            return -1
    
    def distance_to_geo(self, other=[]):
        """
        Find the distance between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if other.type == "CCLineGeo":
            return self.distance_line_line(other)
        elif other.type == "CCArcGeo":
            return 1e99
        else:
            print 'Hab ich noch nicht' 
            
    def distance_line_line(self,other):
        """
        Find the distance between 2 ccLineGeo elements. 
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        return min(self.distance_point_line(other.Pa),
                   self.distance_point_line(other.Pe),
                   other.distance_point_line(self.Pa),
                   other.distance_point_line(self.Pe))
            
        
    def distance_point_line(self,Point):
        """
        Find the shortest distance between CCLineGeo and Point elements.  
        Algorithm acc. to 
        http://notejot.com/2008/09/distance-from-Point-to-line-segment-in-2d/
        http://softsurfer.com/Archive/algorithm_0106/algorithm_0106.htm
        @param Point: the Point
        @return: The shortest distance between the Point and Line
        """
        
        d=self.Pe-self.Pa
        v=Point-self.Pa
    
        t=dotProd(d,v)
        
        if t<=0:
            #our Point is lying "behind" the segment
            #so end Point 1 is closest to Point and distance is length of
            #vector from end Point 1 to Point.
            return self.Pa.distance(Point)
        elif t>=dotProd(d,d):
            #our Point is lying "ahead" of the segment
            #so end Point 2 is closest to Point and distance is length of
            #vector from end Point 2 to Point.
            return self.Pe.distance(Point)
        else:
            #our Point is lying "inside" the segment
            #i.e.:a perpendicular from it to the line that contains the line
            #segment has an end Point inside the segment
            return sqrt(dotProd(v,v) - (t*t)/dotProd(d,d));
                     
    def split_into_2geos(self, ipoint=PointClass()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be split between ipoint and Pe.
        @param ipoint: The Point where the intersection occurs
        @return: A list of 2 CCLineGeo's will be returned.
        """
        #The Point where the geo shall be split
        spoint = PointClass(x=(ipoint.x + self.Pe.x) / 2,
                          y=(ipoint.y + self.Pe.y) / 2)
        
        return self.split_geo_at_point(spoint)
        
    def split_geo_at_point(self,spoint):
        """
        Splits the given geometry into 2 geometries. The
        geometry will be split at Point spoint.
        @param ipoint: The Point where the intersection occurs
        @return: A list of 2 CCArcGeo's will be returned.
        """
        Li1 = CCLineGeo(Pa=self.Pa, Pe=spoint)
        Li2 = CCLineGeo(Pa=spoint, Pe=self.Pe)
        
        return [Li1, Li2]
     
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: A list of 2 CCLineGeo's will be returned.
        """   
        Pa, s_angle = self.get_start_end_points(0)
        Pe, e_angle = self.get_start_end_points(1)
        if direction == 41:
            offPa = Pa.get_arc_point(s_angle + pi/2, radius)
            offPe = Pe.get_arc_point(e_angle - pi/2, radius)
        elif direction == 42:
            offPa = Pa.get_arc_point(s_angle - pi/2, radius)
            offPe = Pe.get_arc_point(e_angle + pi/2, radius)
            
        offLine = CCLineGeo(Pa=offPa, Pe=offPe)
        offLine.calc_bounding_box()
        
        return [offLine]
    
    def trim_join(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        if other.type == "CCLineGeo":
            return self.trim_join_ll(other, newPa, tol)
        else:
            return self.trim_join_la(other, newPa, orgPe, tol)
        
            #print 'Hab ich noch nicht'
    
      
    def trim_join_ll(self, other, newPa, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
        
        #Find the nearest intersection Point
        points = self.find_inter_points(other)
        
        #Problem??
        #if len(points)==0:
        
        #Case 1 according to para 3.2
        if self.Pe.isintol(other.Pa, tol):
            geos.append(CCLineGeo(newPa, self.Pe))
        elif len(points)==0:
            return []
        #Case 2 according to para 3.2
        else:
            
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = ipoint.isTIP(self, tol, 'all')
            isTIP2 = ipoint.isTIP(other, tol, 'all')
                       
            #Case 2a according to para 3.2
            if isTIP1 and isTIP2:
                geos.append(CCLineGeo(newPa, ipoint))
            #Case 2b according to para 3.2
            elif not(isTIP1) and not(isTIP2):
                if ipoint.isPFIP(self):
                    geos.append(CCLineGeo(newPa, ipoint))
                else:
                    geos.append(CCLineGeo(newPa, self.Pe))
                    geos.append(CCLineGeo(self.Pe, other.Pa))
            #Case 2c according to para 3.2
            else:
                geos.append(CCLineGeo(newPa, self.Pe))
                geos.append(CCLineGeo(self.Pe, other.Pa))

        return geos
    
    def trim_join_la(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end Point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
       
        
        #Fast Case 1a
        if self.Pe.isintol(other.Pa,tol):
            geos.append(CCLineGeo(newPa, other.Pa))
            return geos
        
        points = self.find_inter_points(other)
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = ipoint.isTIP(self, tol, 'all')
            isTIP2 = ipoint.isTIP(other, tol, 'all')
            
            #print isTIP1
            #print isTIP2
     
            #Case 1 a
            if isTIP1 and isTIP2:
                #print 'case 1a'
                geos.append(CCLineGeo(newPa, ipoint))
                #if geos[-1].length<tol:
                    #print ('Case1a')
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                #print 'case 1b'
                direction=newPa.get_arc_direction(self.Pe,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(CCLineGeo(newPa, self.Pe))
                #if geos[-1].length<tol:
                #    print ('Case1b')
                geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe, direction=direction,
                                   r=r))
                
                
            #Case 1 c & d
            else:
                #print 'case 1c &d'
                geos.append(CCLineGeo(newPa, self.Pe))
                #if geos[-1].length<tol:
                    #print ('Case1c 1')
                geos.append(CCLineGeo(self.Pe, other.Pa))
                if geos[-1].length<tol:
                    geos.pop()
                    print ('Case1c 2')
                    #print self
                    #print other
                    #print ipoint
                    #print isTIP1
                    #print isTIP2
                
        #Case 2
        else: 
            #print 'case 2'
            direction=newPa.get_arc_direction(self.Pe,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(CCLineGeo(newPa, self.Pe))
            #if geos[-1].length<tol:
                #print ('Case2')
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=direction, 
                               r=r))
            
        return geos
    
class IPointClass(PointClass):
    """
    Standard Point Class Inherited for Intersection Point Class.
    """ 
    def __init__(self, x=0, y=0,v1=0, v2=0, geo1=None, geo2=None):
        """
        Standard Method to initialise the IPointClass
        """
        
        PointClass.__init__(self, x=x,y=y)
        self.v1=v1
        self.v2=v2
        self.geo1=geo1
        self.geo2=geo2
        
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f \n' % (self.x, self.y)) \
                +('v1 ->%6.3f  v2 ->%6.3f \n' % (self.v1, self.v2))
                
    def isTIP(self, geo=[], tol=0.0, type='all'):
        """
        Checks if the Point is on the CCLineGeo, therefore a true intersection
        Point.
        @param other: The Point which shall be checked
        @return: Returns true or false
        """
        if geo==self.geo1:
            v=self.v1
        else:
            v=self.v2
            
        
        if type=='inside':
            if (not(geo.Pa.isintol(self,tol)) and \
                not(geo.Pe.isintol(self,tol)) and \
                (v>0.0 and v<1.0)):
                return True
        elif type=='exact':
            if v>=0.0 and v<=1.0:
                return True
        else:
            if (geo.Pa.isintol(self,tol) or \
                geo.Pe.isintol(self,tol) or \
                (v>0.0 and v<1.0)):
                return True
        
        return False    
#        else:
#            return self.BB.pointisinBB(Point=Point, tol=tol)
    
    def isPFIP(self, geo):
        """
        Checks if the Intersectionpoint is on the Positive ray of the line.
        Therefore is a positive false intersection Point. Therefore it's just 
        needed to check if the Point is nearer to Pe then to Pa
        @param ipoint: The Point which shall be checked
        @return: Returns true or false
        """
        if geo==self.geo1:
            v=self.v1
        else:
            v=self.v2
            
        return v>1.0
    

       
    
def dotProd(P1,P2):
    """
    Returns the dotProduct of two points
    @param P1: The first Point
    @param P2: The 2nd Point
    @return: dot Product of the points.
    """ 
    
    return (P1.x*P2.x) + (P1.y*P2.y)

    
