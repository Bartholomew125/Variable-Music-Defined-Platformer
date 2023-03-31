# importing all them goodies
import pygame as pg
from random import random, randint
import random as rand
import spotipy
from math import sqrt, degrees, atan, sin, cos, radians, tan
from spotipy.oauth2 import SpotifyOAuth
from colorsys import hsv_to_rgb as HTR
import threading
import time

# setup
w = 600
h = 600

pg.font.init()
pg.display.set_caption("Variable Music Defined Platformer")
icon_images = []
for i in range(11):
    icon_images.append(pg.image.load(f"icon\cubedesign-{i+1}.png"))
    
screen = pg.display.set_mode((w,h))
clock = pg.time.Clock()


# SPOTIFY SETUP
scope = "user-read-currently-playing"
client_id = '5b68ffcb63924892995c6b9b02ead2e0'
client_secret = 'e6bc5bd16c4741d38f4609d0e1c57440'
redirect_uri = 'http://localhost:8888/callback'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))


# music setup
bpm = 1
bps = 1
tick = 165


# size setup
character_size = w/50
character_speed = 2
box_size = 100
box_speed = bps


# __VARIABLES__
k_left = False
k_right = False
k_up = False
k_r = False
lose = False
songFound = False
running = True
spawn = False
is_playing = False
game_start = False

white = (255, 255, 255)
red = (255, 0, 0)
ticks = 200
oldHeight = h/1.5
maxDistance = h/5/2
maxMovementSpeed = 1
old_track = 0
current_track = 0
jump_speed = 10
g = 0

# __CLASSES__
# Character class
class Character:
    def __init__(self, pos, dim, color):
        self.pos = pos
        self.dim = dim
        self.color = color
        self.x = pos[0]
        self.y = pos[1]
        self.rect = pg.Rect(self.pos, self.dim)
        self.vec = (0, 0)
    
    def jump(self):
        self.vec = self.vec[0], self.vec[1]-jump_speed

    def update(self):
        self.pos = addVector(self.pos, self.vec)
        self.vec = self.vec[0], self.vec[1]-g
        self.rect = pg.Rect(self.pos, self.dim)

    def draw(self):
        pg.draw.rect(screen, self.color, self.rect)


# Box Class
class Box:
    def __init__(self, pos, dim, color, speed):
        self.pos = pos
        self.dim = dim
        self.color = color
        self.speed = speed
        self.x = pos[0]
        self.y = pos[1]
        self.rect = pg.Rect(self.pos, self.dim)
        self.vec = [0, 0]
    
    def update(self):
       self.pos = self.x, self.y
       self.pos = addVector(self.pos, self.vec)
       self.vec = self.vec[0]-self.speed, self.vec[1]
       self.rect = pg.Rect(self.pos, self.dim)

    def draw(self):
        pg.draw.rect(screen, self.color, self.rect)
        

# Background Class
class Background:
    def __init__(self):
        self.pos = (0, 0)
        self.speed = (0, 0)
        self.color = (0, 0, 0)
        self.texture_seed = 0
        self.points = []
        self.layers = []

    def update(self):
        pass
    
    def new(self, energy, key, valence, speed):
        self.speed = speed
        self.energy = energy
        self.valence = valence
        self.key = key
        self.color = HTR(1/(key+2), 1, 255)
        self.points = []
        self.layers = []

        # generate points and add to layer
        rand.seed(self.energy+self.valence+self.key)
        self.points.append((0, 0))
        for i in range(0, int(self.energy*30), 1):
            point = (w/int(self.energy*30) * i, randint(0, int(h/5*valence)))
            self.points.append(point)
        point = (w, self.points[1])
        self.points.append((w, 0))

        self.layers.append(self.points)
    
    def draw(self):
        for layer in self.layers:
            pg.draw.polygon(screen, self.color, layer)
        

