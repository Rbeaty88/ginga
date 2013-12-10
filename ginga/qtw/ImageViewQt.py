#
# ImageViewQt.py -- classes for the display of FITS files in Qt widgets
# 
# Eric Jeschke (eric@naoj.org) 
#
# Copyright (c) Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
import sys, os
import math
import numpy
import StringIO

from ginga.qtw.QtHelp import QtGui, QtCore
from ginga import ImageView, Mixins, Bindings

moduleHome = os.path.split(sys.modules[__name__].__file__)[0]
icon_dir = os.path.abspath(os.path.join(moduleHome, '..', 'icons'))


class ImageViewQtError(ImageView.ImageViewError):
    pass

    
class RenderGraphicsView(QtGui.QGraphicsView):

    def __init__(self, *args, **kwdargs):
        super(RenderGraphicsView, self).__init__(*args, **kwdargs)
    
        self.fitsimage = None
        self.pixmap = None

    def drawBackground(self, painter, rect):
        """When an area of the window is exposed, we just copy out of the
        server-side, off-screen pixmap to that area.
        """
        if not self.pixmap:
            return
        x1, y1, x2, y2 = rect.getCoords()
        width = x2 - x1
        height = y2 - y1

        # redraw the screen from backing pixmap
        rect = QtCore.QRect(x1, y1, width, height)
        painter.drawPixmap(rect, self.pixmap, rect)

    def resizeEvent(self, event):
        rect = self.geometry()
        x1, y1, x2, y2 = rect.getCoords()
        width = x2 - x1
        height = y2 - y1
       
        self.fitsimage.configure(width, height)

    def sizeHint(self):
        width, height = 300, 300
        if self.fitsimage != None:
            width, height = self.fitsimage.get_desired_size()
        return QtCore.QSize(width, height)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
    
        
class RenderWidget(QtGui.QWidget):

    def __init__(self, *args, **kwdargs):
        super(RenderWidget, self).__init__(*args, **kwdargs)

        self.fitsimage = None
        self.pixmap = None
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        
    def paintEvent(self, event):
        """When an area of the window is exposed, we just copy out of the
        server-side, off-screen pixmap to that area.
        """
        if not self.pixmap:
            return
        rect = event.rect()
        x1, y1, x2, y2 = rect.getCoords()
        width = x2 - x1
        height = y2 - y1

        # redraw the screen from backing pixmap
        painter = QtGui.QPainter(self)
        rect = QtCore.QRect(x1, y1, width, height)
        painter.drawPixmap(rect, self.pixmap, rect)
        
    def resizeEvent(self, event):
        rect = self.geometry()
        x1, y1, x2, y2 = rect.getCoords()
        width = x2 - x1
        height = y2 - y1
       
        self.fitsimage.configure(width, height)
        #self.update()

    def sizeHint(self):
        width, height = 300, 300
        if self.fitsimage != None:
            width, height = self.fitsimage.get_desired_size()
        return QtCore.QSize(width, height)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap


