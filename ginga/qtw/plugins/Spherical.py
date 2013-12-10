#
# Spherical.py -- Cartesian to Spherical plugin for fits viewer
# 
# Ryan Beaty 

#Things to do:
#1) Think about making a SQL type database for objects that I load in (sort of ike aladin)
#2) add sphere that I can go to coordinates on the sphere or left click on the image to go to the sphere.
#
from ginga import GingaPlugin
from ginga.qtw.QtHelp import QtGui, QtCore
from ginga.qtw import QtHelp
from ginga.misc import Bunch

import numpy
import math

class Spherical(GingaPlugin.GlobalPlugin):

    def __init__(self, fv):
        # superclass defines some variables for us, like logger
        super(Spherical, self).__init__(fv) #Inherits the __init__ found in GingaPlugin.GlobalPlugin. 
        #More on Super() found: http://www.cafepy.com/article/python_attributes_and_methods/python_attributes_and_methods.html#using-super-example-1

        self.channel = {}
        self.active = None
        self.info = None
        
        #fitsimage=fitsimage

        self.w.tooltips = self.fv.w.tooltips

        fv.set_callback('add-channel', self.add_channel)
        fv.set_callback('field-info', self.field_info)
        fv.set_callback('right-click', self.right_click)
        
        
    def build_gui(self, container):
        nb = QtHelp.StackedWidget() #StackedWidget adds tab and removes tab.
        self.nb = nb
        container.addWidget(nb, stretch=0) 

    def create_info_window(self):
        sw = QtGui.QScrollArea()

        widget = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(2, 2, 2, 2)
        widget.setLayout(vbox)
        
        captions = (
                    ('X', 'xlabel', '@X', 'entry'),
                    ('Y', 'xlabel', '@Y', 'entry'),
                    ('Z', 'xlabel', '@Z', 'entry'),
                    ('Radius','label'),('Theta','label'),('Phi','label'),
                    ('RA', 'label'), ('DEC', 'label'),
                    ('Radius2','label'),('Theta2','label'),('Phi2','label'),
                    )

        w, b = QtHelp.build_info(captions)

        
        b.x.setToolTip("Set X value (press Enter)")
        b.y.setToolTip("Set Y value (press Enter)")
        b.z.setToolTip('Set Z value (press Enter)')


        vbox.addWidget(w, stretch=0)

        #widget.show()
        sw.setWidget(widget)
        return sw, b

    def add_channel(self, viewer, chinfo):
        sw, winfo = self.create_info_window()
        chname = chinfo.name

        self.nb.addTab(sw, unicode(chname))
        sw.show()
        index = self.nb.indexOf(sw)
        info = Bunch.Bunch(widget=sw, winfo=winfo,
                           nbindex=index)
        self.channel[chname] = info

#http://www.blog.pythonlibrary.org/2013/04/10/pyside-connecting-multiple-widgets-to-the-same-slot/

        winfo.x.returnPressed.connect(lambda: self.coordinates(info)) #self.coordinates(info), if i have def coordinates(self,info): with info.winfo everywhere instead of self.
        winfo.y.returnPressed.connect(lambda: self.coordinates(info))
        winfo.z.returnPressed.connect(lambda: self.coordinates(info))
        
        #winfo.Radius.setText('1')
    
        
    def radius(self,x,y,z):
        r = math.sqrt((x**2)+(y**2)+(z**2))
        return r
        
    def theta(self,x,y,z):
        r=self.radius(x,y,z)
        ang1 = math.acos(z/r)*360/(2*(math.pi)) #ang1 in degrees
        return ang1
        
    def phi(self,x,y):
        ang2 = math.atan(y/x)*360/(2*(math.pi))
        return ang2           
    
    
    def coordinates(self,info):#,info
        x = info.winfo.x.text().strip() #info.
        x = float(x)
    
        y = info.winfo.y.text().strip()
        y = float(y)
        
        z = info.winfo.z.text().strip()
        z = float(z)
        
        #info.winfo.xlbl_x.setText('%.2f' % (self.radius(x,y,z))) #info.winfo.x.setText(....) sets the actual input box the value.
        
        #info.winfo.xlbl_y.setText('%.2f' % (self.theta(x,y,z)))
        
        #info.winfo.xlbl_z.setText('%.2f' % (self.phi(x,y))) 
        
        info.winfo.radius.setText('%.2f' % (self.radius(x,y,z))) #radius, theta, phi in this case correspnds to the Radius etc. in captions() uptop
        info.winfo.theta.setText('%.2f' % (self.theta(x,y,z)))
        info.winfo.phi.setText('%.2f' % (self.phi(x,y)))
        
       # info.winfo.radius1.setText('hu')
     
    def field_info(self, viewer, fitsimage, info):
        # TODO: can this be made more efficient?
        chname = self.fv.get_channelName(fitsimage)
        chinfo = self.fv.get_channelInfo(chname)
        chname = chinfo.name
        obj = self.channel[chname]   
        
     
        obj.winfo.ra.setText(info.ra_txt)
        obj.winfo.dec.setText(info.dec_txt)
        
        
        obj.winfo.radius2.setText('%.2f' % (1.00))
        obj.winfo.theta2.setText(info.ra_txt)
        obj.winfo.phi2.setText(str(90-float(info.dec_txt)))
        #info.winfo.radius1.setText('%.2f' % (self.phi(self.x,self.y)))
        #info.winfo.radius1.setText('%.2f' %(info.ra_txt))
        
        #if info.has_key('ra_txt'):
            #obj.winfo.ra.setText(info.ra_txt)
            #obj.winfo.dec.setText(info.dec_txt)
        #if info.has_key('ra_lbl'):
            #obj.winfo.lbl_ra.setText(info.ra_lbl+':')
            #obj.winfo.lbl_dec.setText(info.dec_lbl+':')
            
        #################################    
        #self.dc = self.fv.getDrawClasses()
        #canvas = self.dc.DrawingCanvas()
        #canvas.enable_draw(True)
        #canvas.setSurface(self.fitsimage)
        #self.canvas = canvas
            
    def right_click(self):#,event):
        #self.name = 'table1'
        menu = self.canvas
        
        Action = menu.addAction("On menu")
        Action.triggered.connect(self.save_action)
        
        #menu.exec_(event.globalPos())
        
    def save_action(self):
        return "Right click to create action"
        
            
        

    def __str__(self):
        return 'info'
    
#END