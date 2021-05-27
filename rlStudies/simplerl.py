from gym import Env
from gym.spaces import Discrete, Box
import numpy as np
import random
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam

'''
goal controlar mi variable : gente que hay dentro de la habitación entre un rango (imaginar que es un centro comercial)
Quiero que el número de gente esté entre 10 y 15

'''

class PopZoneEnv(Env):
    def __init__(self,npop):
        # Actions we can take, down, stay, up
        # 0 no hago nada 1 decremento 2 aumento
        self.action_space = Discrete(3)
        # Temperature array
        self.observation_space = Box(low=np.array([0]), high=np.array([100]))
        # gente que llega al principio más ruido
        # en realidad esto lo cogería de la misma simulación. puedo ponerle gente a esta variable
        # self.state = 38 + random.randint(-3, 3)
        self.state = npop + random.randint(-3, 3)
        # Set shower length
        # el tiempo que me voy a pasar regulando la entrada y salida de gente
        # en mi caso sería más bien los time steps???
        self.shower_length = 60

    def step(self, action):
        # Apply action
        # 0 -1 = -1 temperature
        # 1 -1 = 0
        # 2 -1 = 1 temperature
        self.state += action - 1 # el nuevo state es el resultado de la acción
        # Reduce shower length by 1 second
        self.shower_length -= 1 # time step menos 1

        # Calculate reward
        if self.state >= 20 and self.state <= 25:
            reward = 1
        else:
            reward = -1

            # Check if shower is done
        if self.shower_length <= 0:
            done = True
        else:
            done = False

        # Apply temperature noise
        # self.state += random.randint(-1,1)
        # Set placeholder for info
        info = {}

        # Return step information
        return self.state, reward, done, info

    def render(self):
        # Implement viz
        pass

    def reset(self):
        # Reset shower temperature
        self.state = 30 + random.randint(-3, 3) # esto lo haré haciendo el reseteo del actuator? vuelve a comenzar un episodio.. esto lo haré yo cada día
        # Reset shower time
        self.shower_length = 60
        return self.state

def applay_random_action(npop, episode):
    env = PopZoneEnv(npop)
    episodes = 20
    if episode< episodes:
        state = env.reset()
        done = False
        score = 0

        while not done:
            # env.render()
            action = env.action_space.sample()
            n_state, reward, done, info = env.step(action)
            score += reward
        episode = +1
        print('Episode:{} Score:{}'.format(episode, score))
        return float(n_state), episode


def build_model(states, actions):
    model = Sequential()
    model.add(Dense(24, activation='relu', input_shape=states))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(actions, activation='linear'))
    return model


def run_model(environment):
    env = environment()
    states = env.observation_space.shape
    actions = env.action_space.n
    model = build_model(states, actions)
    return model