from keras.models import Sequential
from keras.layers import Dense


class Brain:
    def __init__(self):
        self.model = Sequential()
        self.model.add(Dense(8, input_dim=4, activation='relu'))
        self.model.add(Dense(3, activation='softmax'))
