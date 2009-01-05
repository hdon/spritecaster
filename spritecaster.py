#!/usr/bin/env python
bgcolor = 200,255,200
boxcolor = 255,255,255
wirecolor = 0,255,255

import gtk, gtk.gdk as gdk, gtk.glade as glade, gobject

def expand_rect_2to4_points(p1, p2):
    return p1, (p1[0],p2[1]), p2, (p2[0],p1[1])

def expand_rect_2to4_dimensions(p1, p2):
    return p1, p2, p2[0]-p1[0], p2[1]-p1[1]

class Application(object):
    def __init__(self):
        self.glade = glade.XML('spritecaster.glade')
        self.glade.signal_autoconnect({
            'on_window1_delete_event':      self.delete_event,
            'on_window1_destroy_event':     self.destroy,
            'on_auto_button_toggled':       self.auto_tool_button,
            'on_div_tool_button_toggled':   self.div_tool_button,
            'on_select_tool_button_toggled':self.select_tool_button,
            'on_drawingarea1_expose_event': self.draw_area_draw,
            'on_drawingarea1_button_press_event':
                                            self.draw_area_button,
            'on_open_command':              self.do_open,
        })
        self.drawing_area = self.glade.get_widget('drawingarea1')

        # Currently loaded source image (TODO more than one!!!)
        self.pic = None

        # Default tool (what the mouse is doing)
        self.tool = 'select'

        # Instantiate GTK abstractions for various collections represented
        # by GUI widgets
        self.sprites = gtk.ListStore(gobject.TYPE_STRING, gdk.Pixbuf)

        # Bind the sprite list model to the sprite list view
        self.sprites_view = self.glade.get_widget('sprite_tree_view')
        self.sprites_view.set_model(self.sprites)

        # Create a text column for the tree view. Bind its values ('text')
        # to column 0 (text = 0) in 'sprites'
        self.sprites_view.append_column(gtk.TreeViewColumn('Name',
            gtk.CellRendererText(), text = 0))

        # Create a pixbuf column
        self.sprites_view.append_column(gtk.TreeViewColumn('Preview',
            gtk.CellRendererPixbuf(), pixbuf = 1))

    def draw_area_draw(self, widget, event, *data):
        '''Redraws the contents of drawingarea1, our main work area'''
        if self.pic:
            area = event.area
            window = widget.window
            window.draw_pixbuf(window.new_gc(), self.pic,
                area.x, area.y, area.x, area.y,
                min(area.width, self.pic.get_width()),
                min(area.height, self.pic.get_height()))

    def draw_area_button(self, widget, event, *data):
        '''Mouse button handler for drawingarea1, our main work area'''
        if self.pic:
            #print self.myimage.get_at(event.x, event.y)
            try: 
                (x,y),(w,h) = identify_rect(self.myimage, (0,255,0),
                    (int(event.x), int(event.y)))
                i = self.sprites.append()
                self.sprites.set_value(i, 0, 'untitled')
                self.sprites.set_value(i, 1,
                    self.pic.subpixbuf(x, y, w-1, h-1))

                # Outline sprite
                #self.pic.draw_lines(self.pic.new_gc(),
                #    expand_rect_2to4_points(r))
                # Update drawing area
                #self.drawing_area.queue_draw_area(
                #    expand_rect_2to4_dimensions(r))
            except IndexError:
                print 'empty image region'

    def main(self):
        gtk.main()

    def do_open(self, widget, *data):
        '''Invokes the Open File dialog'''
        dialog = self.glade.get_widget('filechooserdialog1')
        response = dialog.run()
        dialog.hide()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.pic = gdk.pixbuf_new_from_file(filename)
            self.myimage = MyImage(self.pic)
            self.drawing_area.queue_draw()

    def div_tool_button(self, widget):
        if widget.get_active():
            self.tool = 'divider'
    def auto_tool_button(self, widget):
        if widget.get_active():
            self.tool = 'auto'
    def select_tool_button(self, widget):
        if widget.get_active():
            self.tool = 'select'
    def delete_event(self, widget, event, *data):
        return False
    def destroy(self, widget, *data):
        gtk.main_quit()

