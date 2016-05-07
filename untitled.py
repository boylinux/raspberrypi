#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  untitled.py
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

#import smbus                        # smbus Library Python 2.x
from Adafruit_PureIO import smbus    # smbus Library Python 3.x

import time                         # Time Library
import subprocess                   # Processes Library
import threading                    # Threading Library
import os                           # OS Library

from gpiozero import Button              # www.adafruit.com
from datetime import datetime
from mutagen.id3 import ID3              # www.mutagen.com

from rotary_class import RotaryEncoder   # www.bobrathbone.com

class mpg123(threading.Thread):

    def __init__(self, music=''):
        self.music = music
        super(mpg123, self).__init__()
        #threading.Thread.__init__(self)
        self._kill_me = False
        self.player = self.init_player()

    def finish_it(self):
        self._kill_me = True

    def init_player(self):
        return subprocess.Popen(['mpg123', '--remote', self.music], shell=False, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    def run(self):
        '''Thread method that is called when a Thread is started,
        this is the "main loop" of it'''
        try:
            self.player_loop()
        finally:
            self.quit()

    def play(self, music=''):
        music = music or self.music
        if music:
            cmd = 'LOAD ' + music
            self.player_cmd(cmd)

    def stop(self):
        self.player_cmd('STOP')

    def player_cmd(self, cmd):
      '''Protocol to talk to the mpg123 '''
      #self.player.stdin.write(cmd + '\n')
      self.player.stdin.write(bytes(cmd + '\n', "UTF-8"))
      self.player.stdin.flush()

    def quit(self):
        self.player.terminate()

    def player_loop(self):
        player = self.player

        self.play()

        while not self._kill_me:
            status = player.stdout.readline().decode('UTF-8')
            '''here we have to keep reading the stdout, because if we don't
            read from it this buffer get full and the mpg123 stops working.

            I give from it because of this issue, mplayer.py has a better approach
            '''
            #print status
            if status.startswith('@F'): # @F
                cmd_name, cur_frame,  frames_left, cur_seconds, seconds_left = status.split()
                if cmd_name == '@F': # and cur_seconds == '0.00':
                    #self.total_seconds = float(seconds_left)
                    #cur_seconds = float(cur_seconds)
                    self.status = float(seconds_left)#cur_seconds

    def status(self):
      print('status')

GPIO_23 = Button(23, pull_up=True)  # Go Up
GPIO_24 = Button(24, pull_up=True)  # Go Down
GPIO_25 = Button(25, pull_up=True)  # Select

GPIO_22 = Button(22, pull_up=True)  # Do Left
GPIO_10 = Button(10, pull_up=True)  # Do Right

PIN_A = 20
PIN_B = 21
BUTTON = 7

LCD_ADDR = 0x27                            # LCD - IC2 Address
LCD_CHR = 1                                # LCD - Mode - Sending Data
LCD_CMD = 0                                # LCD - Mode - Sending Command

LCD_LINE = []                              # LCD - Address Space
LCD_LINE.insert(0, 0x80)
LCD_LINE.insert(1, 0xC0)
LCD_LINE.insert(2, 0x94)
LCD_LINE.insert(3, 0xD4)

LCD_BACKLIGHT  = 0x08                      # On

FM_ADDR = 0x58                             # FM - IC2 Address
FM_READ = 0x10
FM_WRITE = 0x11

IC2_ENABLE = 0b00000100                    # IC2 - Enable bit
IC2_PULSE = 0.0005
IC2_DELAY = 0.0005

LSM303_ADDRESS_ACCEL = 0x18                # ACC - IC2 Address
LSM303_ADDRESS_MAG = 0x1e                  # MAG - IC2 Address

# Accel registers
LSM303_REGISTER_ACCEL_CTRL_REG1_A = 0x20   # 00000111   rw
LSM303_REGISTER_ACCEL_CTRL_REG4_A = 0x23   # 00000000   rw
LSM303_REGISTER_ACCEL_OUT_X_L_A = 0x28
LSM303_REGISTER_ACCEL_OUT_X_H_A = 0x29
LSM303_REGISTER_ACCEL_OUT_Y_L_A = 0x2A
LSM303_REGISTER_ACCEL_OUT_Y_H_A = 0x2B
LSM303_REGISTER_ACCEL_OUT_Z_L_A = 0x2C
LSM303_REGISTER_ACCEL_OUT_Z_H_A = 0x2D
# Mag registers
LSM303_REGISTER_MAG_MR_REG_M = 0x02

IC2 = smbus.SMBus(1)

os.system('pkill mpg123')          # Clean up any mpg123, running

global MP3
MP3 = mpg123('')
MP3.start()
global USB_root
USB_root = '/usb/'
global USB_files
USB_files = []
global USB_index
USB_index = 0
# Option Values
global OPTION_MODE                # 0 = clock, 1 = MP3, 2 = Radio
OPTION_MODE = 0
global OPTION_REPEAT              # MP3 repeat track
OPTION_REPEAT = False
#global OPTION_LOOP               # MP3 loop track
#OPTION_LOOP = True
global OPTION_AUTO                # MP3 auto next track
OPTION_AUTO = True
global OPTION_ID3                 # MP3;ID3 enable/disable
OPTION_ID3 = True
global OPTION_VOL                 # Default volume level
OPTION_VOL = 40

os.system('amixer -q -c 1 cset numid=6 -- ' + str(OPTION_VOL) + '%,' + str(OPTION_VOL) + '%')

def switch_event(event):
  if event == RotaryEncoder.CLOCKWISE:
    displayVolume(False)
  elif event == RotaryEncoder.ANTICLOCKWISE:
    displayVolume(True)
  #elif event == RotaryEncoder.BUTTONDOWN:
    #print("Button down")
  #elif event == RotaryEncoder.BUTTONUP:
    #print("Button up")
  return

volume = RotaryEncoder(PIN_A,PIN_B,BUTTON,switch_event)

def LCD_toggle_enable(bits):
  # Toggle enable
  time.sleep(IC2_DELAY)
  IC2.write_byte(LCD_ADDR, (bits | IC2_ENABLE))
  time.sleep(IC2_PULSE)
  IC2.write_byte(LCD_ADDR,(bits & ~IC2_ENABLE))
  time.sleep(IC2_DELAY)

def LCD_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits <<4) & 0xF0) | LCD_BACKLIGHT

  try:
    # High bits
    IC2.write_byte(LCD_ADDR, bits_high)
    LCD_toggle_enable(bits_high)

    # Low bits
    IC2.write_byte(LCD_ADDR, bits_low)
    LCD_toggle_enable(bits_low)
  except:
    print('LCD Module - Offline')

