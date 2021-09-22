from gym import Env
from gym.spaces import Discrete, Box
import random
import numpy as np
import decimal
import matplotlib
import numpy as np
import pandas as pd
from collections import namedtuple
from matplotlib import pyplot as plt


def discretize(obs):
    c = decimal.Decimal(obs)
    return float(round(c, 0))




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
        self.observation_space = Box(low=np.array([0,0,0]), high=np.array([100,15000,1000]), dtype=np.float32)
        self.reward = 0

    def set_obs(self, npop, heat, temp):

        # discretizo las observaciones hasta quitarles decimales
        # TODO parece que este cambio da igual.. ahora todo funciona y no sé porqué
        # TODO culpa del cache? culpa de las variables globales?
        # self.state = np.array([npop, float(round(heat)), float(round(temp))])
        self.state = np.array([discretize(npop), discretize(heat), discretize(temp)])
        obs = (npop, heat, temp)
        return obs


    def apply_action(self, action):
        # Apply action
        # 0 -1 = -1 temperature
        # 1 -1 = 0
        # 2 -1 = 1 temperature
        self.state[0] = self.state[0] + action - 1 # el nuevo state es el resultado de la acción
        # Reduce people number length by 1 second

        # Calculate reward
        # condición dependiente del calor desprendido, por ejemplo
        return self.state[0]

    def get_reward(self,people_heat):
        if 10000 <= people_heat <= 12000:
            self.reward = 50
            self.n_done += 1
        elif people_heat < 0:
            self.reward = -100
        else:
            self.reward = -1


        # Apply temperature noise
        # self.state += random.randint(-1,1)
        # Set placeholder for info
        info = {}
        done = False
        if self.n_done == 5:
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
        self.n_done = 0
        return self.reward



def plot_episode_stats(stats, smoothing_window=500, noshow=False):
    # Plot the episode length over time
    fig1 = plt.figure(figsize=(10,5))
    plt.plot(stats.episode_lengths)
    plt.xlabel("Episode")
    plt.ylabel("Episode Length")
    plt.title("Episode Length over Time")
    if noshow:
        plt.close(fig1)
    else:
        # plt.show(fig1)
        fig1.show()

    # Plot the episode reward over time
    fig2 = plt.figure(figsize=(10,5))
    rewards_smoothed = pd.Series(np.array(stats.episode_rewards)).rolling(smoothing_window, min_periods=smoothing_window).mean()
    plt.plot(rewards_smoothed)
    plt.xlabel("Episode")
    plt.ylabel("Episode Reward (Smoothed)")
    plt.title("Episode Reward over Time (Smoothed over window size {})".format(smoothing_window))
    if noshow:
        plt.close(fig2)
    else:
        # plt.show(fig2)
        fig2.show()

    # Plot time steps and episode number
    fig3 = plt.figure(figsize=(10,5))
    plt.plot(np.cumsum(np.array(stats.episode_lengths)), np.arange(len(stats.episode_lengths)))
    plt.xlabel("Time Steps")
    plt.ylabel("Episode")
    plt.title("Episode per time step")
    if noshow:
        plt.close(fig3)
    else:
        # plt.show(fig3)
        fig3.show()

        # Plot the episode reward over time
    fig4 = plt.figure(figsize=(10, 5))
    plt.plot(np.array(stats.people))
    people_smoothed = pd.Series(np.array(stats.people)).rolling(smoothing_window,
                                                                          min_periods=smoothing_window).mean()
    plt.plot(people_smoothed)
    plt.xlabel("steps")
    plt.ylabel("people")
    plt.title("people Length over Time (Smoothed over window size {})".format(smoothing_window))
    if noshow:
        plt.close(fig4)
    else:
        # plt.show(fig2)
        fig4.show()

    fig5 = plt.figure(figsize=(10, 5))
    plt.plot(np.array(stats.peopleheat))
    peopleheat_smoothed = pd.Series(np.array(stats.peopleheat)).rolling(smoothing_window,
                                                                min_periods=smoothing_window).mean()
    plt.plot(peopleheat_smoothed)
    plt.xlabel("steps")
    plt.ylabel("people heat (Smoothed over window size {})".format(smoothing_window))
    plt.title("people heat over Time")
    if noshow:
        plt.close(fig5)
    else:
        # plt.show(fig2)
        fig5.show()


    return fig1, fig2, fig3, fig4, fig5