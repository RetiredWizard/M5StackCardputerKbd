"""
`M5StackCardputerKbd`
====================================================

CircuitPython M5Stack Cardputer Matrix Keyboard driver.

* Author(s): foamyguy during YouTube livestream
             https://www.youtube.com/watch?v=la7g24fP7IQ&t=4s

             retiredwizard added modifier keys (shift, alt, ...) and minor performance changes

"""


import board
import digitalio
import keypad
from adafruit_debouncer import Debouncer
#import time

class MultiplexerKeys():

    def __init__(self,multiplexed_row_pins, column_pins, value_when_pressed=False):
        self.row_pins = multiplexed_row_pins
        self.column_pins = column_pins
        self.row_dio_objs = []
        self.col_dio_objs = []
        
        # Initialize the row pins as outputs
        for row_pin in self.row_pins:
            _cur_dio = digitalio.DigitalInOut(row_pin)
            _cur_dio.direction = digitalio.Direction.OUTPUT
            self.row_dio_objs.append(_cur_dio)
            
        # Initialize the colun pins as inputs with pull-ups
        for column_pin in self.column_pins:
            _cur_dio = digitalio.DigitalInOut(column_pin)
            _cur_dio.direction = digitalio.Direction.INPUT
            _cur_dio.pull = digitalio.Pull.UP
            self.col_dio_objs.append(Debouncer(_cur_dio,.1))
#            self.col_dio_objs.append(_cur_dio)
        
        self.value_when_pressed = value_when_pressed
        
        self._events = []
        self._last_key = None
        
    @property
    def events(self):
        self._scan()
        return self._events
    
# Function to scan the key matrix
    def _scan(self):
        self._events = []
        key_num = -1   # Set so held button can be differentiated from no key pressed
        for i in range(8):
            self.set_multiplexer_state(i)
            for col, column_pin in enumerate(self.col_dio_objs):
                column_pin.update()
                column_pin.update()
                while column_pin.state not in [0,3]:
                    column_pin.update()
                if column_pin.value == self.value_when_pressed:  # If a key is pressed
                    key_num = (i * len(self.col_dio_objs)) + col
                    #print("Key ({}, {:03b}, {}) pressed".format(key_num, i, col))
                    self._events.append(keypad.Event(key_number=key_num, pressed=True))
                    self._last_key = key_num
#                    time.sleep(.1)
        if key_num == -1:    # No keys pressed
            if self._last_key is not None:
                self._events.append(keypad.Event(key_number=self._last_key, pressed=False))
                self._last_key = None
#                time.sleep(.1)

    def set_multiplexer_state(self, state_binary):
        for idx, compare in enumerate((0b100,0b010,0b001)):
            self.row_dio_objs[idx].value = True if state_binary & compare else False
    
class Cardputer():
    def __init__(self):
        row_pins = (board.KB_A_0, board.KB_A_1, board.KB_A_2)
        column_pins = (
            board.KB_COL_0, board.KB_COL_1, board.KB_COL_2, board.KB_COL_3, board.KB_COL_4, board.KB_COL_5, board.KB_COL_6)

        self._KEY_MATRIX_LUT = {
            # col 1
            49:("`","~","ESC"), 21:("\t","",""), 35:("FN","",""), 7:("CTRL","",""),
            
            # row 1
            42:("1","!",""), 50:("2","@",""), 43:("3","#",""), 51:("4","$",""),
            44:("5","%",""), 52:("6","^",""), 45:("7","&",""), 53:("8","*",""),
            46:("9","(",""), 54:("0",")",""), 47:("_","-",""), 55:("=","+",""),
            48:("\x08","DEL","DEL"),
            
            # row 2
            14:("q","Q",""), 22:("w","W",""), 15:("e","E",""),
            23:("r","R",""), 16:("t","T",""), 24:("y","Y",""), 17:("u","U",""),
            25:("i","I",""), 18:("o","O",""), 26:("p","P",""), 19:("[","{",""),
            27:("]","}",""), 20:("\\","|",""),

            # row 3
            28:("SHIFT","",""), 36:("a","A",""),
            29:("s","S",""), 37:("d","D",""), 30:("f","F",""), 38:("g","G",""),
            31:("h","H",""), 39:("j","J",""), 32:("k","K",""), 40:("l","L",""),
            33:(";",":","UP"), 41:("'",'"',""), 34:("\n","",""),
            
            # row 4
            0:("OPT","",""),
            8:("ALT","",""), 1:("z","Z",""), 9:("x","X",""), 2:("c","C",""),
            10:("v","V",""), 3:("b","B",""), 11:("n","N",""), 4:("m","M",""),
            12:(",","<","LEFT"), 5:(".",">","DOWN"), 13:("/","?","RIGHT"), 6:(" ","","")
        }    
        
        self.keyboard = MultiplexerKeys(row_pins, column_pins)
        
        self.shift = False
        self.funct = False
        self.ctrl = False
        self.opt = False
        self.alt = False
        
    def check_keyboard(self):
        events = self.keyboard.events
        new_char_buffer = ""
        if events:
            for event in events:
                if event.pressed:
                    new_char = self._KEY_MATRIX_LUT[event.key_number][0]
                    if new_char in ['SHIFT','FN','CTRL','OPT','ALT']:
                        new_char = ""
                    else:
                        if self.shift:
                            new_char = self._KEY_MATRIX_LUT[event.key_number][1]
                            self.shift = False
                        elif self.funct:
                            new_char = self._KEY_MATRIX_LUT[event.key_number][2]
                            self.funct = False
                        new_char_buffer += new_char
                else:
                # For modifer keys disable auto-repeat by only responding to "RELEASE" events
                    new_char = self._KEY_MATRIX_LUT[event.key_number][0]
                    if new_char == "SHIFT":
                        self.shift = not self.shift
                    elif new_char == "FN":
                        self.funct = not self.funct
                    elif new_char == "CTRL":
                        self.ctrl = not self.ctrl
                    elif new_char == "OPT":
                        self.opt = not self.opt
                    elif new_char == "ALT":
                        self.alt = not self.alt
                    

        return new_char_buffer

# Exmple Usage:
#
cardputer = Cardputer()

while True:
    print(cardputer.check_keyboard(),end="")

