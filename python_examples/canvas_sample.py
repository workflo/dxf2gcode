import wx, sys, time, threading
from wx.lib.floatcanvas.FloatCanvas import FloatCanvas
from wx.lib.floatcanvas.GUIMode import GUIMove


myEVT_PRINT = wx.NewEventType()
EVT_PRINT = wx.PyEventBinder(myEVT_PRINT, 1)
class PrintEvent(wx.PyCommandEvent):
    def __init__(self,message):
        wx.PyCommandEvent.__init__(self, myEVT_PRINT, wx.ID_ANY)
        self._message = message
        
    def GetMessage(self):
        return self._message


class Renderer:
    def __init__(self,parent):
        self.parent = parent
        self.requests = []
        self.counter = 0
        self.running = True
        threading.Thread(target=self.render).start()

    def MakeRequest(self):
        self.requests.append(None)

    def render(self):
        while self.running:
            if self.requests:
                request = self.requests.pop(0)
                # Make the CPU work
                for i in range(100000): pass
                self.counter += 1
                wx.PostEvent(self.parent.log,PrintEvent("%s\n"%self.counter))
            else:
                time.sleep(.01)
                

class MyTextCtrl(wx.TextCtrl):
    def __init__(self,parent):
        wx.TextCtrl.__init__(self,parent,-1,style = wx.TE_MULTILINE)
        sys.stdout = self
        self.Bind(EVT_PRINT, self.OnPrint)

    def OnPrint(self,e):
        self.AppendText(e.GetMessage())


class MyCanvas(FloatCanvas):
    def __init__(self, parent):
        self.parent = parent
        FloatCanvas.__init__(self, parent, BackgroundColor="BLACK")
        self.circles = []
        self.GUIMode = GUICustom(self)

    def UpdateCircles(self, coord):
        self.RemoveObjects(self.circles)
        self.circles = []
        for i in range(25):
            self.circles.append(self.AddCircle((coord[0]+i%5*5,coord[1]+i),
                                               Diameter=10,LineColor="White"))

class GUICustom(GUIMove):
    def OnLeftDown(self,e):
        self.starttime = time.time()

    def OnLeftUp(self,e):
        return
    
    def OnMove(self,e):
        if e.LeftIsDown() and e.Dragging():
            # Uncomment these lines to see the fix
##            t = time.time()
##            if t - self.starttime < .05:
##                return
##            self.starttime = t
            self.Canvas.UpdateCircles(self.Canvas.PixelToWorld(e.GetPosition()))
            self.Canvas.parent.renderer.MakeRequest()
            self.Canvas.Draw()


class TestFrame(wx.Frame):
    def __init__(self,parent,id):
        wx.Frame.__init__(self,parent,id,"Test App")
        self.renderer = Renderer(self)
        self.log = MyTextCtrl(self)
        self.Canvas = MyCanvas(self)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.Canvas,3,wx.EXPAND)
        sizer.Add(self.log,1,wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE,self.OnExit)
        self.Show(True)

    def OnExit(self,e):
        self.renderer.running = False
        self.Destroy()

app = wx.App()
frame = TestFrame(None,wx.ID_ANY)
app.MainLoop()