# Button Class
class Button:
    def __init__(self, pos, dim, color, text):
        self.pos = (pos[0]-dim[0]/2, pos[1]-dim[1]/2)
        self.centerPos = pos
        self.originalDimensions = dim
        self.dimensions = dim
        self.originalColor = color
        self.color = color
        self.rect = pg.Rect(self.pos, self.dimensions)
        self.selected = False
        self.buttonText = text

    def updateFont(self):
        self.font = pg.font.Font("freesansbold.ttf", int(self.dimensions[1]/3))
        self.fontDimensions = self.font.size(self.buttonText)
        self.text = self.font.render(self.buttonText, True, red)
        self.textPos = (self.pos[0]+(self.dimensions[0]-self.fontDimensions[0])/2, 
                        self.pos[1]+(self.dimensions[1]-self.fontDimensions[1])/2)

    def update(self):
        if self.selected:
            self.color = self.originalColor
            self.dimensions = (self.originalDimensions[0]*1.1, self.originalDimensions[1]*1.1)
            self.pos = (self.centerPos[0]-self.dimensions[0]/2, self.centerPos[1]-self.dimensions[1]/2)
            self.rect = pg.Rect(self.pos, self.dimensions)
            self.updateFont()
        else:
            self.color = (155, 155, 155)
            self.dimensions = self.originalDimensions
            self.pos = (self.centerPos[0]-self.dimensions[0]/2, self.centerPos[1]-self.dimensions[1]/2)
            self.rect = pg.Rect(self.pos, self.dimensions)
            self.updateFont()

    def draw(self):
        pg.draw.rect(screen, self.color, self.rect, width=0, border_radius=int(self.dimensions[1]/2))
        screen.blit(self.text, self.textPos)


# Mouse Class
class Mouse:
    def __init__(self):
        self.pos = (0, 0)
        self.l_click = False
        self.r_click = False
    
    def update(self):
        self.pos = pg.mouse.get_pos()
        

# __FUNCTIONS__
# Rectangle with Rectangle collision function
def rectRectCollide(object1, object2):
   return True if object1.rect.colliderect(object2.rect) else False


# Position with Rectangle collision function
def posRectCollide(pos, rect):
    return True if rect.collidepoint(pos) else False


# Vector Addition
def addVector(v1, v2):
   return v1[0]+v2[0], v1[1]+v2[1]


# Search for song and song values
def searchSong():
    global key
    global energy
    global valence
    global track_name
    global bpm
    global songFound
    global running
    global is_playing
    global current_track

    while running:
        # Get information about the track you are currently playing
        current_track = sp.current_user_playing_track()
       

        # Check if there is a track currently playing
        if current_track is not None and current_track.get('item') is not None:
            track_uri = current_track['item']['uri']
            features = sp.audio_features(tracks=[track_uri])
            track_name = current_track['item']['name']
            bpm = features[0]["tempo"]
            energy = features[0]["energy"]
            is_playing = current_track["is_playing"]
            key = features[0]["key"]
            valence = features[0]["valence"]
            
            #print(track_name, bpm)
            songFound = True
        else:
            #print("searching")
            songFound = False
            #print(songFound) 


# start thread
thread = threading.Thread(target=searchSong)
thread.start()


#before loop setup
boxes = []
Bateman = Character((w/2, h/3), (character_size, character_size), white)
energy, key, valence = 1, 0.3, 0.43
BG = Background()
mouse = Mouse()


# Setup buttons for menu
buttons = []
buttons.append(Button((w/2, h/4), (w/2, h/4), white, "Start Game"))
buttons.append(Button((w/2, h/4*3), (w/2, h/4), white, "Quit"))


# Stagger time for Thread to catch up (Please optimize)
time.sleep(0.4)


