#
# GtkHelp.py -- customized Gtk widgets
# 
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c) Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
import time
import math

from ginga.gtkw import gtksel
import gtk
import gobject

from ginga.misc import Bunch, Callback


class MDIWorkspace(gtk.Layout):
    """
    This is a work in progress!
    """
    def __init__(self):
        super(MDIWorkspace, self).__init__()

        self.children = []
        self.selected_child = None
        self.kbdmouse_mask = 0

        self.connect("motion_notify_event", self.motion_notify_event)
        self.connect("button_press_event", self.button_press_event)
        self.connect("button_release_event", self.button_release_event)
        mask = self.get_events()
        self.set_events(mask
                        | gtk.gdk.ENTER_NOTIFY_MASK
                        | gtk.gdk.LEAVE_NOTIFY_MASK
                        | gtk.gdk.FOCUS_CHANGE_MASK
                        | gtk.gdk.STRUCTURE_MASK
                        | gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.KEY_PRESS_MASK
                        | gtk.gdk.KEY_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.POINTER_MOTION_HINT_MASK
                        | gtk.gdk.SCROLL_MASK)

    def append_page(self, widget, label):
        vbox = gtk.VBox()
        evbox = gtk.EventBox()
        evbox.add(label)
        evbox.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("yellow"))
        evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("skyblue"))
        vbox.pack_start(evbox, fill=False, expand=False)
        vbox.pack_start(widget, fill=True, expand=True)

        fr = gtk.Frame()
        fr.set_border_width(10)
        fr.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        fr.add(vbox)
        #fr.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        fr.show_all()
        
        evbox.connect("button_press_event", self.select_child_cb, fr)
        
        bnch = Bunch.Bunch(widget=widget, window=fr)
        self.children.append(bnch)

        self.put(fr, 10, 10)

    def set_tab_reorderable(self, w, tf):
        pass
    def set_tab_detachable(self, w, tf):
        pass

    def page_num(self, widget):
        idx = 0
        for bnch in self.children:
            if bnch.widget == widget:
                return idx
            idx += 1
        return -1

    def set_current_page(self, idx):
        bnch = self.children[idx]
        window = bnch.window
        window.show()
        
    def remove_page(self, idx):
        bnch = self.children[idx]
        window = bnch.window
        #self.remove(window)
        
    def select_child_cb(self, layout, event, widget):
        ex = event.x; ey = event.y
        x, y, width, height = widget.get_allocation()
        dx, dy = ex - x, ey - y
        self.selected_child = Bunch.Bunch(widget=widget,
                                          cr = self.setup_cr(self.bin_window),
                                          dx=x, dy=y, wd=width, ht=height)
        return False
       
    def button_press_event(self, widget, event):
        # event.button, event.x, event.y
        x = event.x; y = event.y
        button = self.kbdmouse_mask
        if event.button != 0:
            button |= 0x1 << (event.button - 1)
        print ("button event at %dx%d, button=%x" % (x, y, button))

    def setup_cr(self, drawable):
        cr = drawable.cairo_create()
        cr.set_line_width(2)
        cr.set_dash([ 3.0, 4.0, 6.0, 4.0], 5.0)
        return cr


    def button_release_event(self, widget, event):
        # event.button, event.x, event.y
        x = event.x; y = event.y
        button = self.kbdmouse_mask
        if event.button != 0:
            button |= 0x1 << (event.button - 1)
        print ("button release at %dx%d button=%x" % (x, y, button))
        dst_x, dst_y = x, y
        if self.selected_child != None:
            self.move(self.selected_child.widget, dst_x, dst_y)
            self.selected_child = None

    def motion_notify_event(self, widget, event):
        button = self.kbdmouse_mask
        if event.is_hint:
            return
        else:
            x, y, state = event.x, event.y, event.state
            #self.last_win_x, self.last_win_y = x, y
        
        if state & gtk.gdk.BUTTON1_MASK:
            button |= 0x1
        elif state & gtk.gdk.BUTTON2_MASK:
            button |= 0x2
        elif state & gtk.gdk.BUTTON3_MASK:
            button |= 0x4
        print ("motion event at %dx%d, button=%x" % (x, y, button))

        if (button & 0x1) and (self.selected_child != None):
            bnch = self.selected_child
            x += bnch.dx
            y -= bnch.dy
            bnch.cr.rectangle(x, y, bnch.wd, bnch.ht)
            bnch.cr.stroke_preserve()