def LCD_init():
  # Initialise display
  LCD_byte(0x33,LCD_CMD)     # 110011 Initialise
  LCD_byte(0x32,LCD_CMD)     # 110010 Initialise
  LCD_byte(0x06,LCD_CMD)     # 000110 Cursor Move Direction
  LCD_byte(0x0C,LCD_CMD)     # 001100 Display On,Cursor Off, Blink Off {0x0C}
  LCD_byte(0x28,LCD_CMD)     # 101000 Data Length, Number Of Lines, Font Size # {0x28}
  LCD_byte(0x01,LCD_CMD)     # 000001 Clear Display
  time.sleep(IC2_DELAY)

def FM_byte(bits, mode):
  #
  try:
    IC2.write_byte(FM_ADDR, 0)
  except:
    print('FM Module - Offline')

def FM_init():
  # Initialise FM Module
  FM_byte(0x00,0)           # !!!NEEDS MORE WORK!!!

def AXIS_init():
  # Initialise ACC/MAG Module
  WRITE_ACCEL(LSM303_REGISTER_ACCEL_CTRL_REG1_A, 0x27) #initialise the Accelerometer
  WRITE_ACCEL(LSM303_REGISTER_ACCEL_CTRL_REG4_A, 0x40)

  WRITE_MAG(LSM303_REGISTER_MAG_MR_REG_M, 0x00)        #initialise the Magnetometer

