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



sensors = \
    [{"variable_name" : u"Site Direct Solar Radiation Rate per Area","variable_key":u"ENVIRONMENT","name": "solar_sensor"},
     {"variable_name": "Zone People Occupant Count","variable_key": "West Zone", "name": "people_sensor" },
    {"variable_name": "Zone People Total Heating Rate","variable_key": "West Zone", "name": "people_heat_sensor" }
           ]

actuators =[{"component_type":"People",
             "control_type": "Number of People",
             "actuator_key":"WEST ZONE PEOPLE",
             "name":"people_actuator" }]


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
        self.EpisodeStats = namedtuple("Stats", ["episode_lengths", "episode_rewards", "people_sensor", "people_heat_sensor"])


    def _discretize(self, obs):
        c = decimal.Decimal(obs)
        return float(round(c, 0))

    def init_stats(self):
        # Keeps track of useful statistics
        stats = self.EpisodeStats(
            episode_lengths=list(),
            episode_rewards=list(),
            people_sensor=list(),
            people_heat_sensor=list()
        )
        return stats

    def update_stats(self, stats,observation_dict):
        stats.people_sensor.append(observation_dict["people_sensor"])
        stats.people_heat_sensor.append(observation_dict["people_heat_sensor"])
        return stats

    def update_simulation_stats(self,simulation_stats, stats):
        simulation_stats.episode_lengths.extend(stats.episode_lengths)
        simulation_stats.episode_rewards.extend(stats.episode_rewards)
        simulation_stats.people_sensor.append(stats.people_sensor)
        simulation_stats.people_heat_sensor.append(stats.people_heat_sensor)

    def set_obs(self, obs_dictionary):

        # discretizo las observaciones hasta quitarles decimales
        # TODO parece que este cambio da igual.. ahora todo funciona y no sé porqué
        # TODO culpa del cache? culpa de las variables globales?
        # self.state = np.array([npop, float(round(heat)), float(round(temp))])
        obs_discrete = [self._discretize(obs) for k, obs in obs_dictionary.items()]
        self.state = np.array(obs_discrete)
        obs = tuple(obs_discrete)
        return obs


    def apply_action(self, observation, action):
        # Apply action
        # 0 -1 = -1 temperature
        # 1 -1 = 0
        # 2 -1 = 1 temperature

        new_value = observation["people_sensor"] + action - 1  # el nuevo state es el resultado de la acción
        # Reduce people number length by 1 second
        # Calculate reward
        # condición dependiente del calor desprendido, por ejemplo
        return new_value

    def get_reward(self,observation):
        people_heat = observation["people_heat_sensor"]
        if  80000<= people_heat <= 10000:
            self.reward = 50
            self.n_done += 1
        elif people_heat < 0:
            self.reward = -1000
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
    plt.plot(np.array(stats.people_sensor))
    people_smoothed = pd.Series(np.array(stats.people_sensor)).rolling(smoothing_window,
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
    plt.plot(np.array(stats.people_heat_sensor))
    peopleheat_smoothed = pd.Series(np.array(stats.people_heat_sensor)).rolling(smoothing_window,
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