class GridWorkspace(gtk.Table):

    def __init__(self):
        super(GridWorkspace, self).__init__()
        
        self.set_row_spacings(2)
        self.set_col_spacings(2)
        self.widgets = []
        self.labels = {}

    def _relayout(self):
        # calculate number of rows and cols, try to maintain a square
        # TODO: take into account the window geometry
        num_widgets = len(self.widgets)
        rows = int(round(math.sqrt(num_widgets)))
        cols = rows
        if rows**2 < num_widgets:
            cols += 1

        # remove all the old widgets
        for w in self.widgets:
            self.remove(w)

        self.resize(rows, cols)

        # add them back in, in a grid
        for i in xrange(0, rows):
            for j in xrange(0, cols):
                index = i*cols + j
                if index < num_widgets:
                    widget = self.widgets[index]
                self.attach(widget, j, j+1, i, i+1,
                            xoptions=gtk.FILL|gtk.EXPAND,
                            yoptions=gtk.FILL|gtk.EXPAND,
                            xpadding=0, ypadding=0)

    def append_page(self, widget, label):
        self.widgets.append(widget)
        self.labels[widget] = label
        self._relayout()

    def remove_page(self, idx):
        widget = self.getWidget(idx)
        del self.labels[widget]
        self.widgets.remove(widget)
        self.remove(widget)
        self._relayout()

    def page_num(self, widget):
        try:
            return self.widgets.index(widget)
        except (IndexError, ValueError), e:
            return -1

    def getWidget(self, index):
        return self.widgets[index]

    def set_tab_reorderable(self, w, tf):
        pass
    def set_tab_detachable(self, w, tf):
        pass

    def get_tab_label(self, widget):
        return self.labels[widget]

    def set_current_page(self, idx):
        widget = self.getWidget(idx)
        self.set_focus_child(widget)
        

class WidgetMask(object):
    def __init__(self, *args):
        self.cb_fn = None
        self.cb_args = []
        self.cb_kwdargs = {}

        self.connected = False
        self.changed = False

    def sconnect(self, signal, cb_fn, *args, **kwdargs):
        self.cb_fn = cb_fn
        self.cb_args = args
        self.cb_kwdargs = kwdargs

        self.connect(signal, self.cb)
        self.connected = True

    def change(self):
        if self.connected:
            self.changed = True
            
    def cb(self, *args):
        if self.changed:
            self.changed = False
            #print "punted callback!"
            return

        #print "callback is passed through"
        newargs = list(args)
        newargs.extend(self.cb_args)
        kwdargs = self.cb_kwdargs.copy()
        return self.cb_fn(*newargs, **kwdargs)


