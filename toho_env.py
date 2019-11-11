import ctypes
import time
import numpy as np
import cv2
import pyautogui


class toho_env:
    def __init__(self,ch=1,width=84,height=84):
        self.LEFT = 0x25
        self.UP = 0x26
        self.RIGHT = 0x27
        self.DOWN = 0x28
        self.Z=0x5a
        self.X=0x58
        self.SHIFT=0x10
        self.libc = ctypes.WinDLL("Project5.dll")
        self.x=384*448*3
        self.life_board_size=144*48*3

        self.UBYTE_Array = ctypes.c_ubyte * self.x
        self.Life_Board=ctypes.c_ubyte*self.life_board_size

        self.i_arr=[0*self.x]
        self.i_arr_c=self.UBYTE_Array(*self.i_arr)
        self.life_pointer=ctypes.c_int(0)
        self.reward_pointer=ctypes.c_int(0)
        self.done_pointer=ctypes.c_int(0)
        self.loc_x=ctypes.c_int(0)
        self.loc_y=ctypes.c_int(0)

        self.libc.step.restype = None
        self.libc.step.argtypes = (ctypes.c_int ,ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

        self.libc.templatematch.restype = ctypes.c_int
        self.libc.templatematch.argtypes = (ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))


        self.life_board_arr=[0*self.life_board_size]
        self.life_board_arr_c=self.Life_Board(*self.life_board_arr)
        self.ch=ch
        self.width=width
        self.height=height
        self.frame_count=0
        self.life=2
        pyautogui.FAILSAFE=False

    def press_cursor(self,keys):
        for key in keys:
            pyautogui.keyDown(key)
        for key in ['left','up','right','down']:
            if not key in keys:
                pyautogui.keyUp(key)

    def action(self,action):
        keys=[['left'],['up'],['right'],['down'],[],['left','up'],['left','down'],['right','up'],['right','down']]
        #print(keys[action[0]])
        self.press_cursor(keys[action[0]])

        # if action[1]==0:
        #     pyautogui.keyUp('z')
        # if action[1]==1:
        #     pyautogui.keyDown('z')
        pyautogui.keyDown('z')


    def step2(self,action):
        self.libc.step(action[0],self.i_arr_c,self.reward_pointer,self.life_pointer,self.done_pointer)
        image=np.ctypeslib.as_array(self.i_arr_c).reshape(448,384,3)
        image=cv2.resize(image , (self.width,self.height))
        if self.done_pointer.value==1:
            self.press_cursor([])
            pyautogui.keyUp('z')
            print('GameOver')
        return image,self.reward_pointer.value,self.done_pointer.value,None


    def temp_match(self):
        self.libc.templatematch(self.i_arr_c,self.reward_pointer,self.life_pointer)
        return self.reward_pointer.value,self.life_pointer.value



    def step(self,action):
        self.libc.capture_foreground(self.i_arr_c)
        image=np.ctypeslib.as_array(self.i_arr_c).reshape(448,384,3)
        image=cv2.flip(image,0)

        self.libc.capture_life_board(self.life_board_arr_c)
        life_img=np.ctypeslib.as_array(self.life_board_arr_c).reshape(48,144,3)
        life_img=cv2.flip(life_img,0)


        life=0
        done=False
        reward=0


        for j in range(9):
            life+=life_img[8,8+16*j][2]//128
        if self.life!=life:
            self.life=life
            reward-=1

        self.frame_count+=1
        if self.frame_count%10==0:
            reward+=0.05


        if life==0:
            if (image[283,228]==[87,87,174]).all() and (image[273,189]==[59,59,117]).all() and (image[203,168]==[126,126,126]).all():
                self.press_cursor([])
                pyautogui.keyUp('z')
                reward-=1
                done=True
            elif (image[251,203]==[87,87,174]).all() and (image[237,177]==[90,90,179]).all() and (image[249,187]==[93,93,185]).all():
                self.press_cursor([])
                pyautogui.keyUp('z')
                reward-=1
                done=True
        elif (image[280 ,348]==[187,187,187]).all() and (image[225,357]==[33,41,45]).all():
            self.press_cursor([])
            pyautogui.keyUp('z')
            reward-=1
            done=True
        elif (image[436 ,44]==[0,0,0]).all() and (image[434,25]==[0,0,0]).all():
            self.press_cursor([])
            pyautogui.keyUp('z')
            reward-=1
            done=True


        image=cv2.resize(image , (self.width,self.height))
        if self.ch==1:
            image=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        if not done:
            self.action(action)

        return image,reward,done,None

    def reset(self,isfirst):
        self.frame_count=0
        if isfirst:
            return
        else:
            self.GameOverAction()

    def GameOverAction(self):
      self.press_cursor([])
      pyautogui.keyUp('z')
      self.libc.capture_foreground(self.i_arr_c)
      image=np.ctypeslib.as_array(self.i_arr_c).reshape(448,384,3)
      image=cv2.flip(image,0)
      if (image[251,203]==[87,87,174]).all() and (image[237,177]==[90,90,179]).all() and (image[249,187]==[93,93,185]).all():
          self.KeyPress('down',3,0.1,0)
      if (image[280 ,348]==[187,187,187]).all() and (image[225,357]==[33,41,45]).all():
          pass
      else:
          self.KeyPress('z',3,0.2,0.5)
      self.KeyPress('esc',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1)
      self.KeyPress('right',0,0.1,0.5)
      self.KeyPress('z',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1.5)
      self.KeyPress('z',0,0.2,1.5)

    def KeyPress(self,input_key,in_sleep,throw_sleep,out_sleep):
        time.sleep(in_sleep)
        pyautogui.keyDown(input_key)
        time.sleep(throw_sleep)
        pyautogui.keyUp(input_key)
        time.sleep(out_sleep)
