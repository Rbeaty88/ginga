from ginga.qtw.QtHelp import QtGui, QtCore
import sys

class MyTableWidget(QtGui.QTableWidget):

    def __init__(self, name='Table1', parent=None):
        super(MyTableWidget, self).__init__(parent)
        self.name = name

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        Action = menu.addAction('This is' + self.name)
        Action.triggered.connect(self.printName)

        menu.exec_(event.globalPos())

    def printName(self):
        print "Action triggered from " + self.name
        
    def buildgui(self):
        layout = QtGui.QVBoxLayout(self)

        self.table1 = MyTableWidget(name='Table1', parent=self)
        self.table2 = MyTableWidget(name='Table2', parent=self)

        layout.addWidget(self.table1)
        layout.addWidget(self.table2)
        self.setLayout(layout)
        
        


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    main = MyTableWidget()
    main.show()

    app.exec_()