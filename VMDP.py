# importing all them goodies
import pygame as pg
from random import random, randint
import random as rand
import spotipy
from math import sqrt, degrees, atan, sin, cos, radians, tan
from spotipy.oauth2 import SpotifyOAuth
from colorsys import hsv_to_rgb as HTR
from colorsys import rgb_to_hsv as RTH
import threading
import time
from urllib.request import urlopen
import io
import scipy.ndimage as ndimage

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
box_size = w/6
box_speed = bps


# __VARIABLES__
key_escape = False
key_left = False
key_right = False
key_up = False
key_r = False
lose = False
song_found = False
running = True
spawn = False
is_playing = False
game_start = False
settings = False
timestamp = 0
duration = 0
artist = None
selection = None

black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
spotify_green = (29, 185, 84)
ticks = 200
old_height = h/1.5
max_distance = h/5/2
old_track_name = None
current_track = 0
jump_speed = 4
g = 0
volume = 50
bpm_multiplier = 1

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
    def __init__(self, pos = tuple, dim = tuple, buttonColor = tuple, text = str, textColor = tuple, cornerRadius = 0):
        self.pos = (pos[0]-dim[0]/2, pos[1]-dim[1]/2)
        self.centerPos = pos
        self.originalDimensions = dim
        self.dimensions = dim
        self.originalButtonColor = buttonColor
        self.buttonColor = buttonColor
        self.originalTextColor = textColor
        self.text_color = textColor
        self.rect = pg.Rect(self.pos, self.dimensions)
        self.selected = False
        self.button_text = text
        self.borderRadius = int(cornerRadius)

    def updateFont(self):
        self.text = Text("freesansbold.ttf", self.dimensions[1]/3, self.button_text, self.text_color)
        self.textPos = (self.pos[0]+(self.dimensions[0]-self.text.dimensions[0])/2, 
                        self.pos[1]+(self.dimensions[1]-self.text.dimensions[1])/2)

    def update(self):
        # if hover over button
        if self.selected:
            self.buttonColor = hueChange(self.originalButtonColor, 100)
            self.text_color = hueChange(self.originalTextColor, 100)
            self.dimensions = (self.originalDimensions[0]*1.1, self.originalDimensions[1]*1.1)
            self.pos = (self.centerPos[0]-self.dimensions[0]/2, self.centerPos[1]-self.dimensions[1]/2)
            self.rect = pg.Rect(self.pos, self.dimensions)
            self.updateFont()
        # if not hover over
        else:
            self.buttonColor = self.originalButtonColor
            self.text_color = self.originalTextColor
            self.dimensions = self.originalDimensions
            self.pos = (self.centerPos[0]-self.dimensions[0]/2, self.centerPos[1]-self.dimensions[1]/2)
            self.rect = pg.Rect(self.pos, self.dimensions)
            self.updateFont()

    def draw(self):
        pg.draw.rect(screen, self.buttonColor, self.rect, width=0, border_radius=self.borderRadius)
        screen.blit(self.text.text, self.textPos)


# Text render class
class Text:
    def __init__(self, font, font_size, text, color):
        self.font = pg.font.Font(font, int(font_size))
        self.text = self.font.render(text, True, color)
        self.dimensions = self.font.size(text)


