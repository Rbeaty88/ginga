#
# Contents.py -- Table of Contents plugin for fits viewer
# 
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c)  Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
from ginga import GingaPlugin
from ginga.misc import Bunch

from ginga.qtw.QtHelp import QtGui, QtCore
import time

class Contents(GingaPlugin.GlobalPlugin):

    def __init__(self, fv):
        # superclass defines some variables for us, like logger
        super(Contents, self).__init__(fv)

        # For table-of-contents pane
        self.nameDict = {}
        self.columns = [('Name', 'NAME'),
                        ('Object', 'OBJECT'),
                        ('Date', 'DATE-OBS'),
                        ('Time UT', 'UT')]
        
        fv.set_callback('add-image', self.add_image)
        fv.set_callback('delete-channel', self.delete_channel)

    def build_gui(self, container):
        rvbox = container

        # create the Treeview
        treeview = QtGui.QTreeWidget()
        treeview.setColumnCount(len(self.columns))
        treeview.setSortingEnabled(True)
        treeview.setAlternatingRowColors(True)
        #treeview.itemClicked.connect(self.switch_image2)
        #treeview.itemDoubleClicked.connect(self.switch_image2)
        treeview.itemSelectionChanged.connect(self.switch_image3)
        self.treeview = treeview
        
        # create the column headers
        col = 0
        l = []
        for hdr, kwd in self.columns:
            l.append(hdr)
        treeview.setHeaderLabels(l)

        #self.treeview.connect('cursor-changed', self.switch_image2)

        rvbox.addWidget(treeview, stretch=1)


    def switch_image(self, chname, imname):
        fileDict = self.nameDict[chname]
        key = imname.lower()
        bnch = fileDict[key]
        path = bnch.path
        self.logger.debug("chname=%s name=%s path=%s" % (
            chname, imname, path))

        self.fv.switch_name(chname, bnch.NAME, path=path)

    def switch_image2(self, item, column):
        imname = str(item.text(0))
        parent = item.parent()
        if parent:
            chname = str(parent.text(0))
            print "parent is %s" % chname
            self.switch_image(chname, imname)

    def switch_image3(self):
        items = list(self.treeview.selectedItems())
        self.switch_image2(items[0], 0)
        
    def get_info(self, chname, name, image):
        path = image.get('path', None)
        bnch = Bunch.Bunch(NAME=name, CHNAME=chname, path=path)

        # Get header keywords of interest
        header = image.get_header()
        for x, key in self.columns[1:]:
            bnch[key] = header.get(key, 'N/A')
        return bnch
    
    def recreate_toc(self):
        self.logger.debug("Recreating table of contents...")
        toclist = list(self.nameDict.keys())
        toclist.sort()

        self.treeview.clear()

        for key in toclist:
            chitem = QtGui.QTreeWidgetItem(self.treeview, [chname])
            chitem.setFirstColumnSpanned(True)
            self.treeview.addTopLevelItem(chitem)

            fileDict = self.nameDict[key]
            filelist = list(fileDict.keys())
            filelist.remove('_chitem')
            fileDict['_chitem'] = chitem
            filelist.sort(key=str.lower)

            for fname in filelist:
                bnch = fileDict[fname]
                l = []
                for hdr, kwd in self.columns:
                    l.append(bnch[kwd])
        
                item = QtGui.QTreeWidgetItem(chitem, l)
                chitem.addChild(item)


    def add_image(self, viewer, chname, image):
        noname = 'Noname' + str(time.time())
        name = image.get('name', noname)
        path = image.get('path', None)

        if not self.nameDict.has_key(chname):
            # channel does not exist yet in contents--add it
            chitem = QtGui.QTreeWidgetItem(self.treeview, [chname])
            chitem.setFirstColumnSpanned(True)
            self.treeview.addTopLevelItem(chitem)
            fileDict = { '_chitem': chitem }
            self.nameDict[chname] = fileDict

        else:
            fileDict = self.nameDict[chname]
            chitem = fileDict['_chitem']
            
        key = name.lower()
        if fileDict.has_key(key):
            return

        bnch = self.get_info(chname, name, image)
        fileDict[key] = bnch
        l = []
        for hdr, kwd in self.columns:
            l.append(bnch[kwd])
        
        item = QtGui.QTreeWidgetItem(chitem, l)
        chitem.addChild(item)
        self.treeview.scrollToItem(item)
        self.logger.debug("%s added to Contents" % (name))


    def clear(self):
        self.nameDict = {}
        self.recreate_toc()

    def delete_channel(self, viewer, chinfo):
        """Called when a channel is deleted from the main interface.
        Parameter is chinfo (a bunch)."""
        chname = chinfo.name
        del self.nameDict[chname]
        self.recreate_toc()
        

    def __str__(self):
        return 'contents'
    
#END
