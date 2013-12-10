#
# ImageViewAgg.py -- classes for the display of FITS files on AGG surfaces
# 
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c)  Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.

import numpy
import StringIO

import aggdraw as agg
import AggHelp

from ginga import ImageView

from ginga.aggw.ImageViewCanvasTypesAgg import *
try:
    import PIL.Image as PILimage
    have_PIL = True
except ImportError:
    have_PIL = False
    

class ImageViewAggError(ImageView.ImageViewError):
    pass

class ImageViewAgg(ImageView.ImageViewBase):

    def __init__(self, logger=None, rgbmap=None, settings=None):
        ImageView.ImageViewBase.__init__(self, logger=logger,
                                         rgbmap=rgbmap,
                                         settings=settings)

        self.surface = None
        self.img_fg = None
        self.set_fg(1.0, 1.0, 1.0, redraw=False)
        self._rgb_order = 'RGBA'
        
        self.message = None

        # cursors
        self.cursor = {}

        self.t_.setDefaults(show_pan_position=False,
                            onscreen_ff='Sans Serif')
        
    def get_surface(self):
        return self.surface

    def render_image(self, rgbobj, dst_x, dst_y):
        """Render the image represented by (rgbobj) at dst_x, dst_y
        in the pixel space.
        """
        if self.surface == None:
            return
        canvas = self.surface
        self.logger.debug("redraw surface")

        # get window contents as a buffer and load it into the AGG surface
        rgb_buf = self.getwin_buffer(order=self._rgb_order)
        canvas.fromstring(rgb_buf)

        cr = AggHelp.AggContext(canvas)
      
        # Draw a cross in the center of the window in debug mode
        if self.t_['show_pan_position']:
            ctr_x, ctr_y = self.get_center()
            pen = cr.get_pen('red')
            canvas.line((ctr_x - 10, ctr_y, ctr_x + 10, ctr_y), pen)
            canvas.line((ctr_x, ctr_y - 10, ctr_x, ctr_y + 10), pen)
        
        # render self.message
        if self.message:
            font = cr.get_font(self.t_['onscreen_ff'], 24.0, self.img_fg)
            wd, ht = cr.text_extents(self.message, font)
            imgwin_wd, imgwin_ht = self.get_window_size()
            y = ((imgwin_ht // 3) * 2) - (ht // 2)
            x = (imgwin_wd // 2) - (wd // 2)
            canvas.text((x, y), self.message, font)

        # for debugging
        #self.save_rgb_image_as_file('/tmp/temp.png', format='png')

    def configure(self, width, height):
        # create agg surface the size of the window
        self.surface = agg.Draw("RGBA", (width, height), 'black')

        # inform the base class about the actual window size
        self.set_window_size(width, height, redraw=True)
        
    def save_rgb_image_as_buffer(self, output=None, format='png', quality=90):
        if not have_PIL:
            raise ImageViewAggError("Please install PIL to use this method")
        
        if self.surface == None:
            raise ImageViewAggError("No AGG surface defined")

        ibuf = output
        if ibuf == None:
            ibuf = StringIO.StringIO()

        # convert AGG draw surface to a numpy array
        data = numpy.fromstring(self.surface.tostring(), dtype='uint8')
        # TODO: could these have changed between the time that self.surface
        # was last updated?
        wd, ht = self.get_window_size()
        data = data.reshape((wd, ht, 4))

        # convert numpy array to PIL image for output as an image format
        img = PILimage.fromarray(data)

        img.save(ibuf, format=format, quality=quality)
        return ibuf
    
    def save_rgb_image_as_file(self, filepath, format='png', quality=90):
        if not have_PIL:
            raise ImageViewAggError("Please install PIL to use this method")
        if self.surface == None:
            raise ImageViewAggError("No AGG surface defined")

        with open(filepath, 'w') as out_f:
            self.save_rgb_image_as_buffer(output=out_f, format=format,
                                          quality=quality)
        self.logger.debug("wrote %s file '%s'" % (format, filepath))
    
    def update_image(self):
        # subclass implements this method to actually update a widget
        # from the agg surface
        self.logger.warn("Subclass should override this method")
        return False
        
    def set_cursor(self, cursor):
        # subclass implements this method to actually set a defined
        # cursor on a widget
        self.logger.warn("Subclass should override this method")
        
    def define_cursor(self, ctype, cursor):
        self.cursor[ctype] = cursor
        
    def get_cursor(self, ctype):
        return self.cursor[ctype]
        
    def switch_cursor(self, ctype):
        self.set_cursor(self.cursor[ctype])
        
    def get_rgb_order(self):
        return self._rgb_order
        
    def set_fg(self, r, g, b, redraw=True):
        self.img_fg = (r, g, b)
        if redraw:
            self.redraw(whence=3)
        
    def onscreen_message(self, text, delay=None, redraw=True):
        # subclass implements this method using a timer
        self.logger.warn("Subclass should override this method")

    def show_pan_mark(self, tf, redraw=True):
        self.t_.set(show_pan_position=tf)
        if redraw:
            self.redraw(whence=3)
        

#END
