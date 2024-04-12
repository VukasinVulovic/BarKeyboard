from pynput.keyboard import Listener
import keyboard #had trouble using pynput to send, TODO: migrate whole code to use this library
import time

#mapping for keys (barcode 10000 -> w)...
MAPPING = {
    "100000": 'w',
    "800000": 'a',
    "700000": 's',
    "200000": 'd'
}

def calc_crc8(data): #not correct? but we will use it
    data_len = len(data)

    crc = 0x00

    for i in range(0, data_len):
        crc ^= data[i]

        for _ in range(0, 8):
            crc = (crc << 1) ^ 0x07 if crc & 0x80 != 0 else crc << 1

    return crc

class LimStack:
    def __init__(self, limit=2):
        self.__limit = limit
        self.__data = ['0'] * limit #fill with 0

    def push(self, v):
        self.__data.append(v)
        self.__data = self.__data[1:(self.__limit+1)]

    def peek(self):
        return list(self.__data[:(self.__limit)])
    
    def crc8(self): #calc crc8 for stack
        return calc_crc8(list(map(lambda c: ord(c), self.peek())))

class CRC8HashArray: #hash Array where key is hashed using crc
    def __init__(self, items) -> None:
        self.__items = {}

        for k, v in items.items():
            self.__items[calc_crc8(list(map(lambda c: ord(c), k)))] = v

    def add(self, key, value):
        self.__items[calc_crc8(list(map(lambda c: ord(c), key)))] = value

    def get(self, hash):
        if hash not in self.__items.keys():
            return None
        
        return self.__items[hash]

def main():
    key_len = len(list(MAPPING.keys())[0])

    mapping = CRC8HashArray(MAPPING)
    stack = LimStack(limit=key_len)

    def win32_event_filter(msg, data):
        if data.vkCode == 27: #if Escape, stop program
            listener.stop()
            exit(0)

        listener._suppress = False #allow keypresses

        if data.vkCode == 13 or data.vkCode in range(48, 53): #supress(block input) if key=Enter or 0-9
            listener._suppress = True
            
        print(stack.peek())
        v = mapping.get(stack.crc8())

        if v is not None: #send key for 10ms
            keyboard.press_and_release(v, do_release=False)
            time.sleep(0.01)
            keyboard.press_and_release(v, do_press=False)
        
        if msg != 157: #only if event for keydown, ignore keyup
            stack.push(chr(data.vkCode))

    with Listener(win32_event_filter=win32_event_filter) as listener:
        listener.join()

if __name__ == "__main__":
    main()