# THE LOOP
while running:
    #print(bpm)
    for event in pg.event.get():

        if event.type == pg.QUIT:
            running = False

        # check for keystrokes
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
            if event.key == pg.K_UP:
                k_up = True
            if event.key == pg.K_LEFT:
                k_left = True
            if event.key == pg.K_RIGHT:
                k_right = True
            if event.key == pg.K_r:
                k_r = True

        if event.type == pg.KEYUP:
            if event.key == pg.K_UP:
                k_up  = False
            if event.key == pg.K_LEFT:
                k_left = False
            if event.key == pg.K_RIGHT:
                k_right = False
            if event.key == pg.K_r:
                k_r = False
        
        # check for mouse clicks
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse.l_click = True
            if event.button == 3:
                mouse.r_click = True
        
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                mouse.l_click = False
            if event.button == 3:
                mouse.r_click = False

    # reset screen
    screen.fill((0, 0, 0))
    
    # menu
    if not game_start:
        for button in buttons:
            if posRectCollide(mouse.pos, button.rect):
                button.selected = True
                if mouse.l_click:
                    if button.buttonText == "Start Game":
                        game_start = True
                    elif button.buttonText == "Quit":
                        running = False
            else:
                button.selected = False
        
        mouse.update()
        for button in buttons:
            button.update()
            button.draw()
    
    # game start
    elif game_start:

        # update music variables
        print("outside", bpm, g)
        bps = bpm/60
        box_speed = bps

        v0 = sqrt((jump_speed)**2+(bps)**2)
        #print(v0)
        angle = atan(jump_speed/bps)
        #print(angle)
        v0x = cos(angle)*v0
        v0y = sin(angle)*v0
        x = (tick-box_size)
        y = maxDistance

        #g = (2*v0x**2 * maxDistance - 2*v0y*(tick-box_size)) / (tick - box_size)**2
        g = -(2 * v0**2 * cos(angle)**2 * (x * tan(angle) - y))/x**2

        # check for track change
        if type(current_track) != type(0) and current_track is not None and current_track["item"] is not None:
            if old_track != current_track['item']['uri']:
                old_track = current_track['item']['uri']
                BG.new(energy, key, valence, (bps/2, 0))
                print("NEW TRACK!")
                print(track_name)
                Bateman.pos = (w/2, h/3)
                Bateman.vec = (0, 0)
                spawn = False
                print("inside", bpm, g)
                
                #print(track_name, jump_speed, maxDistance, bps, bpm, tick, box_size, g)

        # check if a song is found, and it is playing
        if songFound and is_playing:

            # reset
            if k_r:
                lose = False
                Bateman.pos = (w/2, h/3)
                Bateman.vec = (0, 0)
                spawn = False
                Bateman.update()

            # while you dont suck
            if not lose:

                # collision check
                for box in boxes:
                    if rectRectCollide(Bateman, box):
                        
                        # top collision
                        if box.pos[1]-Bateman.dim[1] < Bateman.pos[1] < box.pos[1]+Bateman.dim[1]:
                            Bateman.pos = Bateman.pos[0], box.pos[1]-Bateman.dim[1]
                            Bateman.vec = (0, 0)
                            if k_up:
                                k_up = False
                                Bateman.jump()
                            
                        # side collision
                        else:
                            Bateman.vec = (-box.speed, Bateman.vec[1])

                # check if bateman has fallen
                if Bateman.pos[1] > h or Bateman.pos[0] < 0:
                    lose = True
            
                # Out Of Bounds box removal
                for box in boxes:
                    if box.x+box.dim[0] <= 0:
                        boxes.remove(box)
                
                # update old box height
                if len(boxes) > 0:
                    oldHeight = boxes[-1].y

                # summon boxes
                if ticks >= tick/bps:
                    ticks = 0
                    offset = maxDistance*2 * (random()-0.5)
                    newHeight = oldHeight + offset
                    if newHeight > h:
                        newHeight = h-10
                    if newHeight < h/2:
                        newHeight = h/2
                    boxcol = HTR(energy, 1, 255)
                    c_or_n = randint(0,1)
                    if c_or_n == 1:
                        boxes.append(Box((w, newHeight), (box_size, box_size/2), boxcol, box_speed))
                    else:
                        boxes.append(Box((w, newHeight), (box_size, h), boxcol, box_speed))
            
            # damn bro, you suck
            elif lose:
                font = pg.font.SysFont('comicsansms', 50)
                screen.blit(font.render("U DED", True, (255, 255, 255)), (w/3, h/3))

            # UPDATE
            for box in boxes:
                box.update()
            if spawn == True or k_up:
                spawn = True
                Bateman.update()
            for p in BG.points:
                p = (p[0]-1, p[1])
            BG.update()
            clock.tick(tick)
            ticks += 1
            
        # if nothing is playing
        elif not is_playing:
            Bateman.pos = (w/2, h/3)
            # pause bars
            pg.draw.rect(screen, white, pg.Rect(w/9*3, h/4, w/9, h/4*2))
            pg.draw.rect(screen, white, pg.Rect(w/9*5, h/4, w/9, h/4*2))
        
        # DRAW SHIT
        BG.draw()
        Bateman.draw()
        for box in boxes:
            box.draw()
        if ticks %10 == 0:
            pg.display.set_icon(icon_images[ticks%11])

    pg.display.flip()

pg.display.quit()
pg.quit()