def WRITE_ACCEL(register,value):
  try:
    IC2.write_byte_data(LSM303_ADDRESS_ACCEL, register, value)
  except:
    print('AXIS Module - Offline')

def WRITE_MAG(register,value):
  try:
    IC2.write_byte_data(LSM303_ADDRESS_MAG, register, value)
  except:
    print('AXIS Module - Offline')

def READ_ACCEL(register):
  try:
    temp = IC2.read_byte_data(LSM303_ADDRESS_ACCEL, register)
  except:
    temp = 0

  return temp

def accelDatax():
  gxhi = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_X_L_A)
  gxlo = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_X_H_A)
  gxtotal = ((gxhi << 8) | gxlo)
  return gxtotal

def accelDatay():
  gyhi = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_Y_L_A)
  gylo = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_Y_H_A)
  gytotal = ((gyhi << 8) | gylo)
  return gytotal

def accelDataz():
  gzhi = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_Z_L_A)
  gzlo = READ_ACCEL(LSM303_REGISTER_ACCEL_OUT_Z_H_A)
  gztotal = ((gzhi << 8) | gzlo)
  return gztotal

def LCD_clear():
  LCD_byte(0x01,LCD_CMD)     # 000001 Clear display

def LCD_draw(row, column, value):
   LCD_byte(LCD_LINE[row] + column, LCD_CMD)
   LCD_byte(value,LCD_CHR)

def LCD_print(row, column, string):
  y = len(string)

  for x in range(y):
    LCD_draw(row, column + x,ord(string[x]))

def displayFlight(mode):
  print('displayFlight')
  LCD_clear()

  flag_1 = False                  # Display runtime h
  scroll = False                  # Enable scrolling
  pause = False                   # Paused/Running

  x = 0
  y = 0
  
  vol_0 = False
  vol_1 = False 

  global OPTION_MODE

  if OPTION_MODE == 1:
    track = ID3_print()
    if len(track) >= 18:
      scroll = True
    LCD_print(2, 1, track[:18])

  while True:
    if GPIO_23.is_pressed:
      return

    if GPIO_24.is_pressed:
      return

    if GPIO_25.is_pressed:    # SELECT
      return

    if vol_0 == True and vol_1 == True:
      if OPTION_MODE == 1:       # MP3 - pause/play
        pause = not pause
        if pause:
          print('MP3 - paused')
        else:
          print('MP3 - play')
        MP3.player_cmd('pause')
        time.sleep(.5)
    else:
      if vol_0 == True:
        displayVolume(True)
      if vol_1 == True:
        displayVolume(False)

    if OPTION_MODE == 2:      # FM Reciever
      LCD_print(1, 1, "101.9 Mhz")
      LCD_print(2, 1, "Classic FM")

    if OPTION_MODE == 1:      # MP3 Player
      a = MP3.status
      try:
        m, s = divmod(a, 60)
        h, m = divmod(m, 60)
      except:
        print('displayTime - MP3.status - error')
        h = 0
        m = 0
        s = 0

      if int(h) != 0 and flag_1 == False:
        LCD_draw(0, 12, ord(str(int(h)).zfill(2)[:1]))
        LCD_draw(0, 13, ord(str(int(h)).zfill(2)[1:]))
        LCD_draw(0, 14, ord(":"))
      else:
        flag_1 = True
        LCD_draw(0, 12, 32)
        LCD_draw(0, 13, 32)
        LCD_draw(0, 14, 32)

      LCD_draw(0, 15, ord(str(int(m)).zfill(2)[:1]))
      LCD_draw(0, 16, ord(str(int(m)).zfill(2)[1:]))
      LCD_draw(0, 17, ord(":"))

      LCD_draw(0, 18, ord(str(int(s)).zfill(2)[:1]))
      LCD_draw(0, 19, ord(str(int(s)).zfill(2)[1:]))

      if GPIO_10.is_pressed:    # NEXT ->
        print('next')
        flag_1 = False
        MP3_next()
        track = ID3_print()

        if len(track) >= 18:
          scroll = True
        else:
          scroll = False

        y = 0
        x = 0

        LCD_print(2, 1, track[:18])

      if int(h) == 0 and int(m) == 0 and int(s) == 0:
        if OPTION_MODE == 1:
          if OPTION_AUTO == True:
            print('auto')
            flag_1 = False
            MP3_next()
            track = ID3_print()

            if len(track) >= 18:
              scroll = True
            else:
              scroll = False

            y = 0
            x = 0

            LCD_print(2, 1, track[:18])

          else:
            if OPTION_REPEAT == True:
              flag_1 = False
              print('repeat')
              MP3.play()
              time.sleep(1)
            else:
              OPTION_MODE = 0
              LCD_clear()

      if GPIO_22.is_pressed:    # <- BACK
        print('back')
        flag_1 = False
        MP3_back()
        track = ID3_print()
        LCD_print(2, 1, track[:18])

      if scroll == True:
        y = y + 1
        if y == 19:
          y = 0
          LCD_print(2, 1, track[x:][:18])
          x = x + 1

          if x == len(track):
            x = 0

    if OPTION_MODE == 0:      # Clock
      hours = datetime.now().strftime('%H')
      minutes = datetime.now().strftime('%M')
      seconds = datetime.now().strftime('%S')

      LCD_draw(1,6,ord(hours[:1]))
      LCD_draw(1,7,ord(hours[1:]))
      LCD_draw(1,8,ord(":"))
      LCD_draw(1,9,ord(minutes[:1]))
      LCD_draw(1,10,ord(minutes[1:]))
      LCD_draw(1,11,ord(":"))
      LCD_draw(1,12,ord(seconds[:1]))
      LCD_draw(1,13,ord(seconds[1:]))
      time.sleep(.1)
      
      #LCD_print(0,0,str(accelDatax()))
      #LCD_print(1,0,str(accelDatay()))
      #LCD_print(2,0,str(accelDataz()))

