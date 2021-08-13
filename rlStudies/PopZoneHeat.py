from gym import Env
from gym.spaces import Discrete, Box
import random
import numpy as np


class PopHeatEnv(Env):
    """

    Observation:
        Type: Box(2)
        Num	Observation                 Min         Max
        0	People in zone               0            100
        1	heat                        0            5000 (W)
            ...                         ...          ....

    Actions:
        Type: Discrete(3)
        Num	Action
        0	do Nothing
        1	decrement in 1
        2   increment in 1

    Reward:
        Reward is 1 if heat is between certain values
        # TODO FIXE THESE VALUES

    Starting State:
        First observation in simulation:
        - population is given by me: 35 p
        - heat is given by the simulation

    Episode Termination:
        This is a "real time" simulation
        episode lengnt (steps) reaches one day
        data will be updated every minute?
        Solved Requirements
            Considered solved when the average reward is greater than or equal to 195.0 over 100 consecutive trials.
    """

    def __init__(self):
        # Actions we can take, down, stay, up
        # 0 no hago nada 1 decremento 2 aumento
        self.action_space = Discrete(3)
        # mis observaciones tienen dos domensiones y aquí establezco máximo y mimnimo
        self.observation_space = Box(low=np.array([0,0,0]), high=np.array([100,5000,70]))
        self.reward = 0

    def set_obs(self, npop, heat, temp):
        self.state = np.array([npop + random.randint(-3, 3), heat, temp])
        obs = (npop + random.randint(-3, 3), heat, temp)
        return obs


    def apply_action(self, action):
        # Apply action
        # 0 -1 = -1 temperature
        # 1 -1 = 0
        # 2 -1 = 1 temperature
        self.state[0] = self.state[0] + action - 1 # el nuevo state es el resultado de la acción
        # Reduce shower length by 1 second

        # Calculate reward
        # condición dependiente del calor desprendido, por ejemplo
        return self.state[0]

    def get_reward(self,people_heat):
        if 10000 >= people_heat >= 11000:
            self.reward += 1
        else:
            self.reward -= 1

        # Apply temperature noise
        # self.state += random.randint(-1,1)
        # Set placeholder for info
        info = {}
        done = False
        if people_heat == 1000:
            done = True

        # Return step information
        return self.reward, done, info

    def render(self):
        # Implement viz
        pass

    def reset(self):
        # Reset shower temperature
        # Reset shower time
        self.reward = 0
        return self.reward