# Slider class
class Slider:
    def __init__(self, pos1, pos2, thickness, color, variable_name, range, steps, text):
        self.pos1 = pos1
        self.pos2 = pos2
        self.thickness = thickness
        self.slider_color = color
        self.knob_color = (100, 100, 100)
        self.variable_name = variable_name
        self.variable_value = globals()[variable_name]
        self.range = range
        self.steps = steps
        self.knob_pos = (mapValues(self.variable_value, range[0], range[1], pos1[0], pos2[0]), pos1[1])
        self.hover = False
        self.selected = False
        self.knob = Circle(self.knob_pos, self.thickness)
        self.value = 0
        self.text_name = text
        if steps != 0:
            self.total_steps = (range[1]-range[0])/steps
        self.updateFont()
    
    def follow(self, pos):
        if self.selected:
            self.knob.pos = (pos[0], self.knob.pos[1])
    
    def updateFont(self):
        self.text = Text("GothamMedium.ttf", 18, self.text_name, spotify_green)
        self.text_pos = (self.pos1[0]-self.text.dimensions[0]-self.knob.radius*2, self.pos1[1]-self.text.dimensions[1]/2)
    
    def update(self):
        # knob selection color change
        if self.hover or self.selected:
            self.knob_color = spotify_green
        else:
            self.knob_color = white
        
        # limit movement of knob
        if self.knob.pos < self.pos1:
            self.knob.pos = self.pos1
        if self.knob.pos > self.pos2:
            self.knob.pos = self.pos2

        # steps locking
        if self.steps != 0:
            pass

        # update assigned variable
        self.value = mapValues(self.knob.pos[0], self.pos1[0], self.pos2[0], self.range[0], self.range[1])
        globals()[self.variable_name] = self.value
    
    def draw(self):
        pg.draw.line(screen, self.slider_color, self.pos1, self.pos2, self.thickness)
        pg.draw.circle(screen, self.knob_color, self.knob.pos, self.knob.radius)
        screen.blit(self.text.text, self.text_pos)


# Circle class
class Circle:
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius


# Mouse Class
class Mouse:
    def __init__(self):
        self.pos = (0, 0)
        self.left_click = False
        self.right_click = False
    
    def update(self):
        self.pos = pg.mouse.get_pos()


