import numpy as np
from keras.models import Sequential
from keras.layers import Dense


class Brain:
    def __init__(self):
        self.model = Sequential()
        self.model.add(Dense(8, input_dim=4, activation='relu'))
        self.model.add(Dense(3, activation='softmax'))

    def getWeights(self):
        return self.model.get_weights()

    def setWeights(self, weights):
        self.model.set_weights(weights)

    def indexMaxValue(self, arr: [float]) -> int:
        if len(arr) == 0:
            return -1

        maxVal = arr[0]
        maxIndex = 0

        for i in range(len(arr)):
            if arr[i] > maxVal:
                maxVal = arr[i]
                maxIndex = i

        return maxIndex

    def getArrayFromDict(self, collisionDict: {str: int}) -> [int]:
        ''' convert collision dict to an array of boolean '''
        res = list(collisionDict.values())
        for i in range(len(res)):
            res[i] = int(res[i])
        res = np.array(res)
        res = res.reshape(1, -1)

        return np.array(res)

    def makeDecision(self, collisions: [int]) -> int:
        ''' return a decision which is a number between 0 and 2 '''
        prediction = self.model(
            self.getArrayFromDict(collisions), training=False)
        prediction = np.array(prediction)
        prediction = np.squeeze(prediction)
        decision = self.indexMaxValue(prediction)

        return decision