def displaySplash():
  print('displaySplash')

  LCD_draw(0,0,162)
  LCD_draw(3,19,163)

  LCD_print(3,0, "Python 3")
    
  x = 2
  for letter in 'Raspberry Pi':
    LCD_draw(1,x,255)
    time.sleep(.1)
    LCD_draw(1,x,ord(letter))
    x = x + 1

  x = 15
  for letter in 'Zero':
    LCD_draw(2,x,255)
    time.sleep(.1)
    LCD_draw(2,x,ord(letter))
    x = x + 1

def displayMP3():
  print('displayMP3')
  LCD_clear()

  menuItem = []
  menuItem.insert(0, 'Play/Stop ')
  menuItem.insert(1, 'File      ')
  menuItem.insert(2, 'Folder    ')
  menuItem.insert(3, 'Options   ')
  menuItem.insert(4, 'Exit      ')

  curIndex = 0

  LCD_print(0, 0,'MP3 Player')
  LCD_print(2, 5, menuItem[curIndex])
  cursorUI(curIndex, len(menuItem))

  tick = 0

  global OPTION_MODE

  while True:
    tick = tick + 1

    if GPIO_22.is_pressed:
      tick = 0
      if curIndex != 0:
        curIndex = curIndex - 1
        LCD_print(2, 5, menuItem[curIndex])
      cursorUI(curIndex, len(menuItem))

    if GPIO_10.is_pressed:
      tick = 0
      if curIndex != 4:
        curIndex = curIndex + 1
        LCD_print(2, 5, menuItem[curIndex])
      cursorUI(curIndex, len(menuItem))

    if GPIO_25.is_pressed:
      tick = 0
      if curIndex == 0:
        if OPTION_MODE == 0:
          print('play')

          try:
            MP3.play()
            OPTION_MODE = 1
          except:
            print('MP3 - play - error')
            OPTION_MODE = 0
        else:
          print('stop')
          MP3.stop()
          OPTION_MODE = 0

      if curIndex == 1:
        track = MP3_file()

        LCD_clear()
        LCD_draw(2, 18, 62)
        LCD_print(0, 0,'MP3 Player')
        LCD_print(2, 5, menuItem[curIndex])

        print(track)

        MP3.music = USB_root + track

      if curIndex == 2:
        MP3_folder()
        LCD_print(0, 0,'MP3 Player')
        LCD_print(2, 5, menuItem[curIndex])
        cursorUI(curIndex, len(menuItem))

      if curIndex == 3:
        displayMP3Options()
        LCD_print(0, 0,'MP3 Player')
        LCD_print(2, 5, menuItem[curIndex])
        cursorUI(curIndex, len(menuItem))

      if curIndex == 4:
        return

    time.sleep(0.15)
    if tick == 80:
       return