# current playing song animation
class Listening:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.progress = None
        self.image = None
        self.length = 1
        self.track_text = None
        self.artist_text = None
        self.selected = False
        self.progressThickness = 9
        self.boundingRect = pg.Rect(self.pos, self.size)
        self.progressBarPos1 = (self.pos[0]+self.size[1]*1.2, self.pos[1]+self.size[1]/1.3)
        self.progressBarPos2 = (self.pos[0]+self.size[0]/1.1, self.pos[1]+self.size[1]/1.3)
        self.progressBarLength = self.progressBarPos2[0]-self.progressBarPos1[0]
        self.progressRect = pg.Rect(self.progressBarPos1[0], self.progressBarPos1[1]-self.progressThickness/2,
        self.progressBarLength, self.progressThickness)
        self.track_text_pos = (((self.pos[0]+self.size[1]*1.2)+(self.pos[0]+self.size[0]/1.1))/2, self.pos[1]+self.size[1]/3)
        self.artist_text_pos = (((self.pos[0]+self.size[1]*1.2)+(self.pos[0]+self.size[0]/1.1))/2, self.pos[1]+self.size[1]/4*2)

    def new(self, imgurl, length, artist, trackName):
        try:
            # Load the image using Pygame
            self.image_str = urlopen(imgurl).read()
            self.image_file = io.BytesIO(self.image_str)
            self.image = pg.image.load(self.image_file)
            # Scale the image
            self.image = pg.transform.scale(self.image, (w//2, 2//2))

            # Convert the image to a numpy array
            self.img_array = pg.surfarray.array2d(self.image)
            self.blurred_img_array = ndimage.gaussian_filter(self.img_array, 5)
            self.image = pg.surfarray.make_surface(self.blurred_img_array)

            # Set the instance variables
            self.length = length
            self.artist = artist
            self.track = trackName
            self.updateFont()

        except Exception as e:
            print("Error loading image:", e)


    def updateFont(self):
        # track font render
        self.track_text = Text("GothamMedium.ttf", 18, self.track, spotify_green)
        self.track_text_pos_offset = (self.track_text_pos[0]-self.track_text.dimensions[0]/2, 
                                      self.track_text_pos[1]-self.track_text.dimensions[1]/2)
        
        # artist font render
        self.artist_text = Text("GothamMedium.ttf", 13, self.track, (94, 94, 94))
        self.artist_text_pos_offset = (self.track_text_pos[0]-self.track_text.dimensions[0]/2, 
                                      self.track_text_pos[1]-self.track_text.dimensions[1]/2)

    def update(self):
        self.progress = timestamp*self.progressBarLength/self.length
        self.progressBarPos2 = (self.progressBarPos1[0]+self.progress, self.progressBarPos1[1])
        self.boundingRect = pg.Rect(self.pos, self.size)
    
    def draw(self):
        pg.draw.rect(screen, (24, 24, 24), self.boundingRect)
        pg.draw.rect(screen, (94, 94, 94), self.progressRect)
        pg.draw.circle(screen, (94, 94, 94), self.progressBarPos1, self.progressThickness/2)
        pg.draw.circle(screen, (94, 94, 94), (self.progressBarPos1[0]+self.progressBarLength, self.progressBarPos1[1]), self.progressThickness/2)
        if self.image is not None:
            screen.blit(self.image, (0,0))
        if self.progress is not None and self.length is not None:
            if self.selected:
                pg.draw.line(screen, spotify_green, self.progressBarPos1, self.progressBarPos2, width=self.progressThickness)
                pg.draw.circle(screen, spotify_green, self.progressBarPos1, self.progressThickness/2)
                pg.draw.circle(screen, (255, 255, 255), self.progressBarPos2, self.progressThickness)
            else:
                pg.draw.line(screen, (255, 255, 255), self.progressBarPos1, self.progressBarPos2, width=self.progressThickness)
                pg.draw.circle(screen, (255, 255, 255), self.progressBarPos2, self.progressThickness/2)
                pg.draw.circle(screen, (255, 255, 255), self.progressBarPos1, self.progressThickness/2)

        if self.artist_text is not None:
            screen.blit(self.artist_text.text, self.artist_text_pos_offset)
            screen.blit(self.track_text.text, self.track_text_pos_offset)

# __FUNCTIONS__
# Rectangle with Rectangle collision function
def rectRectCollide(object1, object2):
   return True if object1.rect.colliderect(object2.rect) else False


# Position with Rectangle collision function
def posRectCollide(pos, rect):
    return True if rect.collidepoint(pos) else False


# Position with circle collision function
def posCircleCollide(pos, circle):
    return True if circle.pos[0]-circle.radius <= pos[0] <= circle.pos[0]+circle.radius and circle.pos[1]-circle.radius <= pos[1] <= circle.pos[1]+circle.radius else False


# Map values
def mapValues(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)


# Vector Addition
def addVector(v1, v2):
   return v1[0]+v2[0], v1[1]+v2[1]


# Hue change
def hueChange(RGB, amount):
    HSV = RTH(RGB[0]/255, RGB[1]/255, RGB[2]/255)
    New = HTR(HSV[0], HSV[1]+amount/255, HSV[2])
    return (New[0]*255, New[1]*255, New[2]*255)


# Search for song and song values
def searchSong():
    global key
    global energy
    global valence
    global track_name
    global artist
    global bpm
    global song_found
    global running
    global is_playing
    global current_track
    global timestamp
    global duration

    while running:
        # Get information about the track you are currently playing
        current_track = sp.current_user_playing_track()
        current_playback = sp.current_playback()

        # Check if there is a track currently playing
        if current_track is not None and current_track.get('item') is not None:
            track_uri = current_track['item']['uri']
            features = sp.audio_features(tracks=[track_uri])
            track_name = current_track['item']['name']
            artist = current_track["item"]["artists"][0]["name"]
            bpm = features[0]["tempo"]
            energy = features[0]["energy"]
            is_playing = current_track["is_playing"]
            key = features[0]["key"]
            valence = features[0]["valence"]
            timestamp = current_playback["progress_ms"]
            duration = current_track["item"]["duration_ms"]
            
            song_found = True
        else:
            song_found = False


# Return variable name from value
def keyReturn(value):
    dictonary = globals().copy()
    for key, val in dictonary.items():
        if val == value:
            return key


# start thread
thread = threading.Thread(target=searchSong)
thread.start()

#before loop setup
boxes = []
Bateman = Character((w/2, h/3), (character_size, character_size), white)
energy, key, valence = 1, 0.3, 0.43
BG = Background()
mouse = Mouse()
listen = Listening((w-600, h-200), (600, 200))

# Setup buttons
main_manu_buttons = []
main_manu_buttons.append(Button((w/4, h/3), (w/3, h/6), white, "Start Game", black, h/8))
main_manu_buttons.append(Button((w/4*3, h/3), (w/3, h/6), white, "Quit", black, h/8))
main_manu_buttons.append(Button((w/4*2, h/1.7), (w/3, h/6), white, "Settings", black, h/8))
settings_menu_buttons = []
settings_menu_buttons.append(Button((w/6, h/11), (w/4, h/8), white, "Back", black, h/8))

# Setup sliders
settings_menu_sliders = []
settings_menu_sliders.append(Slider((w/3.5, h/2), (w/4*3, h/2), 20, (94, 94, 94), "volume", (0, 100), 0, "Volume"))
settings_menu_sliders.append(Slider((w/3.5, h/4), (w/4*3, h/4), 20, (94, 94, 94), "bpm_multiplier", (0, 4), 1, "Bpm scaler"))

# Stagger time for Thread to catch up (Please optimize)
time.sleep(0.4)

# THE LOOP
while running:
    print(bpm_multiplier, volume)
    for event in pg.event.get():

        if event.type == pg.QUIT:
            running = False

        # check for keystrokes
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                key_escape = True
            if event.key == pg.K_UP:
                key_up = True
            if event.key == pg.K_LEFT:
                key_left = True
            if event.key == pg.K_RIGHT:
                key_right = True
            if event.key == pg.K_r:
                key_r = True

        if event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                key_escape = False
            if event.key == pg.K_UP:
                key_up  = False
            if event.key == pg.K_LEFT:
                key_left = False
            if event.key == pg.K_RIGHT:
                key_right = False
            if event.key == pg.K_r:
                key_r = False
        
        # check for mouse clicks
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse.left_click = True
            if event.button == 3:
                mouse.right_click = True
        
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                mouse.left_click = False
            if event.button == 3:
                mouse.right_click = False

    # reset screen
    screen.fill(black)
        # spotify currenlty listening handling
    if posRectCollide(mouse.pos, listen.progressRect):
        listen.selected = True
    else:
        listen.selected = False

    #Draw listen in
    listen.update()
    listen.draw()
    # Main menu
    if not game_start and not settings:
        if listen.image is None and artist is not None and duration is not None:
            listen.new(current_track["item"]["album"]["images"][0]["url"], duration, artist, track_name)
        for button in main_manu_buttons:
            if posRectCollide(mouse.pos, button.rect):
                button.selected = True
                if mouse.left_click:
                    if button.button_text == "Start Game":
                        game_start = True
                        if lose:
                            key_r = True
                    if button.button_text == "Quit":
                        running = False
                    if button.button_text == "Settings":
                        settings = True
            else:
                button.selected = False
        
        # quit game with escape
        if key_escape == True:
            running = False
        
        for button in main_manu_buttons:
            button.update()
            button.draw()
    
    # Settings menu
    elif not game_start and settings:
        if key_escape:
            key_escape = False
            settings = False
        
        # buttons
        for button in settings_menu_buttons:
            if posRectCollide(mouse.pos, button.rect):
                if selection is None:
                    button.selected = True
                    if mouse.left_click:
                        if button.button_text == "Back":
                            settings = False
            else:
                button.selected = False

            if not mouse.left_click:
                selection = None
            
            button.update()
            button.draw()
        
        # sliders
        for slider in settings_menu_sliders:
            if selection is None:
                if posCircleCollide(mouse.pos, slider.knob):
                    slider.hover = True
                    if mouse.left_click:
                        slider.selected = True
                        selection = slider
                else:
                    slider.hover = False
            
            if not mouse.left_click:
                slider.selected = False
                selection = None

            slider.follow(mouse.pos)
            slider.update()
            slider.draw()
    
    # game start
    elif game_start:

        # go back to menu
        if key_escape:
            key_escape = False
            game_start = False

        # update music variables
        bps = bpm/60
        box_speed = bps

        # gravity calulations
        v0 = sqrt((jump_speed)**2+(bps)**2)
        angle = atan(jump_speed/bps)
        x = (tick-box_size)
        y = max_distance
        g = -(2 * v0**2 * cos(angle)**2 * (x * tan(angle) - y))/x**2
        jump_speed = 0.039*bpm

        # check for track change
        if type(current_track) != type(0) and current_track is not None and current_track["item"] is not None:
            if old_track_name != track_name:
                old_track_name = track_name
                BG.new(energy, key, valence, (bps/2, 0))
                print("NEW TRACK!")
                print("Now playing:", track_name, "at:", bpm, "bpm.")
                spawn = False

                # update currently playing
                listen.new(current_track["item"]["album"]["images"][0]["url"], duration, artist, track_name)

        # check if a song is found, and it is playing
        if song_found and is_playing:

            # reset
            if key_r:
                key_r = False
                lose = False
                Bateman.pos = (w/2, h/4)
                Bateman.vec = (0, 0)
                spawn = False
                Bateman.update()

            # while you dont suck
            if not lose:

                # collision check
                for box in boxes:
                    if rectRectCollide(Bateman, box):

                        # top collision
                        if box.pos[1]-Bateman.dim[1] <= Bateman.pos[1] <= box.pos[1]:
                            Bateman.pos = Bateman.pos[0], box.pos[1]-Bateman.dim[1]
                            Bateman.vec = (0, 0)
                            if key_up:
                                key_up = False
                                Bateman.jump()

                        # side collision
                        if Bateman.pos[1]+Bateman.dim[1] > box.pos[1]:
                            Bateman.vec = (-box.speed, Bateman.vec[1])
                        
                        else:
                            Bateman.pos = Bateman.pos[0], box.pos[1]-Bateman.dim[1]

                # check if bateman has fallen
                if Bateman.pos[1] > h or Bateman.pos[0] < 0:
                    lose = True
            
                # Out Of Bounds box removal
                for box in boxes:
                    if box.x+box.dim[0] <= 0:
                        boxes.remove(box)
                
                # update old box height
                if len(boxes) > 0:
                    old_height = boxes[-1].y

                # summon boxes
                if ticks%(int(tick/bps)) == 0:
                    box_color = HTR(energy, 1, 255)
                    if spawn:
                        offset = max_distance * randint(-1, 1)
                        newHeight = old_height + offset
                        if newHeight > h-130:
                            newHeight = h-130
                        if newHeight < h/3:
                            newHeight = h/3
                        if randint(0,1) == 1:
                            boxes.append(Box((w, newHeight), (box_size, box_size/2), box_color, box_speed))
                        else:
                            boxes.append(Box((w, newHeight), (box_size, h), box_color, box_speed))

                    # current attempt at to-do list 1. andreas
                    elif not spawn:
                        for box in boxes:
                            if box.pos[0] < Bateman.pos[0] < box.pos[0]+box.dim[0]:
                                box.dim = (box_size*3, box.dim[1])
                            #else:
                            #    boxes.remove(box)
                            
                        boxes.append(Box((w, old_height), (tick, box_size/2), box_color, box_speed))
            
            # damn bro, you suck
            elif lose:
                font = pg.font.SysFont('GothamMedium', 100)
                screen.blit(font.render("DEAD", True, (200, 50, 50)), (w/3, h/3))

            # UPDATE
            for box in boxes:
                box.update()
            if spawn or key_up:
                spawn = True
                Bateman.update()
            for p in BG.points:
                p = (p[0]-1, p[1])
            BG.update()
            
        # if nothing is playing
        elif not is_playing:
            Bateman.pos = (w/2, h/3)
            # pause bars
            pg.draw.rect(screen, white, pg.Rect(w/9*3, h/4, w/9, h/4*2))
            pg.draw.rect(screen, white, pg.Rect(w/9*5, h/4, w/9, h/4*2))
        
        # draw Bateman, boxes and background
        BG.draw()
         # spotify currenlty listening handling
        if posRectCollide(mouse.pos, listen.progressRect):
            listen.selected = True
        else:
            listen.selected = False

        listen.update()
        listen.draw()

        mouse.update()
        Bateman.draw()
        for box in boxes:
            box.draw()

    # update icon
    if ticks %10 == 0:
        pg.display.set_icon(icon_images[ticks%11])

    # spotify currenlty listening handling
    if posRectCollide(mouse.pos, listen.progressRect):
        listen.selected = True
    else:
        listen.selected = False



    mouse.update()
    

    clock.tick(tick)
    ticks += 1
    pg.display.flip()

pg.display.quit()
pg.quit()
