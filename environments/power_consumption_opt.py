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

"""
From Paper
"""

"""

The state vector contains the following:
    –Outdoor air temperature between -20ªC and 50ªC 
    –West Zone air temperature between -20 C and 50ºC  <-- 
    –East Zone air temperature between -20ºC and 50ºC
    –Total electric demand power between 0W and 1GW <--
    –Non-HVAC electric demand power between 0W and 1GW <--
    –HVAC electric demand power between 0W and 1GW 
    PATA UN PRIMER ESTUDIO SOLO UTILIZARÉ TRES
"""

# Inizialize globals


####

# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf' # modified people wet zone at 35
# idffile = "/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/1ZoneUncontrolled_win_1.idf"
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/eplusout'

sensors = \
    [{"variable_name" : u"Zone Mean Air Temperature","variable_key":u"WEST ZONE","name": "WestZoneTemp"},
     {"variable_name": "Facility Total Building Electricity Demand Rate","variable_key": "Whole Building", "name": "IT_Equip_Power" },
    {"variable_name": "Facility Total Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_Building_Power" },
    {"variable_name": "Facility Total HVAC Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_HVAC_Power" }
           ]


# hay más actuadores pero voy a dejarlo así por ahora
# West Zone setpoint temperature between10ºC and 40ºC
# este actuator existe
actuators =[{"component_type":"System Node Setpoint",
             "control_type": "Temperature Setpoint",
             "actuator_key":"West Zone DEC Outlet Node",
             "name":"WestZoneDECOutletNode_setpoint" }]



class Power_Consumption_Op(Env):

    def __init__(self):
        self.action_space = Discrete(3)
        # West Zone air temperature between -20 C and 50ºC
        # Total electric demand power between 0W and 1GW
        # Non-HVAC electric demand power between 0W and 1GW
        # Todo debería pasarlo todo a medidas normalizadas entre -1 y 1
        self.observation_space = Box(low=np.array([-20,0,0]), high=np.array([50,1_000_000,1_000_000]), dtype=np.float32)
        self.reward = 0
        self.done = 0

    def _discretize(self,obs):
        c = decimal.Decimal(obs)
        return float(round(c, 0))

    def transform(self):
        '''
        hacer transformación dela observación a normalizados aquí
        :return:
        '''
        pass

    def set_obs(self, obs_dictionary):
        # WestZoneTemp, IT_Equip_Power, Whole_Building_Power
        # discretizo las observaciones hasta quitarles decimales

        obs_discrete = [self._discretize(obs) for k,obs in obs_dictionary.items()]
        self.state = np.array(obs_discrete)
        obs = tuple(obs_discrete)
        return obs

    def apply_action(self, action, actuator_value):
        # Apply action
        # 0 -1 = -1 temperature
        # 1 -1 = 0
        # 2 -1 = 1 temperature
        new_value = actuator_value + action - 1 # el nuevo state es el resultado de la acción
        # Reduce people number length by 1 second

        # Calculate reward
        # condición dependiente del calor desprendido, por ejemplo
        return new_value

    def get_reward(self,observation):
        # [{"variable_name": u"Zone Mean Air Temperature", "variable_key": u"WEST ZONE", "name": "WestZoneTemp,"},
        #  {"variable_name": "Facility Total Building Electricity Demand Rate", "variable_key": "Whole Building",
        #   "name": "IT_Equip_Power"},
        #  {"variable_name": "Facility Total Electricity Demand Rate", "variable_key": "Whole Building",
        #   "name": "Whole_Building_Power"},
        # TODO ver bien en paper
        # T^i_U= 24.0ªC,T^i_C= 23.5ºC,T^i_L= 23.0ºC,lambda_P=1/100000,lambda_1=0.5,lambda_2=0.1
        temp = observation["WestZoneTemp"]
        if temp > 25:
            r1 = -50

        else:
            r1 = 10
        power = observation["Whole_Building_Power"]
        if power > 130_000: # Power viene en W
            r2 = -100
        else:
            r2 = 10
        self.reward = r1+r2
        if self.reward == 20:
            self.done += 1

        # Set placeholder for info
        info = {}
        done = False
        if self.n_done == 5:
            done = True

        # Return step information
        return self.reward, done, info

    def reset(self):
        self.reward = 0
        self.n_done = 0
        return self.reward


def plot_power_opt_stats(stats, smoothing_window=500, noshow=False):
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
    plt.plot(np.array(stats.power_consumption))
    people_smoothed = pd.Series(np.array(stats.power_consumption)).rolling(smoothing_window,
                                                                          min_periods=smoothing_window).mean()
    plt.plot(people_smoothed)
    plt.xlabel("steps")
    plt.ylabel("power_consumption")
    plt.title("power_consumption over Time (Smoothed over window size {})".format(smoothing_window))
    if noshow:
        plt.close(fig4)
    else:
        # plt.show(fig2)
        fig4.show()

    fig5 = plt.figure(figsize=(10, 5))
    plt.plot(np.array(stats.Temperature))
    peopleheat_smoothed = pd.Series(np.array(stats.Temperature)).rolling(smoothing_window,
                                                                min_periods=smoothing_window).mean()
    plt.plot(peopleheat_smoothed)
    plt.xlabel("steps")
    plt.ylabel("Temperature (Smoothed over window size {})".format(smoothing_window))
    plt.title("Temperature over Time")
    if noshow:
        plt.close(fig5)
    else:
        # plt.show(fig2)
        fig5.show()


    return fig1, fig2, fig3, fig4, fig5