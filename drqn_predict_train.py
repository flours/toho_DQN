import numpy as np
import keras
import cv2

from keras.layers.convolutional import Conv2D
from keras.optimizers import Adam
from keras.layers import Dense, Flatten, LSTM, TimeDistributed,Input,MaxPooling2D,GlobalAveragePooling2D,BatchNormalization,Activation,Add
from keras.optimizers import RMSprop
from keras.models import Sequential,Model
from keras.utils import Sequence



class MyGenerator(Sequence):
    """Custom generator"""

    def __init__(self, data_path='data/output_integrated.avi', target_path='data/keys_integrated.txt',
                 batch_size=1, width=84, height=84, ch=3,frame_size=10):
        """construction

        :param data_paths: List of image file
        :param data_classes: List of class
        :param batch_size: Batch size
        :param width: Image width
        :param height: Image height
        :param ch: Num of image channels
        :param num_of_class: Num of classes
        """
        self.frame_size=frame_size
        self.data_path = data_path
        self.target_path = target_path
        self.cap=cv2.VideoCapture(data_path)
        self.length = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)//frame_size
        self.batch_size = batch_size
        self.width = width
        self.height = height
        self.ch = ch
        self.num_batches_per_epoch = int((self.length - 1) / batch_size) + 1
        self.keys_word=['SHIFT','left','right','up','down','Z','X']
        self.f=open(target_path)
        self.lines=self.f.readlines()
    def _cursorkey2direction(self,keys):
        keys*=[0,1,1,1,1,0,0]
        if keys[1]==1 and keys [2]==1:
            keys[1]=0
            keys[2]=0
        if keys[3]==1 and keys [4]==1:
            keys[3]=0
            keys[4]=0
        ret_value=[0,0,0,0,0,0,0,0,0]
        ret_value[0]=keys[1]
        ret_value[1]=keys[2]
        ret_value[2]=keys[3]
        ret_value[3]=keys[4]
        if ret_value[0]==1 and ret_value[2]==1:
            ret_value[0]=0
            ret_value[2]=0
            ret_value[4]=1
        if ret_value[0]==1 and ret_value[3]==1:
            ret_value[0]=0
            ret_value[2]=0
            ret_value[5]=1
        if ret_value[1]==1 and ret_value[2]==1:
            ret_value[1]=0
            ret_value[2]=0
            ret_value[6]=1
        if ret_value[1]==1 and ret_value[3]==1:
            ret_value[1]=0
            ret_value[3]=0
            ret_value[7]=1

        if ret_value==[0,0,0,0,0,0,0,0,0]:
            ret_value[4]=1
        return np.array(ret_value)



    def __getitem__(self, idx):
        """Get batch data

        :param idx: Index of batch

        :return imgs: numpy array of images
        :return labels: numpy array of label
        """

        start_pos = self.batch_size * idx*self.frame_size
        end_pos = start_pos + self.batch_size*self.frame_size

        data,target=np.empty((0,self.width,self.height,self.ch),int),np.empty((7),int)

        res=self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

        for i in range(int(start_pos),int(end_pos),1):
            isread,frame=self.cap.read()
            if isread==False:
                break
            frame=cv2.resize(frame , (self.width,self.height))
            if self.ch==1:
                frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

            data=np.append(data,[frame.reshape(self.width,self.height,self.ch)],axis=0)

            line=self.lines[i]
            key=np.array([0,0,0,0,0,0,0])

            for i,k in enumerate(self.keys_word):
                if k in line:
                    key[i]=1
            t1=self._cursorkey2direction(key)
            t2=np.array([key[5],1-key[5]])
            target=key

        data=data.reshape(self.batch_size,self.frame_size,self.height,self.width,self.ch)
        t1=t1.reshape(self.batch_size,9)
        t2=t2.reshape(self.batch_size,2)
        return data,[t1,t2]

    def __len__(self):
        """Batch length"""

        return self.num_batches_per_epoch


    def on_epoch_end(self):
        """Task when end of epoch"""
        pass







def build_model():
    action_size=7
    model = Sequential()
    model.add(TimeDistributed(Conv2D(32, (4, 4), strides=(2, 2), activation='relu'),
                              input_shape=(10, 84, 84, 1)))
                              #input_shape=(time_step, row, col, channels)
    model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(2, 2), activation='relu')))
    model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(2, 2), activation='relu')))
    model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(1, 1), activation='relu')))
    model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(1, 1), activation='relu')))
    model.add(TimeDistributed(Conv2D(64, (3, 3), strides=(1, 1), activation='relu')))
    model.add(TimeDistributed(Flatten()))
    model.add(LSTM(512))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(action_size))
    model.summary()
    return model