def displayRadio():
  print('displayRadio')
  LCD_clear()

  menuItem = []
  menuItem.insert(0, 'Exit')

  curIndex = 0
  LCD_print(0, 0, 'FM Radio')
  LCD_print(2, 3, menuItem[curIndex])
  cursorUI(curIndex, len(menuItem))
  
  tick = 0

  global OPTION_MODE

  while True:
    tick = tick + 1
    if GPIO_25.is_pressed:
      return

    
    time.sleep(.15)
   
    if tick == 40:
      OPTION_MODE = 2
      return 0

def displayOptions():
  print('displayOptions')
  LCD_clear()
  
  LCD_print(0, 0,'Options')
  
  time.sleep(5)

def displayMP3Options():
  print('displayMP3Options')
  LCD_clear()

  menuItem = []
  menuItem.insert(0, 'Repeat ')
  menuItem.insert(1, 'Volume ')
  menuItem.insert(2, 'ID3    ')
  menuItem.insert(3, 'Auto   ')
  menuItem.insert(4, 'Exit ')

  curIndex = 0
  LCD_print(0, 0,'MP3 Options')
  LCD_print(2, 3, menuItem[curIndex])
  cursorUI(curIndex, len(menuItem))

  tick = 0

  while True:
    tick = tick + 1

    if GPIO_22.is_pressed:
      tick = 0
      if curIndex != 0:
        curIndex = curIndex - 1
        LCD_print(2, 3, menuItem[curIndex])
      cursorUI(curIndex, len(menuItem))

#      if curIndex == 0:
#        LCD_print(2, 10, '[' + str(OPTION_VOL) + ']')
#      if curIndex == 1:
#        LCD_print(2, 10, '[' + str(OPTION_ID3) + ']')
#      if curIndex == 2:
#        LCD_print(2, 10, '[' + str(OPTION_AUTO) + ']')
#      if curIndex == 3:
#        LCD_print(2, 10, '[' + str(OPTION_REPEAT) + ']')

    if GPIO_10.is_pressed:
      tick = 0
      if curIndex != 4:
        curIndex = curIndex + 1
        LCD_print(2, 3, menuItem[curIndex])
      cursorUI(curIndex, len(menuItem))

#      if curIndex == 0:
#        LCD_print(2, 10, '[' + str(OPTION_VOL) + ']')
#      if curIndex == 1:
#        LCD_print(2, 10, '[' + str(OPTION_ID3) + ']')
#      if curIndex == 2:
#        LCD_print(2, 10, '[' + str(OPTION_AUTO) + ']')
#      if curIndex == 3:
#        LCD_print(2, 10, '[' + str(OPTION_REPEAT) + ']')

    if GPIO_25.is_pressed:
      tick = 0
      if curIndex == 4:
        LCD_clear()
        return

    if tick == 40:
      LCD_clear()
      return

    time.sleep(.15)

def displayVolume(mode):
  print('displayVolume')

  global OPTION_VOL

  if mode == True:
    if OPTION_VOL != 100:
      OPTION_VOL = OPTION_VOL + 2
  else:
    if OPTION_VOL != 0:
      OPTION_VOL = OPTION_VOL - 2