def perimeter(x1, y1, x2, y2):
    '''Generator for each x,y position in a rectangular perimeter'''
    for n in range(x1,  x2+1):  yield n,    y1
    for n in range(y1+1,y2+1):  yield x2,   n
    for n in range(1, x2-x1):   yield x2-n, y2
    for n in range(0, y2-y1):   yield x1,   y2-n

def in_bounds(w, h):
    def closure(pos):
        x, y = pos
        return (x>=0)and(x<w)and(y>=0)and(y<h)
    return closure

class MyImage(object):
    '''This provides a convenient abstraction for image processing so that
    in the future if I change the underlying technology, the image processing
    code doesn't need to change.'''
    # It should be noted, however, that I would still like to replace this
    # with a C-coded Python module
    def __init__(self, pixbuf):
        if not isinstance(pixbuf, gdk.Pixbuf):
            raise TypeError('constructor argument must be gdk.Pixbuf')
        self.pbuf = pixbuf
        self.pxdata = pixbuf.get_pixels()
    def get_width(self): return self.pbuf.get_width()
    def get_height(self): return self.pbuf.get_height()
    def get_at(self, pos):
        x, y = pos
        size = self.pbuf.get_bits_per_sample() / 8 * self.pbuf.get_n_channels()
        pos = int(x * size + y * self.pbuf.get_rowstride())
        return tuple(ord(c)for c in self.pxdata[pos:pos+size])

def identify_rect(image, colorkey, pos):
    '''Returns (x,y),(w,h) for a the largest rectangular perimeter
    containing at least one non-transparent pixel, but which is smaller
    than the smallest rectangular perimeter containing only transparent
    pixels, such that the pixel at position `pos` is contained in the
    first rectangle, and the first rectangle is contained in the second'''
    w = image.get_width()
    h = image.get_height()
    x, y = pos
    x1, y1, x2, y2 = x, y, x+1, y+1

    if image.get_at(pos) == colorkey:
        raise IndexError("Requested empty image location")
        # XXX lol is IndexError really appropriate?

    # The search for the sprite begins...
    while True:
        # r.collidepoint filtration rejects pixels outside of the image
        for x,y in filter(in_bounds(w, h), perimeter(x1, y1, x2, y2)):
            # check for transparent area
            color = image.get_at((x,y))
            if color != colorkey:
                if x <= x1: x1 -= 1
                elif x >= x2: x2 += 1
                if y <= y1: y1 -= 1
                elif y >= y2: y2 += 1
                break
        if color == colorkey:
            return (x1+1,y1+1),(x2-x1,y2-y1)

#def identify_blob(image, colorkey, pos):
#    r = image.get_rect()
#    x1, y1 = pos
#    x2, y2 = pos
#    x2 += 1
#    y2 += 1
#    def floodfill(x,y):
#        if floodfill(
        
def usage_exit():
    raise SystemExit("usage: %s <image>" % sys.argv[0])

def main():
    pygame.init()

    # identify filename argument
    try: filename = sys.argv[1]
    except IndexError: usage_exit()
    if not filename: usage_exit()

    # load the image and get it on-screen
    image = pygame.image.load(filename)
    rect = image.get_rect()
    pygame.display.set_mode(image.get_size())
    image = image.convert()
    colorkey = image.get_at((0,0))
    image.set_colorkey(colorkey, RLEACCEL)
    screen = pygame.display.get_surface()
    screen.fill(bgcolor)
    screen.blit(image, (0,0))

    # main event loop
    while 1:
        pygame.display.flip()
        event = pygame.event.wait()
        if event.type == QUIT: return

        # MOUSEBUTTONDOWN means search for sprite
        elif event.type == MOUSEBUTTONDOWN:
            try:
                if image.mustlock(): image.lock()
                area = identify_rect(image, colorkey, event.pos)
            except IndexError, msg:
                area = None
                print msg
            if image.get_locked(): image.unlock()
            
            # did we find a sprite!
            if area:
                screen.fill(boxcolor, area)
                pygame.draw.rect(screen, (wirecolor), area, 1)
                screen.blit(image, area, area)

if __name__ == '__main__':
    try:
        app = Application()
        app.main()
    except KeyboardInterrupt:
        print 'Bye'

