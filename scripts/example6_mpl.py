# -*- coding: utf-8 -*-

"""
   $ ./example6_mpl.py [fits file]

example6 is a simple calculator to go from cartesian coordinates to galactic or to celestial coordinates.
"""
import sys
import os
import numpy
import math



from ginga.qtw.QtHelp import QtGui
from ginga.qtw import QtHelp


class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.BuildGui()
        
    #def sayHello(self):
    #    try:
    #        self.qle_x.returnPressed.connect(self.Print_text)
    #        self.qle_y.returnPressed.connect(self.Print_text)
    #        self.qle_z.returnPressed.connect(self.Print_text)
    #    except Exception:
    #        pass
            
    def BuildGui(self):  
        
        #w = QtGui.QWidget() # top-level widget to hold everything  
        self.button = QtGui.QPushButton('Enter')
        self.button.clicked.connect(self.Print_text)
        
        self.button2 = QtGui.QPushButton('Close')
        #self.button2.clicked.connect(self.sayHello)
        #self.button.show()  

        self.lbl_x = QtGui.QLabel('x')
        self.qle_x = QtGui.QLineEdit(self)
        
        self.lbl_y = QtGui.QLabel('y')
        self.qle_y = QtGui.QLineEdit(self)
        
        self.lbl_z = QtGui.QLabel('z')
        self.qle_z = QtGui.QLineEdit(self)
        
       
        
        #self.qle_x.returnPressed.connect(self.Print_text)
        #self.qle_y.returnPressed.connect(self.Print_text)
        #self.qle_z.returnPressed.connect(self.Print_text)
        
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(2)

        grid.addWidget(self.lbl_x, 1, 0)
        grid.addWidget(self.qle_x, 1, 2)

        grid.addWidget(self.lbl_y, 2, 0)
        grid.addWidget(self.qle_y, 2, 2)

        grid.addWidget(self.lbl_z, 3, 0)
        grid.addWidget(self.qle_z, 3, 2)
        
        grid.addWidget(self.button,4,0)
        grid.addWidget(self.button2,5,0)
        
        self.setLayout(grid) 
        
        
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Transformation')
        self.show()
        
    def Radius(x,y,z):
        r = math.sqrt((x**2)+(y**2)+(z**2))
        print r
    
    def Theta(z,r):
        theta = math.acos(z/r)
        print theta
    
    def Phi(x,y):
        phi = math.atan(y/x)
        print phi
            
    def Print_text(self):
        try:
            textx = self.qle_x.text() #think about adding .strip as seen in Sample.py to eliminate the possibility of if white spaces occur
            if textx !='':
                textx = float(textx)
                textx = textx*3
                textx = str.format('%.15f' % textx)
                self.lbl_x.setText(textx)
                self.lbl_x.adjustSize()
                
            texty = self.qle_y.text()    
            if texty !='':
                texty = float(texty)
                texty = texty*8
                texty = str.format('%.15f' % texty)
                self.lbl_y.setText(texty)
                self.lbl_y.adjustSize()
                
            textz = self.qle_z.text()
            if textz !='':
                textz = float(textz)
                textz = textz*10
                textz = str.format('%.15f' % textz)
                self.lbl_z.setText(textz)#str.format('{0:.1f}' % textz.strip()))
                self.lbl_z.adjustSize()
                
            
        except Exception:
            pass
        
       
    
        
def main():
    
    app = QtGui.QApplication([]) #sys.argv
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()