class ImageViewQt(ImageView.ImageViewBase):

    def __init__(self, logger=None, rgbmap=None, settings=None, render=None):
        ImageView.ImageViewBase.__init__(self, logger=logger,
                                         rgbmap=rgbmap, settings=settings)

        if render == None:
            render = 'widget'
        self.wtype = render
        if self.wtype == 'widget':
            self.imgwin = RenderWidget()
        elif self.wtype == 'scene':
            self.scene = QtGui.QGraphicsScene()
            self.imgwin = RenderGraphicsView(self.scene)
        else:
            raise ImageViewQtError("Undefined render type: '%s'" % (render))
        self.imgwin.fitsimage = self
        self.pixmap = None
        # Qt expects 32bit BGRA data for color images
        self._rgb_order = 'BGRA'
        
        self.t_.setDefaults(show_pan_position=False,
                            onscreen_ff='Sans Serif')

        self.message = None
        self.msgtimer = QtCore.QTimer()
        self.msgtimer.timeout.connect(self.onscreen_message_off)
        self.msgfont = QtGui.QFont(self.t_['onscreen_ff'],
                                   pointSize=24)
        self.set_bg(0.5, 0.5, 0.5, redraw=False)
        self.set_fg(1.0, 1.0, 1.0, redraw=False)

        # cursors
        self.cursor = {}

        # For optomized redrawing
        self._defer_task = QtCore.QTimer()
        self._defer_task.setSingleShot(True)
        self._defer_task.timeout.connect(self.delayed_redraw)


    def get_widget(self):
        return self.imgwin

    def _render_offscreen(self, drawable, data, dst_x, dst_y,
                          width, height):
        # NOTE [A]
        daht, dawd, depth = data.shape
        self.logger.debug("data shape is %dx%dx%d" % (dawd, daht, depth))

        # Get qimage for copying pixel data
        qimage = self._get_qimage(data)

        painter = QtGui.QPainter(drawable)
        painter.setWorldMatrixEnabled(True)

        # fill pixmap with background color
        imgwin_wd, imgwin_ht = self.get_window_size()
        bgclr = self._get_color(*self.get_bg())
        painter.fillRect(QtCore.QRect(0, 0, imgwin_wd, imgwin_ht),
                         bgclr)

        # draw image data from buffer to offscreen pixmap
        painter.drawImage(QtCore.QRect(dst_x, dst_y, width, height),
                          qimage,
                          QtCore.QRect(0, 0, width, height))

        # Draw a cross in the center of the window in debug mode
        if self.t_['show_pan_position']:
            clr = QtGui.QColor()
            clr.setRgbF(1.0, 0.0, 0.0)
            painter.setPen(clr)
            ctr_x, ctr_y = self.get_center()
            painter.drawLine(ctr_x - 10, ctr_y, ctr_x + 10, ctr_y)
            painter.drawLine(ctr_x, ctr_y - 10, ctr_x, ctr_y + 10)
        
        # render self.message
        if self.message:
            self.draw_message(painter, imgwin_wd, imgwin_ht,
                              self.message)

    def draw_message(self, painter, width, height, message):
        painter.setPen(self.img_fg)
        painter.setBrush(self.img_fg)
        painter.setFont(self.msgfont)
        rect = painter.boundingRect(0, 0, 1000, 1000, 0, message)
        x1, y1, x2, y2 = rect.getCoords()
        wd = x2 - x1
        ht = y2 - y1
        y = ((height // 3) * 2) - (ht // 2)
        x = (width // 2) - (wd // 2)
        painter.drawText(x, y, message)
        

    def render_image(self, rgbobj, dst_x, dst_y):
        """Render the image represented by (rgbobj) at dst_x, dst_y
        in the pixel space.
        """
        self.logger.debug("redraw pixmap=%s" % (self.pixmap))
        if self.pixmap == None:
            return
        self.logger.debug("drawing to pixmap")

        # Prepare array for rendering
        arr = rgbobj.get_array(self._rgb_order)
        (height, width) = arr.shape[:2]

        return self._render_offscreen(self.pixmap, arr, dst_x, dst_y,
                                      width, height)

    def configure(self, width, height):
        self.logger.debug("window size reconfigured to %dx%d" % (
            width, height))
        if hasattr(self, 'scene'):
            self.scene.setSceneRect(0, 0, width, height)
        # If we need to build a new pixmap do it here.  We allocate one
        # twice as big as necessary to prevent having to reinstantiate it
        # all the time.  On Qt this causes unpleasant flashing in the display.
        if (self.pixmap == None) or (self.pixmap.width() < width) or \
           (self.pixmap.height() < height):
            pixmap = QtGui.QPixmap(width*2, height*2)
            #pixmap.fill(QColor("black"))
            self.pixmap = pixmap
            self.imgwin.set_pixmap(pixmap)
        self.set_window_size(width, height, redraw=True)
        
    def get_rgb_image_as_buffer(self, output=None, format='png',
                                quality=90):
        ibuf = output
        if ibuf == None:
            ibuf = StringIO.StringIO()
        imgwin_wd, imgwin_ht = self.get_window_size()
        qpix = self.pixmap.copy(0, 0,
                                imgwin_wd, imgwin_ht)
        qbuf = QtCore.QBuffer()
        qbuf.open(QtCore.QIODevice.ReadWrite)
        qpix.save(qbuf, format=format, quality=quality)
        ibuf.write(bytes(qbuf.data()))
        qbuf.close()
        return ibuf
    
    def get_rgb_image_as_bytes(self, format='png', quality=90):
        ibuf = self.get_rgb_image_as_buffer(format=format, quality=quality)
        return bytes(ibuf.getvalue())
        
    def get_rgb_image_as_widget(self, output=None, format='png',
                                quality=90):
        imgwin_wd, imgwin_ht = self.get_window_size()
        qpix = self.pixmap.copy(0, 0,
                                imgwin_wd, imgwin_ht)
        return qpix.toImage()
    
    def save_rgb_image_as_file(self, filepath, format='png', quality=90):
        qimg = self.get_rgb_image_as_widget()
        res = qimg.save(filepath, format=format, quality=quality)
    
    def get_image_as_widget(self):
        """Used for generating thumbnails.  Does not include overlaid
        graphics.
        """
        rgbobj = self.get_rgb_object(whence=0)
        arr = rgbobj.get_array(self._rgb_order)
        image = self._get_qimage(arr)
        return image

    def save_image_as_file(self, filepath, format='png', quality=90):
        """Used for generating thumbnails.  Does not include overlaid
        graphics.
        """
        qimg = self.get_image_as_widget()
        res = qimg.save(filepath, format=format, quality=quality)
    
    def reschedule_redraw(self, time_sec):
        try:
            self._defer_task.stop()
        except:
            pass

        time_ms = int(time_sec * 1000)
        self._defer_task.start(time_ms)

    def update_image(self):
        if (not self.pixmap) or (not self.imgwin):
            return
            
        self.logger.debug("updating window from pixmap")
        if hasattr(self, 'scene'):
            imgwin_wd, imgwin_ht = self.get_window_size()
            self.scene.invalidate(0, 0, imgwin_wd, imgwin_ht,
                                  QtGui.QGraphicsScene.BackgroundLayer)
        else:
            self.imgwin.update()
            #self.imgwin.show()

    def set_cursor(self, cursor):
        if self.imgwin:
            self.imgwin.setCursor(cursor)
        
    def define_cursor(self, ctype, cursor):
        self.cursor[ctype] = cursor
        
    def get_cursor(self, ctype):
        return self.cursor[ctype]
        
    def get_rgb_order(self):
        return self._rgb_order
        
    def switch_cursor(self, ctype):
        self.set_cursor(self.cursor[ctype])
        
    # def _get_qimage(self, rgb):
    #     h, w, channels = rgb.shape

    #     # Qt expects 32bit BGRA data for color images:
    #     bgra = numpy.empty((h, w, 4), numpy.uint8, 'C')
    #     bgra[...,0] = rgb[...,2]
    #     bgra[...,1] = rgb[...,1]
    #     bgra[...,2] = rgb[...,0]
    #     if channels == 3:
    #             bgra[...,3].fill(255)
    #             fmt = QtGui.QImage.Format_RGB32
    #     else:
    #             bgra[...,3] = rgb[...,3]
    #             fmt = QtGui.QImage.Format_ARGB32

    #     result = QtGui.QImage(bgra.data, w, h, fmt)
    #     # Need to hang on to a reference to the array
    #     result.ndarray = bgra
    #     return result

    def _get_qimage(self, bgra):
        h, w, channels = bgra.shape

        fmt = QtGui.QImage.Format_ARGB32
        result = QtGui.QImage(bgra.data, w, h, fmt)
        # Need to hang on to a reference to the array
        result.ndarray = bgra
        return result

    def _get_color(self, r, g, b):
        n = 255.0
        clr = QtGui.QColor(int(r*n), int(g*n), int(b*n))
        return clr
        
    def set_fg(self, r, g, b, redraw=True):
        self.img_fg = self._get_color(r, g, b)
        if redraw:
            self.redraw(whence=3)
        
    def onscreen_message(self, text, delay=None, redraw=True):
        try:
            self.msgtimer.stop()
        except:
            pass
        self.message = text
        if redraw:
            self.redraw(whence=3)
        if delay:
            ms = int(delay * 1000.0)
            self.msgtimer.start(ms)

    def onscreen_message_off(self, redraw=True):
        return self.onscreen_message(None, redraw=redraw)
    
    def show_pan_mark(self, tf, redraw=True):
        self.t_.set(show_pan_position=tf)
        if redraw:
            self.redraw(whence=3)
        

class RenderMixin(object):

    def showEvent(self, event):
        self.fitsimage.map_event(self, event)
            
    def focusInEvent(self, event):
        self.fitsimage.focus_event(self, event, True)
            
    def focusOutEvent(self, event):
        self.fitsimage.focus_event(self, event, False)
            
    def enterEvent(self, event):
        self.fitsimage.enter_notify_event(self, event)
    
    def leaveEvent(self, event):
        self.fitsimage.leave_notify_event(self, event)
    
    def keyPressEvent(self, event):
        self.fitsimage.key_press_event(self, event)
        
    def keyReleaseEvent(self, event):
        self.fitsimage.key_release_event(self, event)
        
    def mousePressEvent(self, event):
        self.fitsimage.button_press_event(self, event)

    def mouseReleaseEvent(self, event):
        self.fitsimage.button_release_event(self, event)

    def mouseMoveEvent(self, event):
        self.fitsimage.motion_notify_event(self, event)

    def wheelEvent(self, event):
        self.fitsimage.scroll_event(self, event)

    def event(self, event):
        # This method is a hack necessary to support trackpad gestures
        # on Qt4 because it does not support specific method overrides.
        # Instead we have to override the generic event handler, look
        # explicitly for gesture events.
        if event.type() == QtCore.QEvent.Gesture:
            return self.fitsimage.gesture_event(self, event)
        return super(RenderMixin, self).event(event)

    def dragEnterEvent(self, event):
#         if event.mimeData().hasFormat('text/plain'):
#             event.accept()
#         else:
#             event.ignore()
        event.accept()

    def dragMoveEvent(self, event):
#         if event.mimeData().hasFormat('text/plain'):
#             event.accept()
#         else:
#             event.ignore()
        event.accept()

    def dropEvent(self, event):
        self.fitsimage.drop_event(self, event)

    
class RenderWidgetZoom(RenderMixin, RenderWidget):
    pass

class RenderGraphicsViewZoom(RenderMixin, RenderGraphicsView):
    pass

class ImageViewEvent(ImageViewQt):

    def __init__(self, logger=None, rgbmap=None, settings=None, render=None):
        ImageViewQt.__init__(self, logger=logger, rgbmap=rgbmap,
                             settings=settings, render=render)

        # replace the widget our parent provided
        if self.wtype == 'scene':
            imgwin = RenderGraphicsViewZoom()
            imgwin.setScene(self.scene)
        else:
            imgwin = RenderWidgetZoom()
            
        imgwin.fitsimage = self
        self.imgwin = imgwin
        imgwin.setFocusPolicy(QtCore.Qt.FocusPolicy(
                              QtCore.Qt.TabFocus |
                              QtCore.Qt.ClickFocus |
                              QtCore.Qt.StrongFocus |
                              QtCore.Qt.WheelFocus))
        imgwin.setMouseTracking(True)
        imgwin.setAcceptDrops(True)
        # enable gesture handling
        imgwin.grabGesture(QtCore.Qt.PanGesture)
        imgwin.grabGesture(QtCore.Qt.PinchGesture)
        imgwin.grabGesture(QtCore.Qt.SwipeGesture)
        # imgwin.grabGesture(QtCore.Qt.TapGesture)
        # imgwin.grabGesture(QtCore.Qt.TapAndHoldGesture)
        
        # last known window mouse position
        self.last_win_x = 0
        self.last_win_y = 0
        # last known data mouse position
        self.last_data_x = 0
        self.last_data_y = 0
        # Does widget accept focus when mouse enters window
        self.follow_focus = True

        # Define cursors
        for curname, filename in (('pan', 'openHandCursor.png'),
                               ('pick', 'thinCrossCursor.png')):
            path = os.path.join(icon_dir, filename)
            cur = make_cursor(path, 8, 8)
            self.define_cursor(curname, cur)

        # @$%&^(_)*&^ qt!!
        self._keytbl = {
            '`': 'backquote',
            '"': 'doublequote',
            "'": 'singlequote',
            '\\': 'backslash',
            ' ': 'space',
            }
        self._fnkeycodes = [QtCore.Qt.Key_F1, QtCore.Qt.Key_F2,
                            QtCore.Qt.Key_F3, QtCore.Qt.Key_F4,
                            QtCore.Qt.Key_F5, QtCore.Qt.Key_F6,
                            QtCore.Qt.Key_F7, QtCore.Qt.Key_F8,
                            QtCore.Qt.Key_F9, QtCore.Qt.Key_F10,
                            QtCore.Qt.Key_F11, QtCore.Qt.Key_F12,
                            ]

        for name in ('motion', 'button-press', 'button-release',
                     'key-press', 'key-release', 'drag-drop', 
                     'scroll', 'map', 'focus', 'enter', 'leave',
                     'pinch', 'pan', 'swipe', 'tap'):
            self.enable_callback(name)

    def transkey(self, keycode, keyname):
        self.logger.debug("keycode=%d keyname='%s'" % (
            keycode, keyname))
        if keycode in [QtCore.Qt.Key_Control]:
            return 'control_l'
        if keycode in [QtCore.Qt.Key_Shift]:
            return 'shift_l'
        if keycode in [QtCore.Qt.Key_Alt]:
            return 'alt_l'
        # if keycode in [QtCore.Qt.Key_Super_L]:
        #     return 'super_l'
        # if keycode in [QtCore.Qt.Key_Super_R]:
        #     return 'super_r'
        if keycode in [QtCore.Qt.Key_Escape]:
            return 'escape'
        # Control key on Mac keyboards and "Windows" key under Linux
        if keycode in [16777250]:
            return 'meta_right'
        if keycode in self._fnkeycodes:
            index = self._fnkeycodes.index(keycode)
            return 'f%d' % (index+1)

        try:
            return self._keytbl[keyname.lower()]

        except KeyError:
            return keyname
        
    def get_keyTable(self):
        return self._keytbl
    
    def set_followfocus(self, tf):
        self.followfocus = tf
        
    def map_event(self, widget, event):
        rect = widget.geometry()
        x1, y1, x2, y2 = rect.getCoords()
        width = x2 - x1
        height = y2 - y1
       
        self.configure(width, height)
        return self.make_callback('map')
            
    def focus_event(self, widget, event, hasFocus):
        return self.make_callback('focus', hasFocus)
            
    def enter_notify_event(self, widget, event):
        if self.follow_focus:
            widget.setFocus()
        return self.make_callback('enter')
    
    def leave_notify_event(self, widget, event):
        self.logger.debug("leaving widget...")
        return self.make_callback('leave')
    
    def key_press_event(self, widget, event):
        keyname = event.key()
        keyname2 = "%s" % (event.text())
        keyname = self.transkey(keyname, keyname2)
        self.logger.debug("key press event, key=%s" % (keyname))
        return self.make_callback('key-press', keyname)

    def key_release_event(self, widget, event):
        keyname = event.key()
        keyname2 = "%s" % (event.text())
        keyname = self.transkey(keyname, keyname2)
        self.logger.debug("key release event, key=%s" % (keyname))
        return self.make_callback('key-release', keyname)

    def button_press_event(self, widget, event):
        buttons = event.buttons()
        x, y = event.x(), event.y()

        button = 0
        if buttons & QtCore.Qt.LeftButton:
            button |= 0x1
        if buttons & QtCore.Qt.MidButton:
            button |= 0x2
        if buttons & QtCore.Qt.RightButton:
            button |= 0x4
        self.logger.debug("button down event at %dx%d, button=%x" % (x, y, button))
                
        data_x, data_y = self.get_data_xy(x, y)
        return self.make_callback('button-press', button, data_x, data_y)

    def button_release_event(self, widget, event):
        # note: for mouseRelease this needs to be button(), not buttons()!
        buttons = event.button()
        x, y = event.x(), event.y()
        
        button = 0
        if buttons & QtCore.Qt.LeftButton:
            button |= 0x1
        if buttons & QtCore.Qt.MidButton:
            button |= 0x2
        if buttons & QtCore.Qt.RightButton:
            button |= 0x4
            
        data_x, data_y = self.get_data_xy(x, y)
        return self.make_callback('button-release', button, data_x, data_y)

    def get_last_win_xy(self):
        return (self.last_win_x, self.last_win_y)

    def get_last_data_xy(self):
        return (self.last_data_x, self.last_data_y)

    def motion_notify_event(self, widget, event):
        buttons = event.buttons()
        x, y = event.x(), event.y()
        self.last_win_x, self.last_win_y = x, y
        
        button = 0
        if buttons & QtCore.Qt.LeftButton:
            button |= 0x1
        if buttons & QtCore.Qt.MidButton:
            button |= 0x2
        if buttons & QtCore.Qt.RightButton:
            button |= 0x4

        data_x, data_y = self.get_data_xy(x, y)
        self.last_data_x, self.last_data_y = data_x, data_y

        return self.make_callback('motion', button, data_x, data_y)

    def scroll_event(self, widget, event):
        delta = event.delta()
        direction = None
        if delta > 0:
            direction = 'up'
        elif delta < 0:
            direction = 'down'
        self.logger.debug("scroll delta=%f direction=%s" % (
            delta, direction))

        return self.make_callback('scroll', direction)

    def gesture_event(self, widget, event):
        gesture = event.gestures()[0]
        state = gesture.state()
        if state == QtCore.Qt.GestureStarted:
            gstate = 'start'
        elif state == QtCore.Qt.GestureUpdated:
            gstate = 'move'
        elif state == QtCore.Qt.GestureFinished:
            gstate = 'end'
        elif state == QtCore.Qt.GestureCancelled:
            gstate = 'end'

        # dispatch on gesture type
        gtype = event.gesture(QtCore.Qt.SwipeGesture)
        if gtype:
            self.gs_swiping(event, gesture, gstate)
            return True
        gtype = event.gesture(QtCore.Qt.PanGesture)
        if gtype:
            self.gs_panning(event, gesture, gstate)
            return True
        gtype = event.gesture(QtCore.Qt.PinchGesture)
        if gtype:
            self.gs_pinching(event, gesture, gstate)
            return True
        # gtype = event.gesture(QtCore.Qt.TapGesture)
        # if gtype:
        #     self.gs_tapping(event, gesture, gstate)
        #     return True
        # gtype = event.gesture(QtCore.Qt.TapAndHoldGesture)
        # if gtype:
        #     self.gs_taphold(event, gesture, gstate)
        #     return True
        return True

    def gs_swiping(self, event, gesture, gstate):
        #print "SWIPING"
        if gstate == 'end':
            _hd = gesture.horizontalDirection()
            hdir = None
            if _hd == QtGui.QSwipeGesture.Left:
                hdir = 'left'
            elif _hd == QtGui.QSwipeGesture.Right:
                hdir = 'right'

            _vd = gesture.verticalDirection()
            vdir = None
            if _vd == QtGui.QSwipeGesture.Up:
                vdir = 'up'
            elif _vd == QtGui.QSwipeGesture.Down:
                vdir = 'down'

            self.logger.debug("swipe gesture hdir=%s vdir=%s" % (
                hdir, vdir))

            return self.make_callback('swipe', gstate, hdir, vdir)

    def gs_pinching(self, event, gesture, gstate):
        #print "PINCHING"
        rot = gesture.rotationAngle()
        scale = gesture.scaleFactor()
        self.logger.debug("pinch gesture rot=%f scale=%f state=%s" % (
            rot, scale, gstate))

        return self.make_callback('pinch', gstate, rot, scale)

    def gs_panning(self, event, gesture, gstate):
        #print "PANNING"
        # x, y = event.x(), event.y()
        # self.last_win_x, self.last_win_y = x, y

        # data_x, data_y = self.get_data_xy(x, y)
        # self.last_data_x, self.last_data_y = data_x, data_y

        d = gesture.delta()
        dx, dy = d.x(), d.y()
        self.logger.debug("pan gesture dx=%f dy=%f state=%s" % (
            dx, dy, gstate))

        return self.make_callback('pan', gstate, dx, dy)

    def gs_tapping(self, event, gesture, gstate):
        #print "TAPPING", gstate
        pass

    def gs_taphold(self, event, gesture, gstate):
        #print "TAP/HOLD", gstate
        pass

    def drop_event(self, widget, event):
        dropdata = event.mimeData()
        formats = map(str, list(dropdata.formats()))
        self.logger.debug("available formats of dropped data are %s" % (
            formats))
        if dropdata.hasUrls():
            urls = list(dropdata.urls())
            paths = [ str(url.toString()) for url in urls ]
            event.acceptProposedAction()
            self.logger.debug("dropped filename(s): %s" % (str(paths)))
            self.make_callback('drag-drop', paths)
        

class ImageViewZoom(Mixins.UIMixin, ImageViewEvent):

    # class variables for binding map and bindings can be set
    bindmapClass = Bindings.BindingMapper
    bindingsClass = Bindings.ImageViewBindings

    @classmethod
    def set_bindingsClass(cls, klass):
        cls.bindingsClass = klass
        
    @classmethod
    def set_bindmapClass(cls, klass):
        cls.bindmapClass = klass
        
    def __init__(self, logger=None, settings=None, rgbmap=None,
                 render='widget',
                 bindmap=None, bindings=None):
        ImageViewEvent.__init__(self, logger=logger, settings=settings,
                                rgbmap=rgbmap, render=render)
        Mixins.UIMixin.__init__(self)

        if bindmap == None:
            bindmap = ImageViewZoom.bindmapClass(self.logger)
        self.bindmap = bindmap
        bindmap.register_for_events(self)

        if bindings == None:
            bindings = ImageViewZoom.bindingsClass(self.logger)
        self.set_bindings(bindings)

    def get_bindmap(self):
        return self.bindmap
    
    def get_bindings(self):
        return self.bindings
    
    def set_bindings(self, bindings):
        self.bindings = bindings
        bindings.set_bindings(self)

        
def make_cursor(iconpath, x, y):
    image = QtGui.QImage()
    image.load(iconpath)
    pm = QtGui.QPixmap(image)
    return QtGui.QCursor(pm, x, y)


#END
