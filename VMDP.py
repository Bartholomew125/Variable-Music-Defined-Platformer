# importing all them goodies
import pygame as pg
from random import random, randint
import random as rand
import spotipy
from math import sqrt
from spotipy.oauth2 import SpotifyOAuth
from colorsys import hsv_to_rgb as HTR
import threading
import time

# setup
w = 600
h = 600

screen = pg.display.set_mode((w,h))
clock = pg.time.Clock()

pg.font.init()


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
box_size = w/6
box_speed = bps


# variables
white = (255, 255, 255)
red = (255, 0, 0)
ticks = 200
oldHeight = h/1.5
maxDistance = h/5/2
maxMovementSpeed = 1
k_left = False
k_right = False
k_up = False
lose = False
songFound = False
running = True
spawn = False
is_playing = False
old_track = 0
current_track = 0
jump_speed = 4
g = 0

# classes here
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
        

class Background:
    def __init__(self):
        self.pos = (0, 0)
        self.speed = (0, 0)
        self.color = (0, 0, 0)
        self.texture_seed = 0
        self.points = []

    def update(self):
        pass
    
    def new(self, energy, key, valence, speed):
        self.speed = speed
        self.energy = energy
        self.valence = valence
        self.key = key
        self.color = HTR(1/(key+2), 1, 255)
        self.top = []
        self.bottom = []
        self.layers = []

        # generate points of both halves and add to layer
        rand.seed(self.energy+self.valence+self.key)
        self.top.append((0, 0))
        for i in range(0, int(self.energy*30), 1):
            point = (w/int(self.energy*30) * i, randint(0, int(h/4*valence)))
            self.top.append(point)
        point = (w, self.top[1])
        self.top.append((w, 0))

        rand.seed(self.energy-self.valence+self.key)
        self.bottom.append((0, h))
        for i in range(0, int(self.energy*30), 1):
            point = (w/int(self.energy*30) * i, h-randint(0, int(h/4*valence)))
            self.bottom.append(point)
        point = (w, self.bottom[1])
        self.bottom.append((w, h))
        layer = [self.top, self.bottom]
        self.layers.append(layer)
    
    def draw(self):
        for layer in self.layers:
            for half in layer:
                pg.draw.polygon(screen, self.color, half)
        

# functions here
def collide(object1, object2):
   return True if object1.rect.colliderect(object2.rect) else False

def addVector(v1, v2):
   return v1[0]+v2[0], v1[1]+v2[1]

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

time.sleep(0.3)
# THE LOOP
while running:
    #print(bpm)
    for event in pg.event.get():

        if event.type == pg.QUIT:
            running = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
            if event.key == pg.K_UP:
                k_up = True
            if event.key == pg.K_LEFT:
                k_left = True
            if event.key == pg.K_RIGHT:
                k_right = True

        if event.type == pg.KEYUP:
            if event.key == pg.K_UP:
                k_up  = False
            if event.key == pg.K_LEFT:
                k_left = False
            if event.key == pg.K_RIGHT:
                k_right = False

    # update music variables
    bps = bpm/60
    box_speed = bps


    # check for track change
    if type(current_track) != type(0) and current_track is not None and current_track["item"] is not None:
        if old_track != current_track['item']['uri']:
            old_track = current_track['item']['uri']
            BG.new(energy, key, valence, (bps/2, 0))
            print("NEW TRACK!")
            Bateman.pos = (w/2, h/3)
            Bateman.vec = (0, 0)
            spawn = False
            g = -(2*jump_speed**2 * maxDistance - 2*bps*jump_speed * (tick-box_size)) / (tick - box_size)**2
            g = g/2
            print(track_name, jump_speed, maxDistance, bps, bpm, tick, box_size, g)

        
    # check if a song is found, and it is playing
    if songFound and is_playing:
        screen.fill((0, 0, 0))

        # while you dont suck
        if not lose:

            # collision check
            for box in boxes:
                if collide(Bateman, box):
                    
                    # top collision
                    if box.pos[1]-Bateman.dim[1] < Bateman.pos[1] < box.pos[1]:
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
        else:
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
        

        # DRAW SHIT
        BG.draw()
        Bateman.draw()
        for box in boxes:
            box.draw()
    
    # if nothing is playing
    elif not is_playing:
        Bateman.pos = (w/2, h/3)


    pg.display.flip()


pg.display.quit()
pg.quit()
