import ctypes
import time
import numpy as np
import cv2
import pyautogui

LEFT = 0x25
UP = 0x26
RIGHT = 0x27
DOWN = 0x28
Z=0x5a
X=0x58
SHIFT=0x10

def getkey(key):
    return(bool(ctypes.windll.user32.GetAsyncKeyState(key)&0x8000))

def getKeys():
    str=''
    if getkey(LEFT):
        str+="left,"
    if getkey(RIGHT):
        str+="right,"
    if getkey(UP):
        str+="up,"
    if getkey(DOWN):
        str+="down,"
    if getkey(Z):
        str+="Z,"
    if getkey(X):
        str+="X,"
    if getkey(SHIFT):
        str+="SHIFT,"
    return str



stamp=str(time.time())

fourcc = cv2.VideoWriter_fourcc('D','I','V','X')
writer = cv2.VideoWriter('data/output'+stamp+'.avi',fourcc,30,(384,448))
f=open('data/keys'+stamp+'.txt',mode='w')

def save_data(frame):
    writer.write(frame)
    f.write(getKeys()+'\n')



def main():
    libc = ctypes.WinDLL("Project5.dll")
    x=384*448*3
    life_board_size=144*48*3

    UBYTE_Array = ctypes.c_ubyte * x
    Life_Board=ctypes.c_ubyte*life_board_size

    i_arr=[0*x]
    i_arr_c=UBYTE_Array(*i_arr)

    life_board_arr=[0*life_board_size]
    life_board_arr_c=Life_Board(*life_board_arr)

    t1=time.time()
    count=0
    sum=0
    before_img=0
    start=False

    while True:
        libc.capture_foreground(i_arr_c)
        image=np.ctypeslib.as_array(i_arr_c).reshape(448,384,3)
        image=cv2.flip(image,0)


        cv2.imshow("aa",image)
        cv2.waitKey(1)
        before_img=image
        if 'SHIFT' in getKeys():
            start=True
        if start:
            save_data(image)
        print(getKeys())




if __name__ == '__main__':
    main()