#  x = OPTION_VOL / 100                   # Maths!!
#  y = int(x * 18)
  print(OPTION_VOL)
  os.system('amixer -q -c 1 cset numid=6 -- ' + str(OPTION_VOL) + '%,' + str(OPTION_VOL) + '%')

def displayMenu():
  print('displayMenu')
  LCD_clear()

  menuItem = []
  menuItem.insert(0, 'MP3 Player')
  menuItem.insert(1, 'FM Radio  ')
  menuItem.insert(2, 'Options   ')

  curIndex = 0
  LCD_draw(2, 18, 62)

  tick = 0

  LCD_print(0, 0,'Main Menu')
  LCD_print(2, 5, menuItem[curIndex])
  cursorUI(curIndex, len(menuItem))

  while True:
    tick = tick + 1

    if GPIO_22.is_pressed:
      tick = 0
      if curIndex != 0:
        curIndex = curIndex - 1
        LCD_print(2, 5, menuItem[curIndex])
        cursorUI(curIndex, len(menuItem))

    if GPIO_10.is_pressed:
      tick = 0
      if curIndex != 2:
        curIndex = curIndex + 1
        LCD_print(2, 5, menuItem[curIndex])
        cursorUI(curIndex, len(menuItem))

    if GPIO_25.is_pressed:
      tick = 0
      LCD_clear()
      return curIndex + 1

    time.sleep(0.15)
    if tick == 50:
      LCD_clear()
      return 0

def cursorUI(index, last):
  print('cursorUI')

#UI - Arrows
  if index == 0:
    LCD_draw(2, 18, 62)      #                    >
    LCD_draw(2, 1, 32)       # 
  else:
    LCD_draw(2, 1, 60)       # <
#UI - Arrows
  if index == last - 1:
    LCD_draw(2, 18, 32)

def MP3_folder():
    print('MP3_folder')
    LCD_clear()

    curIndex = 0
    search = os.listdir('/usb/')

    folders = []
    index = 0

    for item in search:
      if os.path.isdir('/usb/' + item):
        if item != 'lost+found':
          folders.insert(index, item)
          index = index + 1

    folders.sort()

    LCD_print(0, 1,folders[0][:18])
    LCD_print(1, 1,folders[1][:18])
    LCD_print(2, 1,folders[2][:18])
    LCD_print(3, 1,folders[3][:18])

    index = 0
    LCD_draw(curIndex, 0, 62)

    global USB_root
    global USB_files
    global USB_index

    while True:
      if GPIO_23.is_pressed:
        if curIndex != 0:
          LCD_draw(curIndex, 0, 32)
          curIndex = curIndex -1
          LCD_draw(curIndex, 0, 62)
        else:
          if index != 0:
            index = index - 1
            LCD_print(0, 1,folders[index + 0][:18].ljust(18))
            LCD_print(1, 1,folders[index + 1][:18].ljust(18))
            LCD_print(2, 1,folders[index + 2][:18].ljust(18))
            LCD_print(3, 1,folders[index + 3][:18].ljust(18))

      if GPIO_24.is_pressed:
        if curIndex != 3:
          LCD_draw(curIndex, 0, 32)
          curIndex = curIndex + 1
          LCD_draw(curIndex, 0, 62)
        else:
          if index != len(folders) - 4:
            index = index + 1
            LCD_print(0, 1,folders[index + 0][:18].ljust(18))
            LCD_print(1, 1,folders[index + 1][:18].ljust(18))
            LCD_print(2, 1,folders[index + 2][:18].ljust(18))
            LCD_print(3, 1,folders[index + 3][:18].ljust(18))

      if GPIO_25.is_pressed:
        LCD_clear()
        USB_root = '/usb/' + folders[index + curIndex] + '/'
        MP3_filter()
        USB_index = 0
        return

      time.sleep(0.15)

