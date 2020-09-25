# -*- coding: utf-8 -*-

import numpy as np
import gym
import random

from collections import deque
from keras.layers import Dense, Flatten, LSTM, TimeDistributed,Input,MaxPooling2D,GlobalAveragePooling2D,BatchNormalization,Activation,Add
from keras.layers.convolutional import Conv2D
from keras.models import Model
from keras import backend as K
import os
import cv2
from skimage.color import rgb2gray
from skimage.transform import resize
# rmsprop
import keras
from toho_env import toho_env#import __init__

np.set_printoptions(suppress=True)

resize_x = 84
resize_y = 84

file_history = open("history.txt", "w")
file_history.close()


class Agent:
    def __init__(self, env):
        self.env = env
#        self.input_dim = env.observation_space.shape
#        self.output_dim = env.action_space.n

        self.q_network = self.build_model3()
        self.t_network = self.build_model3()

        self.t_network.load_weights("save_model/breakout_drqn15.h51579291010.0132682episode3000") # 初期の重みを考慮する場合
        self.q_network.summary()
        self.max_q = 0
    def load(self,num):
        files=os.listdir('save_model')
        file_name=''
        for file in files:
            if file.endswith('episode'+str(num)):
                file_name=file
        self.t_network.load_weights('save_model/'+file_name) # 初期の重みを考慮する場合


    def ModelCreate(self):
        ip = Input(shape=(resize_y, resize_x, 1))
        h = Conv2D(32, (4,4),strides=(2,2),padding="same",activation='relu')(ip)
        h = Conv2D(64,(4,4),strides=(4,4),padding="same",activation='relu')(h)
        h = Conv2D(64,(3,3),strides=(3,3),padding="same",activation='relu')(h)
        h = Flatten()(h)
        h = Dense(512, activation='relu')(h)
        h = Dense(self.output_dim)(h)
        model = Model(ip, output=h)

        rmsprop = keras.optimizers.RMSprop(lr=0.00025, rho=0.95, epsilon=0.01, decay=0.0)
        model.compile(rmsprop, 'mse')
        return model

    def resblock(self,input,ch1,strides=2):
        x = TimeDistributed(BatchNormalization())(input)
        x = TimeDistributed(Activation("relu"))(x)
        x=TimeDistributed(Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same'))(x)
        x = TimeDistributed(BatchNormalization())(x)
        x = TimeDistributed(Activation("relu"))(x)
        x=TimeDistributed(Conv2D(ch1, (3, 3), strides=(1, 1),padding='same'))(x)
        if not x.shape==input.shape:
            input=TimeDistributed(Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same'))(input)
        return Add()([input, x])

    def build_model2(self,width=84,height=84,ch=1):
        action_size=[9,2]
        input=Input(shape=(4,width,height,ch))

        x=TimeDistributed(Conv2D(64, (6, 6), strides=(2, 2), activation='relu'))(input)

        x=self.resblock(x,64)
        x=self.resblock(x,128)
        x=self.resblock(x,256)
        x=TimeDistributed(GlobalAveragePooling2D())(x)
        x=TimeDistributed(Flatten())(x)
        x=Flatten()(x)
#        x=LSTM(512)(x)
        x=Dense(128, activation='relu')(x)
        out1=Dense(action_size[0],name='out1')(x)
        model = Model(inputs=input, outputs=out1)
        rmsprop = keras.optimizers.RMSprop(lr=0.00025, rho=0.95, epsilon=0.01, decay=0.0)
        model.compile(rmsprop, 'mse')
        model.summary()
        return model
    def resblock2(self,input,ch1,strides=2):
        x = BatchNormalization()(input)
        x = Activation("relu")(x)
        x=Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same')(x)
        x = BatchNormalization()(x)
        x = Activation("relu")(x)
        x=  Conv2D(ch1, (3, 3), strides=(1, 1),padding='same')(x)
        if not x.shape==input.shape:
            input=Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same')(input)
        return Add()([input, x])

    def build_model3(self,width=84,height=84,ch=4):
        action_size=[9,2]
        input=Input(shape=(width,height,4))

        x=Conv2D(64, (6, 6), strides=(2, 2), activation='relu')(input)
        x=MaxPooling2D(2)(x)

        x=self.resblock2(x,64)
        x=self.resblock2(x,128)
        x=self.resblock2(x,256)
        x=GlobalAveragePooling2D()(x)
        x=Dense(128, activation='relu')(x)
        out1=Dense(action_size[0],name='out1')(x)
        out2=Dense(action_size[1],name='out2')(x)
        model = Model(inputs=input, outputs=[out1,out2])
        model.summary()
        return model


    def getAction(self, state, epsilon):
        # epsilon-greedy
        if np.random.rand() < epsilon:
            return 4#self.env.action_space.sample()

        state = state[np.newaxis,:,:,:]
        #q_value = self.Predict(state)
        q_value = self.q_network.predict_on_batch(state)
        return np.argmax(q_value[0])


    def Predict(self, x_batch):
        return self.t_network.predict_on_batch(x_batch)


def Preprocess(image, _resize_x=resize_x, _resize_y=resize_y):
    gray_image = rgb2gray(image)
    gray_image = resize(gray_image, (_resize_x, _resize_y))
    return gray_image[:,:,np.newaxis]

def main():

#    env_name = 'myenv-v0'


    env = toho_env()
    agent = Agent(env)

    for i in range(48):
        agent.load(i*100)
        replay_memory = deque()

        epsilon=0.05

        end_flag=False

        state,_,_,_ = env.step([4,0])
        state = Preprocess(state, resize_x, resize_y)
        state=np.stack(( state, state, state,state ), axis=0)
        state=np.reshape([state],(84,84,4))

        while not end_flag:
            action = agent.getAction(state,epsilon)
            end_flag=False
            state2=[]
            for i in range(4):
                tmp, reward, end_flag, info = env.step([action,0])
                tmp = Preprocess(tmp, resize_x, resize_y)
                state2.append(tmp)
            print(env.get_score())
            reward*=10
            reward+=0.1

            # 前処理
            state2=np.array(state2)
            state2 = state2.reshape(84, 84, 4 )
    #        img=env.render('human')
    #        cv2.imshow("a",state2[3])
    #        cv2.waitKey(1)
            state = state2
        env.reset(False)



if __name__ == '__main__':
    main()
