#!/usr/bin/env python
bgcolor = 200,255,200
boxcolor = 255,255,255
wirecolor = 0,255,255

import pygame, sys, os, inspect
from pygame.locals import *

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
    pixels, such that both rectangles also contain the position `pos`'''
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
    main()
    print 'Bye'

