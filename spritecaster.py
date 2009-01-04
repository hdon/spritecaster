#!/usr/bin/env python
bgcolor = 200,255,200
boxcolor = 255,255,255
wirecolor = 0,255,255

import gtk, gtk.glade as glade

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
            'on_open_command':              self.do_open,
        })

    pic = None
    def draw_area_draw(self, widget, event, data=None):
        if self.pic:
            area = event.area
            print area.x, area.y, area.width, area.height
            widget.window.draw_pixbuf(widget.window.new_gc(), self.pic,
                area.x, area.y, area.x, area.y, area.width, area.height)
            print 'draw_pixbuf() returned!'

    def main(self):
        gtk.main()

    def do_open(self, widget, *data):
        dialog = self.glade.get_widget('filechooserdialog1')
        response = dialog.run()
        dialog.hide()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.pic = gtk.gdk.pixbuf_new_from_file(filename)

    def div_tool_button(self, widget):
        if widget.get_active():
            print 'TODO assign div tool'
    def auto_tool_button(self, widget):
        if widget.get_active():
            print 'TODO assign auto tool'
    def select_tool_button(self, widget):
        if widget.get_active():
            print 'TODO assign select tool'
    def delete_event(self, widget, event, data=None):
        return False
    def destroy(self, widget, data=None):
        gtk.main_quit()

def perimeter(x1, y1, x2, y2):
    '''Generator for each x,y position in a rectangular perimeter'''
    for n in range(x1,  x2+1):  yield n,    y1
    for n in range(y1+1,y2+1):  yield x2,   n
    for n in range(1, x2-x1):   yield x2-n, y2
    for n in range(0, y2-y1):   yield x1,   y2-n

def identify_rect(image, colorkey, pos):
    '''Returns (x,y),(w,h) for a the largest rectangular perimeter
    containing at least one non-transparent pixel, but which is smaller
    than the smallest rectangular perimeter containing only transparent
    pixels, such that the pixel at position `pos` is contained in the
    first rectangle, and the first rectangle is contained in the second'''
    r = image.get_rect()
    x, y = pos
    x1, y1, x2, y2 = x, y, x+1, y+1

    if image.get_at(pos) == colorkey:
        raise IndexError("Requested empty image location")
        # XXX lol is IndexError really appropriate?

    # The search for the sprite begins...
    while True:
        # r.collidepoint filtration rejects pixels outside of the image
        for x,y in filter(r.collidepoint, perimeter(x1, y1, x2, y2)):
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

