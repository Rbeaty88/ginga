
"""
   $ ./example9_mpl.py

example9_mpl.py is a simple calculator to go from cartesian coordinates to celestial coordinates. This GUI has some simple functionality
such as Enter, Clear, and Close buttons. This is a work in progress.

Some things to add:
    1) Add w = QtGui.QWidget() as the parent widget. So far I simply have
    2) Add more labels, so I don't have x - Radius etc. Also make it so that these labels do not get overwritten with the output.
    3) Substitute equations in Print_text() module with the modules that correspond to the equations. i.e. Example().self.Radius()
    
"""
#import os
#import numpy
import sys
import math

from ginga.qtw.QtHelp import QtGui
from ginga.qtw import QtHelp

class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.BuildGui() #needed so BuildGui() module is initialized on startup.
        
    def closeEvent(self, event):
        
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
        
    def BuildGui(self):  
        
        self.button = QtGui.QPushButton('Enter')
        self.button.clicked.connect(self.Print_text)
        
        self.button2 = QtGui.QPushButton('Clear')
        self.button2.clicked.connect(self.Clear)
        
        self.button3 = QtGui.QPushButton('Close')
        self.button3.clicked.connect(self.close) #self.close is from QtGui.QMainWindow
        

        self.lbl_x = QtGui.QLabel('x - Radius')
        self.qle_x = QtGui.QLineEdit(self)
        
        self.lbl_y = QtGui.QLabel('y - Theta (Degrees)')
        self.qle_y = QtGui.QLineEdit(self)
        
        self.lbl_z = QtGui.QLabel('z - Phi (Degrees)')
        self.qle_z = QtGui.QLineEdit(self)
        
#############
              
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
        grid.addWidget(self.button3,6,0)
        
###########                        
        
        self.setLayout(grid) 
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Cartesian_to_Spherical')
        self.show()
        
    def Radius(self,x,y,z):
        r = math.sqrt((x**2)+(y**2)+(z**2))
        print r
    
    def Theta(self,x,y,z):
        r=self.Radius(x,y,z)
        theta = math.acos(z/r)
        print theta
    
    def Phi(self,x,y):
        phi = math.atan(y/x)
        print phi
            
    def Print_text(self):
        
        textx = self.qle_x.text() #add .strip()?
        textx = float(textx)
        x1 = textx
               
        texty = self.qle_y.text()    
        texty = float(texty)
        y1 = texty
                    
        textz = self.qle_z.text()
        textz = float(textz)
        z1 = textz
                
        textx = math.sqrt((x1**2)+(y1**2)+(z1**2))#Example().Radius(x1,y1,z1)
        textx = str.format('%.2f' % textx)
        textx = str.format(textx)
        self.lbl_x.setText(textx)
        self.lbl_x.adjustSize()
        
        r = math.sqrt((x1**2)+(y1**2)+(z1**2))
        theta = math.acos(z1/r)*360/(2*(math.pi))
        texty = theta
        texty = str.format('%.2f' % texty)
        self.lbl_y.setText(texty)
        self.lbl_y.adjustSize()
        
        
        phi = math.atan(y1/x1)*360/(2*(math.pi))
        textz = phi
        textz = str.format('%.2f' % textz)
        self.lbl_z.setText(textz)
        self.lbl_z.adjustSize()
            
    def Clear(self):
        self.lbl_x.setText('x - Radius')
        self.lbl_y.setText('y - Theta (Degrees)')
        self.lbl_z.setText('z - Phi (Degrees)')
        
        
def main():
    
    app = QtGui.QApplication([]) #sys.argv
    ex = Example()
    #ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()