def build_model2(width=84,height=84):
    action_size=[9,2]
    input=Input(shape=(10,width,height,1))
    x=TimeDistributed(Conv2D(32, (8, 8), strides=(4, 4), activation='relu'))(input)
    x=TimeDistributed(Conv2D(64, (4, 4), strides=(2, 2), activation='relu'))(x)
    x=TimeDistributed(Conv2D(64, (3, 3), strides=(1, 1), activation='relu'))(x)
    x=TimeDistributed(Flatten())(x)
    x=LSTM(512)(x)
    x=Dense(128, activation='relu')(x)
    out1=Dense(action_size[0],name='out1',activation='softmax')(x)
    out2=Dense(action_size[1],name='out2',activation='softmax')(x)
    model = Model(inputs=input, outputs=[out1,out2])
    model.summary()
    return model

def build_model3(width=84,height=84):
    action_size=[9,2]
    input=Input(shape=(10,width,height,1))
    x=TimeDistributed(Conv2D(32, (4, 4), strides=(2, 2), activation='relu'))(input)
    x=TimeDistributed(Conv2D(32, (4, 4), strides=(2, 2), activation='relu'))(x)
    x=TimeDistributed(Conv2D(64, (4, 4), strides=(2, 2), activation='relu'))(x)
    x=TimeDistributed(Conv2D(128, (3, 3), strides=(1, 1), activation='relu'))(x)
    x=TimeDistributed(Conv2D(128, (3, 3), strides=(1, 1), activation='relu'))(x)
    x=TimeDistributed(Flatten())(x)
    x=LSTM(512)(x)
    x=Dense(128, activation='relu')(x)
    out1=Dense(action_size[0],name='out1',activation='softmax')(x)
    out2=Dense(action_size[1],name='out2',activation='softmax')(x)
    model = Model(inputs=input, outputs=[out1,out2])
    model.summary()
    return model



def resblock(input,ch1,strides=2):
    x = TimeDistributed(BatchNormalization())(input)
    x = TimeDistributed(Activation("relu"))(x)
    x=TimeDistributed(Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same'))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Activation("relu"))(x)
    x=TimeDistributed(Conv2D(ch1, (3, 3), strides=(1, 1),padding='same'))(x)
    if not x.shape==input.shape:
        input=TimeDistributed(Conv2D(ch1, (3, 3), strides=(strides, strides),padding='same'))(input)
    return Add()([input, x])

def build_model4(width=84,height=84):
    action_size=[9,2]
    input=Input(shape=(10,width,height,1))

    x=TimeDistributed(Conv2D(64, (6, 6), strides=(2, 2), activation='relu'))(input)
    x=TimeDistributed(MaxPooling2D(2))(x)

    x=resblock(x,64)
    x=resblock(x,128)
    x=resblock(x,256)
    x=resblock(x,512)
    x=TimeDistributed(GlobalAveragePooling2D())(x)
    x=TimeDistributed(Flatten())(x)
    x=LSTM(512)(x)
    x=Dense(128, activation='relu')(x)
    out1=Dense(action_size[0],name='out1',activation='softmax')(x)
    out2=Dense(action_size[1],name='out2',activation='softmax')(x)
    model = Model(inputs=input, outputs=[out1,out2])
    model.summary()
    return model

model=build_model4(84,84)
optimizer=Adam(lr=0.001)
model.compile(loss="categorical_crossentropy", optimizer=optimizer)

#model.load_weights("param.hdf5")


# cap=cv2.VideoCapture('data/output1567755746.0803812.avi')
# data,target=np.empty((0,84,84),int),np.empty((0,7),int)
#
# f=open('data/keys1567755746.0803812.txt')
# lines=f.readlines()
# count=0
# keys_word=['SHIFT','left','right','up','down','Z','X']
# while True:
#     isread,frame=cap.read()
#     if isread==False:
#         break
#     frame=cv2.resize(frame , (84,84))
#     gray_img=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
#     line=lines[count]
#
#     data=np.append(data,[gray_img],axis=0)
#     np.array(data)
#     key=np.array([0,0,0,0,0,0,0])
#     for i,k in enumerate(keys_word):
#         if line in k:
#             key[i]=1
#     target=np.append(target,[key],axis=0)
#     count+=1
#     if count%10==0:
#         print(count)
#     if count%10000==0:
#         break

#print(target.shape,data.shape)
#data=np.array(data).reshape(len(data)//10,10,84,84,1)
#target=np.array(target)[::10,:].reshape(len(target)//10,7)

train_gen=MyGenerator(width=84,height=84,ch=1)

model.fit_generator(train_gen,
           steps_per_epoch=train_gen.num_batches_per_epoch,
           epochs=20,
           verbose=1,
           shuffle=True)

model.save_weights('param.hdf5')
#model.fit(data, target,batch_size=300,epochs=100,validation_split=0.1)