def MP3_file():
  print('MP3_file')
  LCD_clear()

  curIndex = 0

  MP3_filter()

  LCD_draw(2, 19, 62)
  MP3_print(0)

  while True:
    if GPIO_22.is_pressed:
      if curIndex != 0:
        curIndex = curIndex - 1
      else:
        LCD_draw(3, 0, 32)
      MP3_print(curIndex)

    if GPIO_10.is_pressed:
      if curIndex != len(USB_files) - 1:
        curIndex = curIndex + 1
        LCD_draw(2, 0 ,60)
      else:
        LCD_draw(2, 19, 32)
      MP3_print(curIndex)

    if GPIO_25.is_pressed:
      USB_index = curIndex
      return USB_files[USB_index]

    time.sleep(0.15)

def MP3_filter():
  print('MP3_filter')

  global USB_files

  print(USB_root)

  index = 0
  USB_files = []

  for file in os.listdir(USB_root):
    if file.endswith('.mp3'):
      USB_files.insert(index, file)
      index = index + 1

  if len(USB_files) == 0:
    USB_files.insert(0, 'NO FILES')
    
  USB_files.sort()

def MP3_next():
  print('MP3_next')

  global USB_index
  global OPTION_MODE

  if len(USB_files) -1 != USB_index:
    USB_index = USB_index + 1
  else:
    USB_index = 0

  if os.path.isfile(USB_root + USB_files[USB_index]):
    MP3.music = USB_root + USB_files[USB_index]
    MP3.play()
  else:
    OPTION_MODE = 0

def MP3_back():
  print('MP3_back')

  global USB_index
  global OPTION_MODE

  if USB_index != 0:
    USB_index = USB_index -1
  else:
    USB_index = len(USB_files) - 1

  if os.path.isfile(USB_root + USB_files[USB_index]):
    MP3.music = USB_root + USB_files[USB_index]
    MP3.play()
  else:
    OPTION_MODE = 0

def MP3_print(index):
  print('MP3_print')

  path = USB_root + USB_files[index] 

  musicTitle = MP3_ID3(path, 1)
  musicAlbum = MP3_ID3(path, 2)

  LCD_print(0, 0, str(index) + '/' + str(len(USB_files) - 1))
  
  if musicAlbum != musicTitle:
    LCD_print(1, 1, musicAlbum[:18].ljust(18))

  LCD_print(2, 1, musicTitle[:18].ljust(18))

def MP3_ID3(file, index):
  print('MP3_ID3')
  print(file)

  if OPTION_ID3 == True:
    try:
      track = ID3(file)
      track_1 = track.pprint()
      track_2 = track_1.title()
      track_3 = track_2.split('\n')
      return track_3[index][5:]
    except:
      if index == 1: # file
        x = str(file).split('/')[-1:][0]
        y = str(x).split('.mp3')[0]
      if index == 2: # folder
        y = str(file).split('/')[-2:][0]
      return y
  else:
    if index == 1: # file
      x = str(file).split('/')[-1:][0]
      y = str(x).split('.mp3')[0]
    if index == 2: # folder
      y = str(file).split('/')[-2:][0]
    return y

def ID3_print():
  print('ID3_print')

  musicTitle = MP3_ID3(MP3.music, 1)
  musicAlbum = MP3_ID3(MP3.music, 2)

  LCD_print(1, 1, musicAlbum[:18].ljust(18))

  return musicTitle.title() + ' '

def main():
  print('main')

  menuIndex = 0

  LCD_init()
  FM_init()
  AXIS_init()

  displaySplash()
  time.sleep(5)
  LCD_clear()

  while True:
    menuIndex = displayMenu()
    time.sleep(.15)

    if menuIndex == 0: # Clock
      displayFlight(0)

    if menuIndex == 1: # MP3 Player
      displayMP3()

    if menuIndex == 2: # FM Radio
      displayRadio()

    if menuIndex == 3: # Options
      displayOptions()

if __name__ == '__main__':
  main()
