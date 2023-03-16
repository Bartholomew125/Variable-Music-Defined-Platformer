# importing all them goodies
import pygame as pg
from random import random, randint
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from colorsys import hsv_to_rgb as HTR

# setup
w = 600
h = 600

tick = 165

screen = pg.display.set_mode((w,h))
clock = pg.time.Clock()

pg.font.init()


# variables
white = (255, 255, 255)
red = (255, 0, 0)
ticks = 200
oldHeight = h/1.5
maxDistance = h/4
maxMovementSpeed = 1
g = 1/tick * 4
k_left = False
k_right = False
k_up = False
startSong = True
lose = False


# SPOTIFY SETUP

# Set up the Spotify API client
client_id = '5b68ffcb63924892995c6b9b02ead2e0'
client_secret = 'e6bc5bd16c4741d38f4609d0e1c57440'
redirect_uri = 'http://localhost:8888/callback'
scope = 'user-modify-playback-state'

# Prompt the user to authorize your app to access their Spotify account
scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

# Replace the song title and artist below with the song you want to play
song_title = "6705"
artist_name = "Kellermensch"

# Search for the song and get its URI
results = sp.search(q=f"{song_title} {artist_name}", type="track", limit=1)
if results["tracks"]["items"]:
    track_uri = results["tracks"]["items"][0]["uri"]
    track_features = sp.audio_features(tracks=[track_uri])
    print(track_features)
    if track_features:
        tempo = track_features[0]["tempo"]
        energy = track_features[0]["energy"]
        print(f"Now playing: {song_title} by {artist_name}, bpm: {tempo}")
else:
    print("Song not found")


# music setup
bpm = tempo
bps = bpm/60


# size setup
character_size = w/50
character_speed = 0.5
box_size = w/6
box_speed = bps


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
        self.vec = self.vec[0], self.vec[1]-1

    def move(self, dir):
        if dir == "left":
            self.vec = -character_speed, self.vec[1]
        elif dir == "right":
            self.vec = character_speed, self.vec[1]

    def update(self):
        self.pos = addVector(self.pos, self.vec)
        self.vec = self.vec[0], self.vec[1]+g
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
        

# functions here
def collide(object1, object2):
   return True if object1.rect.colliderect(object2.rect) else False

def addVector(v1, v2):
   return v1[0]+v2[0], v1[1]+v2[1]


#before loop setup
boxes = []
Bateman = Character((w/2, h/2), (character_size, character_size), white)


# THE LOOP
running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
            if event.key == pg.K_UP:
                k_up = True
            if event.key ==pg.K_LEFT:
                k_left = True
            if event.key == pg.K_RIGHT:
                k_right = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_UP:
                k_up  == False
            if event.key == pg.K_LEFT:
                k_left = False
            if event.key == pg.K_RIGHT:
                k_right = False

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
                
                # side collision
                else:
                    Bateman.vec = (-box.speed, Bateman.vec[1])
        

        # check if bateman has fallen
        if Bateman.pos[1] > h or Bateman.pos[0] < 0:
            lose = True
        

        # Bateman movement
        if k_up:
            k_up = False
            Bateman.jump()
        if k_left:
            Bateman.move("left")
        if k_right:
            Bateman.move("right")


        # OOB box removal
        for box in boxes:
            if box.x+box.dim[0] <= 0:
                boxes.remove(box)
        

        # update old box height
        if len(boxes) > 0:
            oldHeight = boxes[-1].y


        # summon boxes
        if ticks >= tick/bps:
            ticks = 0
            offset = maxDistance * (random()-0.5)
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
            
            if startSong:
                sp.start_playback(uris=[track_uri])
                startSong = False
    
    # damn bro, you suck
    else:
        font = pg.font.SysFont('comicsansms', 50)
        screen.blit(font.render("HA YOU SUCK", True, (255, 255, 255)), (w/3, h/3))
        

    # UPDATE
    for box in boxes:
        box.update()
    Bateman.update()
    clock.tick(tick)
    ticks += 1
    

    # DRAW SHIT
    Bateman.draw()
    for box in boxes:
        box.draw()


    pg.display.flip()

sp.pause_playback()
pg.display.quit()
pg.quit()