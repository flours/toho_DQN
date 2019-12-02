#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 28 2018

@author: Sooyoung Moon

atari breakout drqn
"""
import numpy as np
import keras
import cv2

from keras.layers.convolutional import Conv2D
from keras.optimizers import Adam
from keras.layers import Dense, Flatten, LSTM, TimeDistributed,Input,MaxPooling2D,GlobalAveragePooling2D,BatchNormalization,Activation,Add
from keras.optimizers import RMSprop,Adam
from keras.models import Sequential,Model
from keras.utils import Sequence
from keras.layers import Dense, Flatten, LSTM, TimeDistributed

from keras.optimizers import RMSprop

from keras.models import Sequential

from skimage.transform import resize

from skimage.color import rgb2gray

from collections import deque

from keras import backend as K

import tensorflow as tf

import numpy as np

import random

from toho_env import toho_env

#from keras.utils.training_utils import multi_gpu_model



EPISODES = 50000


# 브레이크아웃에서의 DRQN 에이전트

class DRQNAgent:

    def __init__(self, action_size):

        self.render = False

        self.load_model = False
        # 행동의 크기 정의

        self.action_size = action_size
        self.max_memory = 20000
        # DRQN 하이퍼파라미터

        self.epsilon = 1.

        self.epsilon_start, self.epsilon_end = 1.0, 0.1

        self.exploration_steps = 100000.

        self.epsilon_decay_step = (self.epsilon_start - self.epsilon_end) \
                                            / self.exploration_steps

        self.batch_size = 32

        self.train_start = 50000#50000

        self.update_target_rate = 1000

        self.discount_factor = 0.9

        # 리플레이 메모리, 최대 크기 400000

        self.memory = deque(maxlen=400000)

        self.no_op_steps = 20

        # 모델과 타겟모델을 생성하고 타겟모델 초기화 및 gpu에 모델 할당

        self.model = self.build_model3()
        #self.model = multi_gpu_model(self.model, gpus = 4)
        self.target_model = self.build_model3()
        #self.target_model = multi_gpu_model(self.target_model, gpus = 4)

        self.update_target_model()

        self.optimizer = self.optimizer()



        # 텐서보드 설정

        self.sess = tf.InteractiveSession()

        K.set_session(self.sess)


        self.avg_q_max, self.avg_loss = 0, 0

        self.summary_placeholders, self.update_ops, self.summary_op = self.setup_summary()

        self.summary_writer = tf.summary.FileWriter(

            'summary/breakout_drqn15', self.sess.graph)

        self.sess.run(tf.global_variables_initializer())



        if self.load_model:

            self.model.load_weights("./save_model/breakout_drqn15.h51572405568.9825697")



    # 샘플 <s, a, r, s'>을 리플레이 메모리에 저장

    def append_sample(self, history, action, reward, next_history, dead):

        self.memory.append((history, action, reward, next_history, dead))
        if len(self.memory)>self.max_memory:
            self.memory.popleft



    # Huber Loss를 이용하기 위해 최적화 함수를 직접 정의

    def optimizer(self):

        a = K.placeholder(shape=(None,), dtype='int32')
        a2 = K.placeholder(shape=(None,), dtype='int32')

        y = K.placeholder(shape=(None,), dtype='float32')

        prediction = self.model.output

        a_one_hot = K.one_hot(a, self.action_size[0])

        q_value = K.sum(prediction[0] * a_one_hot, axis=1)

        a2_one_hot = K.one_hot(a2, self.action_size[1])

        q2_value = K.sum(prediction[1] * a2_one_hot, axis=1)

        error = K.abs(y - q_value)
        error2 = K.abs(y - q2_value)



        quadratic_part = K.clip(error, 0.0, 1.0)
        quadratic_part2 = K.clip(error2, 0.0, 1.0)

        linear_part = error - quadratic_part
        linear_part2 = error2 - quadratic_part2

        loss = K.mean(0.5 * K.square(quadratic_part) + linear_part)
        loss2 = K.mean(0.5 * K.square(quadratic_part2) + linear_part2)


        optimizer = Adam(lr=0.00025, epsilon=0.01)

        updates = optimizer.get_updates(self.model.trainable_weights, [],    [loss,loss2])
        train = K.function([self.model.input, a,a2, y], [loss,loss2], updates=updates)

        return train



    # 상태가 입력, 큐함수가 출력인 인공신경망 생성

    def build_model(self):

        model = Sequential()

        model.add(TimeDistributed(Conv2D(32, (8, 8), strides=(4, 4), activation='relu'),

                                  input_shape=(10, 84, 84, 1)))

                                  #input_shape=(time_step, row, col, channels)

        model.add(TimeDistributed(Conv2D(64, (4, 4), strides=(2, 2), activation='relu')))

        model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(1, 1), activation='relu')))

        model.add(TimeDistributed(Flatten()))

        model.add(LSTM(512))

        model.add(Dense(128, activation='relu'))

        model.add(Dense(self.action_size))

        model.summary()

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

    def build_model2(self,width=84,height=84,ch=3):
        action_size=[9,2]
        input=Input(shape=(4,width,height,ch))

        x=TimeDistributed(Conv2D(64, (6, 6), strides=(2, 2), activation='relu'))(input)
        x=TimeDistributed(MaxPooling2D(2))(x)

        x=self.resblock(x,64)
        x=self.resblock(x,128)
        x=self.resblock(x,256)
        x=self.resblock(x,512)
        x=TimeDistributed(GlobalAveragePooling2D())(x)
        x=TimeDistributed(Flatten())(x)
        x=Flatten()(x)
        x=Dense(128, activation='relu')(x)
        out1=Dense(action_size[0],name='out1')(x)
        out2=Dense(action_size[1],name='out2')(x)
        model = Model(inputs=input, outputs=[out1,out2])
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







    # 타겟 모델을 모델의 가중치로 업데이트

    def update_target_model(self):

        self.target_model.set_weights(self.model.get_weights())



    # 입실론 탐욕 정책으로 행동 선택

    def get_action(self, history):

        history = np.float32(history / 255.0)

        if np.random.rand() <= self.epsilon:

            return random.randrange(self.action_size[0]),random.randrange(self.action_size[1])

        else:

            q_value = self.model.predict(history)
            print(q_value)

            return np.argmax(q_value[0]),np.argmax(q_value[1])



    # 리플레이 메모리에서 무작위로 추출한 배치로 모델 학습

    def train_model(self):
        if self.epsilon > self.epsilon_end:

            self.epsilon -= self.epsilon_decay_step



        mini_batch = random.sample(self.memory, self.batch_size)

        history = np.zeros((self.batch_size,  84, 84, 4))

        next_history = np.zeros((self.batch_size,  84, 84, 4))

        target = np.zeros((self.batch_size,))

        action, reward, dead = [], [], []



        for i in range(self.batch_size):

            history[i] = np.int32(mini_batch[i][0])

            next_history[i] = np.int32(mini_batch[i][3])

            action.append(mini_batch[i][1])

            reward.append(mini_batch[i][2])

            dead.append(mini_batch[i][4])



        target_value = self.target_model.predict(next_history)



        for i in range(self.batch_size):

            if dead[i]:

                target[i] = reward[i]

            else:
                target[i] = reward[i] + self.discount_factor * np.amax(target_value[0][i])


        loss = self.optimizer([history, [action[0][0]],[action[0][1]], target])
        self.avg_loss += loss[0]



    # 각 에피소드 당 학습 정보를 기록

    def setup_summary(self):

        episode_total_reward = tf.Variable(0.)

        episode_avg_max_q = tf.Variable(0.)

        episode_duration = tf.Variable(0.)

        episode_avg_loss = tf.Variable(0.)



        tf.summary.scalar('Total_Reward/Episode', episode_total_reward)

        tf.summary.scalar('Average_Max_Q/Episode', episode_avg_max_q)

        tf.summary.scalar('Duration/Episode', episode_duration)

        tf.summary.scalar('Average_Loss/Episode', episode_avg_loss)



        summary_vars = [episode_total_reward, episode_avg_max_q,

                        episode_duration, episode_avg_loss]

        summary_placeholders = [tf.placeholder(tf.float32) for _ in

                                range(len(summary_vars))]

        update_ops = [summary_vars[i].assign(summary_placeholders[i]) for i in

                      range(len(summary_vars))]


        summary_op = tf.summary.merge_all()

        return summary_placeholders, update_ops, summary_op





# 학습속도를 높이기 위해 흑백화면으로 전처리

def pre_processing(observe):


    #processed_observe = np.uint8(
    #    resize(rgb2gray(observe), ( 84, 84 ), mode='constant') * 255)

    return observe





if __name__ == "__main__":

    # 환경과 DRQN 에이전트 생성

    env = toho_env(ch=1)

    agent = DRQNAgent(action_size=[9,2])



    scores, episodes, global_step = [], [], 0


    isfirst=True
    for e in range(EPISODES):

        done = False

        dead = False



        step, score, start_life = 0, 0, 5

        observe = env.reset(isfirst)
        isfirst=False



        for _ in range(random.randint( 1, agent.no_op_steps )):

            observe, _, _, _ = env.step2([4,1] )




        state = pre_processing(observe)

        state = state.reshape( 84, 84, 1 )

        history = np.stack(( state, state, state, state ), axis=0)
                    #( 10, 84, 84, 1 )

        history = np.reshape([history], ( 1, 84, 84, 4 ))


        train_num=0
        while not done:

            if agent.render:

                env.render()

            global_step += 1

            step += 1


            # 바로 전 4개의 상태로 행동을 선택

            action = agent.get_action(history)
            print(action)



            # 1: 정지, 2: 왼쪽, 3: 오른쪽




            # 선택한 행동으로 환경에서 한 타임스텝 진행

            observe, reward, done, info = env.step2(action)

            #reward = reward * 10

            # 각 타임스텝마다 상태 전처리

            next_state = pre_processing(observe)

            next_state = next_state.reshape( 84, 84, 1 )

            next_history = next_state.reshape( 1, 84, 84, 1 )
            print(history[:,:,:,:3].shape,next_history.shape)

            next_history = np.append(next_history, history[:, :, :, :3], axis=3)

            next_history = np.reshape([next_history],( 1, 84, 84, 4 ))


            agent.avg_q_max += np.amax(
                           agent.model.predict(np.float32(history / 255.))[0])





            reward = np.clip( reward, -1., 1. )


            # 샘플 <s, a, r, s'>을 저장

            agent.append_sample( history, action, reward, next_history, dead )



            if len(agent.memory) >= 100:#agent.train_start:
                train_num+=1




            # 일정 시간마다 타겟모델을 모델의 가중치로 업데이트

            if global_step % agent.update_target_rate == 0:
                agent.update_target_model()




            score += reward



            if dead:

                dead = False

            else:

                history = next_history



            if done:

                print(score)

                # 각 에피소드 당 학습 정보를 기록
                for i in range(train_num):
                    agent.train_model()

                if global_step > agent.train_start:

                    stats = [score, agent.avg_q_max / float(step), step,

                             agent.avg_loss / float(step)]

                    for i in range(len(stats)):

                        agent.sess.run(agent.update_ops[i], feed_dict={

                            agent.summary_placeholders[i]: float(stats[i])

                        })

                    summary_str = agent.sess.run(agent.summary_op)

                    agent.summary_writer.add_summary(summary_str, e + 1)



                print("episode:", e, "  score:", score, "  memory length:",

                      len(agent.memory), "  epsilon:", agent.epsilon,

                      "  global_step:", global_step, "  average_q:",

                      agent.avg_q_max / float(step), "  average loss:",

                      agent.avg_loss / float(step))



                agent.avg_q_max, agent.avg_loss = 0, 0

        # 1000 에피소드마다 모델 저장

        if e % 1000 == 0:
            import time
            now=time.time()

            agent.model.save_weights("./save_model/breakout_drqn15.h5"+str(now))