class TopLevel(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

class CheckButton(WidgetMask, gtk.CheckButton):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.CheckButton.__init__(self, *args, **kwdargs)

    def set_active(self, newval):
        oldval = self.get_active()
        if oldval != newval:
            self.change()

        super(CheckButton, self).set_active(newval)

class ToggleButton(WidgetMask, gtk.ToggleButton):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.ToggleButton.__init__(self, *args, **kwdargs)

    def set_active(self, newval):
        oldval = self.get_active()
        if oldval != newval:
            self.change()

        super(ToggleButton, self).set_active(newval)

    def toggle(self):
        oldval = self.get_active()
        newval = not oldval
        super(ToggleButton, self).set_active(newval)
        
    
class RadioButton(WidgetMask, gtk.RadioButton):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.RadioButton.__init__(self, *args, **kwdargs)

    def set_active(self, newval):
        oldval = self.get_active()
        if oldval != newval:
            self.change()

        super(RadioButton, self).set_active(newval)

    def toggle(self):
        oldval = self.get_active()
        newval = not oldval
        super(RadioButton, self).set_active(newval)
        
    
class CheckMenuItem(WidgetMask, gtk.CheckMenuItem):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.CheckMenuItem.__init__(self, *args, **kwdargs)

    def set_active(self, newval):
        oldval = self.get_active()
        if oldval != newval:
            self.change()

        super(CheckMenuItem, self).set_active(newval)

    
class SpinButton(WidgetMask, gtk.SpinButton):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.SpinButton.__init__(self, *args, **kwdargs)

    def set_value(self, newval):
        oldval = self.get_value()
        if oldval != newval:
            self.change()

        super(SpinButton, self).set_value(newval)

    
class HScale(WidgetMask, gtk.HScale):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.HScale.__init__(self, *args, **kwdargs)

    def set_value(self, newval):
        oldval = self.get_value()
        if oldval != newval:
            self.change()

        super(HScale, self).set_value(newval)

class VScale(WidgetMask, gtk.VScale):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.VScale.__init__(self, *args, **kwdargs)

    def set_value(self, newval):
        oldval = self.get_value()
        if oldval != newval:
            self.change()

        super(VScale, self).set_value(newval)

    
class ComboBox(WidgetMask, gtk.ComboBox):
    def __init__(self, *args, **kwdargs):
        WidgetMask.__init__(self)
        gtk.ComboBox.__init__(self, *args, **kwdargs)

    def set_active(self, newval):
        oldval = self.get_active()
        if oldval != newval:
            self.change()

        super(ComboBox, self).set_active(newval)

    def insert_alpha(self, text):
        model = self.get_model()
        tup = (text, )
        j = 0
        for i in xrange(len(model)):
            j = i
            if model[i][0] > text:
                model.insert(j, tup)
                return
        model.insert(j+1, tup)

    def insert_text(self, idx, text):
        model = self.get_model()
        tup = (text, )
        model.insert(idx, tup)

    def delete_alpha(self, text):
        model = self.get_model()
        for i in xrange(len(model)):
            if model[i][0] == text:
                del model[i]
                return

    def clear(self):
        model = self.get_model()
        model.clear()

    def show_text(self, text):
        model = self.get_model()
        for i in xrange(len(model)):
            if model[i][0] == text:
                self.set_active(i)
                return

class Notebook(gtk.Notebook):
    def set_group_id(self, id):
        if not gtksel.have_gtk3:
            super(Notebook, self).set_group_id(id)
        else:
            super(Notebook, self).set_group_name(str(id))

    
def combo_box_new_text():
    liststore = gtk.ListStore(gobject.TYPE_STRING)
    combobox = ComboBox()
    combobox.set_model(liststore)
    cell = gtk.CellRendererText()
    combobox.pack_start(cell, True)
    combobox.add_attribute(cell, 'text', 0)
    return combobox


class Dialog(gtk.Dialog):
    def __init__(self, title=None, flags=None, buttons=None,
                 callback=None):

        button_list = []
        for name, val in buttons:
            button_list.extend([name, val])

        super(Dialog, self).__init__(title=title, flags=flags,
                                     buttons=tuple(button_list))
        #self.w.connect("close", self.close)
        if callback:
            self.connect("response", callback)

        
class Desktop(Callback.Callbacks):

    def __init__(self):
        super(Desktop, self).__init__()
        
        # for tabs
        self.tab = Bunch.caselessDict()
        self.tabcount = 0
        self.notebooks = Bunch.caselessDict()

        self.toplevels = []

        for name in ('page-switch', 'page-select'):
            self.enable_callback(name)
        
    # --- Tab Handling ---
    
    def make_ws(self, name=None, group=1, show_tabs=True, show_border=False,
                detachable=True, tabpos=None, scrollable=True, wstype='nb'):
        if not name:
            name = str(time.time())
        if wstype == 'nb':
            nb = gtk.Notebook()
            if tabpos == None:
                tabpos = gtk.POS_TOP
            # Allows drag-and-drop between notebooks
            if not gtksel.have_gtk3:
                nb.set_group_id(group)
            if detachable:
                nb.connect("create-window", self.detach_page_cb, group)
            nb.connect("switch-page", self.switch_page_cb)
            nb.set_tab_pos(tabpos)
            nb.set_scrollable(scrollable)
            nb.set_show_tabs(show_tabs)
            nb.set_show_border(show_border)
            #nb.set_border_width(2)
            widget = nb

        elif wstype == 'grid':
            nb = GridWorkspace()
            widget = nb

        else:
            nb = Workspace()
            widget = gtk.ScrolledWindow()
            widget.set_border_width(2)
            widget.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            widget.add(nb)

        bnch = Bunch.Bunch(nb=nb, name=name, widget=widget, group=group)
        self.notebooks[name] = bnch
        return bnch

    def get_nb(self, name):
        return self.notebooks[name].nb
        
    def get_wsnames(self, group=1):
        res = []
        for name in self.notebooks.keys():
            bnch = self.notebooks[name]
            if group == None:
                res.append(name)
            elif group == bnch.group:
                res.append(name)
        return res
    
    def add_tab(self, wsname, widget, group, labelname, tabname=None,
                data=None):
        tab_w = self.get_nb(wsname)
        self.tabcount += 1
        if not tabname:
            tabname = labelname
            if self.tab.has_key(tabname):
                tabname = 'tab%d' % self.tabcount
            
        label = gtk.Label(labelname)
        evbox = gtk.EventBox()
        evbox.add(label)
        evbox.show_all()
        tab_w.append_page(widget, evbox)
        bnch = Bunch.Bunch(widget=widget, name=labelname,
                           tabname=tabname, data=data)
        self.tab[tabname] = bnch
        evbox.connect("button-press-event", self.select_cb, labelname, data)
        tab_w.set_tab_reorderable(widget, True)
        tab_w.set_tab_detachable(widget, True)
        widget.show()
        return tabname

    def _find_nb(self, tabname):
        widget = self.tab[tabname].widget
        for bnch in self.notebooks.values():
            nb = bnch.nb
            page_num = nb.page_num(widget)
            if page_num < 0:
                continue
            return (nb, page_num)
        return (None, None)

    def _find_tab(self, widget):
        for key, bnch in self.tab.items():
            if widget == bnch.widget:
                return bnch
        return None

    def select_cb(self, widget, event, name, data):
        self.make_callback('page-select', name, data)
        
    def raise_tab(self, tabname):
        nb, page_num = self._find_nb(tabname)
        if nb:
            nb.set_current_page(page_num)

            # bring this window to the user's attention
            win = nb.get_window()
            if win:
                if hasattr(win, 'present'):
                    # gtk3 ?
                    win.present()
                else:
                    # gtk2
                    win.show()

    def remove_tab(self, tabname):
        nb, page_num = self._find_nb(tabname)
        if nb:
            nb.remove_page(page_num)
            del self.tab[tabname]
            return

    def highlight_tab(self, tabname, onoff):
        nb, page_num = self._find_nb(tabname)
        if nb:
            widget = self.tab[tabname].widget
            lbl = nb.get_tab_label(widget)
            name = self.tab[tabname].name
            if onoff:
                lbl.modify_bg(gtk.STATE_NORMAL,
                              gtk.gdk.color_parse('palegreen'))
            else:
                lbl.modify_bg(gtk.STATE_NORMAL,
                              gtk.gdk.color_parse('grey'))

    def add_toplevel(self, widget, wsname, width=700, height=700):
        topw = TopLevel()
        topw.set_default_size(width, height)
        self.toplevels.append(topw)
        topw.set_title(wsname)
        topw.set_border_width(0)

        topw.add(widget)
        topw.show_all()
        return topw

    def create_toplevel_ws(self, width, height, group, x=None, y=None):
        # create top level workspace
        root = gtk.Window(gtk.WINDOW_TOPLEVEL)
        ## root.set_title(title)
        # TODO: this needs to be more sophisticated
        root.set_border_width(2)
        root.set_default_size(width, height)
        root.show()
        #self.update_pending()

        vbox = gtk.VBox()
        root.add(vbox)

        menubar = gtk.MenuBar()
        vbox.pack_start(menubar, fill=True, expand=False)

        # create a Window pulldown menu, and add it to the menu bar
        winmenu = gtk.Menu()
        item = gtk.MenuItem(label="Window")
        menubar.append(item)
        item.show()
        item.set_submenu(winmenu)

        ## w = gtk.MenuItem("Take Tab")
        ## winmenu.append(w)
        #w.connect("activate", lambda w: self.gui_take_tab())

        sep = gtk.SeparatorMenuItem()
        winmenu.append(sep)
        quit_item = gtk.MenuItem(label="Close")
        winmenu.append(quit_item)
        #quit_item.connect_object ("activate", self.quit, "file.exit")
        quit_item.show()

        bnch = self.make_ws(group=group)
        vbox.pack_start(bnch.widget, padding=2, fill=True, expand=True)
        root.connect("delete_event", lambda w, e: self.close_page_cb(bnch, root))

        lbl = gtk.Statusbar()
        lbl.set_has_resize_grip(True)
        vbox.pack_end(lbl, expand=False, fill=True, padding=2)

        vbox.show_all()
        root.show_all()
        if x != None:
            win = root.get_window()
            win.move(x, y)
        return bnch

    def close_page_cb(self, bnch, root):
        children = bnch.nb.get_children()
        if len(children) == 0:
            del self.notebooks[bnch.name]
            root.destroy()
        return True
    
    def detach_page_cb(self, source, widget, x, y, group):
        # Detach page to new top-level workspace
        ## page = self.widgetToPage(widget)
        ## if not page:
        ##     return None
        xo, yo, width, height = widget.get_allocation()
        
        bnch = self.create_toplevel_ws(width, height, group, x=x, y=y)
        return bnch.nb

    def switch_page_cb(self, nbw, gptr, page_num):
        pagew = nbw.get_nth_page(page_num)
        bnch = self._find_tab(pagew)
        if bnch != None:
            self.make_callback('page-switch', bnch.name, bnch.data)
        return False

    def make_desktop(self, layout, widgetDict=None):
        if widgetDict == None:
            widgetDict = {}
            
        def process_common_params(widget, inparams):
            params = Bunch.Bunch(name=None, height=-1, width=-1, xpos=-1, ypos=-1)
            params.update(inparams)
            
            if params.name:
                widgetDict[params.name] = widget

            if (params.width >= 0) or (params.height >= 0):
                widget.set_size_request(params.width, params.height)
                #pass

            # User wants to place window somewhere
            if params.xpos >= 0:
                #widget.show()
                win = widget.get_window()
                if win != None:
                    win.move(params.xpos, params.ypos)

            return params

        def make_widget(kind, paramdict, args, pack):
            kind = kind.lower()

            # Process workspace parameters
            params = Bunch.Bunch(name=None, title=None, height=-1,
                                 width=-1, group=1, show_tabs=True,
                                 show_border=False, scrollable=True,
                                 detachable=True, tabpos=gtk.POS_TOP)
            params.update(paramdict)

            if kind == 'widget':
                widget = args[0]

            elif kind == 'ws':
                group = int(params.group)
                widget = self.make_ws(name=params.name, group=group,
                                      show_tabs=params.show_tabs,
                                      show_border=params.show_border,
                                      detachable=params.detachable,
                                      tabpos=params.tabpos,
                                      scrollable=params.scrollable).widget

            # If a title was passed as a parameter, then make a frame to
            # wrap the widget using the title.
            if params.title:
                fr = gtk.Frame(label=' '+params.title+' ')
                fr.set_shadow_type(gtk.SHADOW_ETCHED_IN)
                fr.set_label_align(0.10, 0.5)
                fr.add(widget)
                pack(fr)
            else:
                pack(widget)

            process_common_params(widget, params)
            
            if (kind == 'ws') and (len(args) > 0):
                # <-- Notebook ws specified a sub-layout.  We expect a list
                # of tabname, layout pairs--iterate over these and add them
                # to the workspace as tabs.
                for tabname, layout in args[0]:
                    def pack(w):
                        # ?why should group be the same as parent group?
                        self.add_tab(params.name, w, group,
                                     tabname, tabname.lower())

                    make(layout, pack)

            widget.show_all()
            return widget

        # Horizontal adjustable panel
        def horz(params, cols, pack):
            if len(cols) > 2:
                hpaned = gtk.HPaned()
                make(cols[0], lambda w: hpaned.pack1(w, resize=True, shrink=True))
                horz(params, cols[1:],
                     lambda w: hpaned.pack2(w, resize=True, shrink=True))
                pack(hpaned)

            elif len(cols) == 2:
                hpaned = gtk.HPaned()
                make(cols[0], lambda w: hpaned.pack1(w, resize=True, shrink=True))
                make(cols[1], lambda w: hpaned.pack2(w, resize=True, shrink=True))
                pack(hpaned)

            elif len(cols) == 1:
                hpaned = gtk.HBox()
                make(cols[0], lambda w: hpaned.pack_start(w, expand=True, fill=True)) #?
                pack(hpaned)

            process_common_params(hpaned, params)
            
            hpaned.show_all()

        # Vertical adjustable panel
        def vert(params, rows, pack):
            if len(rows) > 2:
                vpaned = gtk.VPaned()
                make(rows[0], lambda w: vpaned.pack1(w, resize=True, shrink=True))
                vert(params, rows[1:],
                     lambda w: vpaned.pack2(w, resize=True, shrink=True))
                pack(vpaned)

            elif len(rows) == 2:
                vpaned = gtk.VPaned()
                make(rows[0], lambda w: vpaned.pack1(w, resize=True, shrink=True))
                make(rows[1], lambda w: vpaned.pack2(w, resize=True, shrink=True))
                pack(vpaned)

            elif len(rows) == 1:
                vpaned = gtk.VBox()
                make(rows[0], lambda w: vpaned.pack_start(w, expand=True, fill=True))  #?
                pack(vpaned)

            process_common_params(vpaned, params)
            
            vpaned.show_all()

        # Horizontal fixed array
        def hbox(params, cols, pack):
            widget = gtk.HBox()

            for dct in cols:
                if isinstance(dct, dict):
                    #fill = dct.get('fill', True)
                    #expand = dct.get('expand', True)  #?
                    fill = True
                    expand = (dct.get('stretch', 1) == 1)
                    col = dct.get('col', None)
                else:
                    # assume a list defining the col
                    fill = expand = True
                    col = dct
                if col != None:
                    make(col, lambda w: widget.pack_start(w,
                                                          fill=fill,
                                                          expand=expand))
            process_common_params(widget, params)
            
            widget.show_all()
            pack(widget)

        # Vertical fixed array
        def vbox(params, rows, pack):
            widget = gtk.VBox()

            for dct in rows:
                if isinstance(dct, dict):
                    #fill = dct.get('fill', True)
                    #expand = dct.get('expand', True)  #?
                    fill = True
                    expand = (dct.get('stretch', 1) == 1)
                    row = dct.get('row', None)
                else:
                    # assume a list defining the row
                    fill = expand = True
                    row = dct
                if row != None:
                    make(row, lambda w: widget.pack_start(w,
                                                          fill=fill,
                                                          expand=expand))
            process_common_params(widget, params)

            widget.show_all()
            pack(widget)

        # Sequence of separate items
        def seq(params, cols, pack):
            def mypack(w):
                topw = TopLevel()
                ## topw.set_title(title)
                topw.set_border_width(0)
                topw.add(w)
                self.toplevels.append(topw)
                topw.show_all()
                
            for dct in cols:
                if isinstance(dct, dict):
                    #fill = dct.get('fill', True)
                    #expand = dct.get('expand', True)  #?
                    fill = True
                    expand = (dct.get('stretch', 1) == 1)
                    col = dct.get('col', None)
                else:
                    # assume a list defining the col
                    fill = expand = True
                    col = dct
                if col != None:
                    make(col, mypack)

            widget = gtk.Label("Placeholder")
            pack(widget)
            

        def make(constituents, pack):
            kind = constituents[0]
            params = constituents[1]
            if len(constituents) > 2:
                rest = constituents[2:]
            else:
                rest = []

            if kind == 'vpanel':
                vert(params, rest, pack)
            elif kind == 'hpanel':
                horz(params, rest, pack)
            elif kind == 'vbox':
                vbox(params, rest, pack)
            elif kind == 'hbox':
                hbox(params, rest, pack)
            elif kind == 'seq':
                seq(params, rest, pack)
            elif kind in ('ws', 'widget'):
                make_widget(kind, params, rest, pack)

        make(layout, lambda w: None)

def _name_mangle(name, pfx=''):
    newname = []
    for c in name.lower():
        if not (c.isalpha() or c.isdigit() or (c == '_')):
            newname.append('_')
        else:
            newname.append(c)
    return pfx + ''.join(newname)
    
def _make_widget(tup, ns):
    swap = False
    title = tup[0]
    if not title.startswith('@'):
        name  = _name_mangle(title)
        w1 = gtk.Label(title + ':')
        w1.set_alignment(0.95, 0.5)
    else:
        # invisible title
        swap = True
        name  = _name_mangle(title[1:])
        w1 = gtk.Label('')

    wtype = tup[1]
    if wtype == 'label':
        w2 = gtk.Label('')
        w2.set_alignment(0.05, 0.5)
    elif wtype == 'xlabel':
        w2 = gtk.Label('')
        w2.set_alignment(0.05, 0.5)
        name = 'xlbl_' + name
    elif wtype == 'entry':
        w2 = gtk.Entry()
        w2.set_width_chars(12)
    elif wtype == 'combobox':
        w2 = combo_box_new_text()
    elif wtype == 'spinbutton':
        w2 = SpinButton()
    elif wtype == 'vbox':
        w2 = gtk.VBox()
    elif wtype == 'hbox':
        w2 = gtk.HBox()
    elif wtype == 'hscale':
        w2 = HScale()
    elif wtype == 'vscale':
        w2 = VScale()
    elif wtype == 'checkbutton':
        w1 = gtk.Label('')
        w2 = CheckButton(title)
        w2.set_mode(True)
        swap = True
    elif wtype == 'radiobutton':
        w1 = gtk.Label('')
        w2 = RadioButton(title)
        swap = True
    elif wtype == 'togglebutton':
        w1 = gtk.Label('')
        w2 = ToggleButton(title)
        w2.set_mode(True)
        swap = True
    elif wtype == 'button':
        w1 = gtk.Label('')
        w2 = gtk.Button(title)
        swap = True
    elif wtype == 'spacer':
        w1 = QtGui.QLabel('')
        w2 = QtGui.QLabel('')
    else:
        raise ValueError("Bad wtype=%s" % wtype)

    lblname = 'lbl_%s' % (name)
    if swap:
        w1, w2 = w2, w1
        ns[name] = w1
        ns[lblname] = w2
    else:
        ns[name] = w2
        ns[lblname] = w1
    return (w1, w2)


def build_info(captions):
    vbox = gtk.VBox(spacing=2)

    numrows = len(captions)
    numcols = reduce(lambda acc, tup: max(acc, len(tup)), captions, 0)
    table = gtk.Table(rows=numrows, columns=numcols)
    table.set_row_spacings(2)
    table.set_col_spacings(4)
    vbox.pack_start(table, expand=False)

    wb = Bunch.Bunch()
    row = 0
    for tup in captions:
        col = 0
        while col < numcols:
            if col < len(tup):
                tup1 = tup[col:col+2]
                w1, w2 = _make_widget(tup1, wb)
                table.attach(w1, col, col+1, row, row+1,
                             xoptions=gtk.FILL, yoptions=gtk.FILL,
                             xpadding=1, ypadding=1)
                table.attach(w2, col+1, col+2, row, row+1,
                             xoptions=gtk.FILL, yoptions=gtk.FILL,
                             xpadding=1, ypadding=1)
            col += 2
        row += 1

    vbox.show_all()

    return vbox, wb


def _get_widget(title, wtype):
    if wtype == 'label':
        w = gtk.Label(title)
        w.set_alignment(0.95, 0.5)
    elif wtype == 'llabel':
        w = gtk.Label(title)
        w.set_alignment(0.05, 0.95)
    elif wtype == 'entry':
        w = gtk.Entry()
        w.set_width_chars(12)
    elif wtype == 'combobox':
        w = combo_box_new_text()
    elif wtype == 'spinbutton':
        w = SpinButton()
    elif wtype == 'vbox':
        w = gtk.VBox()
    elif wtype == 'hbox':
        w = gtk.HBox()
    elif wtype == 'hscale':
        w = HScale()
    elif wtype == 'vscale':
        w = VScale()
    elif wtype == 'checkbutton':
        w = CheckButton(title)
        w.set_mode(True)
    elif wtype == 'radiobutton':
        w = RadioButton(title)
    elif wtype == 'togglebutton':
        w = ToggleButton(title)
        w.set_mode(True)
    elif wtype == 'button':
        w = gtk.Button(title)
    elif wtype == 'spacer':
        w = QtGui.QLabel('')
    else:
        raise ValueError("Bad wtype=%s" % wtype)

    return w


def build_info2(captions):
    vbox = gtk.VBox(spacing=2)

    numrows = len(captions)
    numcols = reduce(lambda acc, tup: max(acc, len(tup)), captions, 0)
    if (numcols % 2) != 0:
        raise ValueError("Column spec is not an even number")
    numcols /= 2
    table = gtk.Table(rows=numrows, columns=numcols)
    table.set_row_spacings(2)
    table.set_col_spacings(4)
    vbox.pack_start(table, expand=False)

    wb = Bunch.Bunch()
    row = 0
    for tup in captions:
        col = 0
        while col < numcols:
            idx = col * 2
            if idx < len(tup):
                title, wtype = tup[idx:idx+2]
                if not title.endswith(':'):
                    name = _name_mangle(title)
                else:
                    name = _name_mangle('lbl_'+title[:-1])
                w = _get_widget(title, wtype)
                table.attach(w, col, col+1, row, row+1,
                             xoptions=gtk.FILL, yoptions=gtk.FILL,
                             xpadding=1, ypadding=1)
                wb[name] = w
            col += 1
        row += 1

    vbox.show_all()

    return vbox, wb

class ParamSet(Callback.Callbacks):
    def __init__(self, logger, params):
        super(ParamSet, self).__init__()
        
        self.logger = logger
        self.paramlst = []
        self.params = params
        self.widgets = {}

        for name in ('changed', ):
            self.enable_callback(name)
        
    def build_params(self, paramlst):
        # construct a set of widgets for the parameters
        captions = []
        for param in paramlst:
            title = param.get('time', param.name)

            captions.append((title, 'xlabel', '@'+param.name, 'entry'))

        w, b = build_info(captions)

        # fill with default values and tool tips
        for param in paramlst:
            name = param.name

            # if we have a cached value for the parameter, use it
            if self.params.has_key(name):
                value = self.params[name]
                b[name].set_text(str(value))

            # otherwise initialize to the default value, if available
            elif param.has_key('default'):
                value = param.default
                b[name].set_text(str(value))
                self.params[name] = value

            if param.has_key('description'):
                b[name].set_tooltip_text(param.description)

            b[name].connect('activate', self._value_changed_cb)
            
        self.paramlst = paramlst
        self.widgets = b

        return w

    def _get_params(self):
        for param in self.paramlst:
            w = self.widgets[param.name]
            value = w.get_text()
            if param.has_key('type'):
                value = param.type(value)
            self.params[param.name] = value

    def sync_params(self):
        for param in self.paramlst:
            key = param.name
            w = self.widgets[key]
            if self.params.has_key(key):
                value = self.params[key]
                w.set_text(str(value))

    def get_params(self):
        self._get_params()
        return self.params
    
    def _value_changed_cb(self, w):
        self._get_params()
        self.make_callback('changed', self.params)
        
#END
