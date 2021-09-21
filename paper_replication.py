import os
import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')
import numpy

from testing_random_decision import createEpsilonGreedyPolicy
from pyenergyplus.api import EnergyPlusAPI
import matplotlib.style
import numpy as np
from rlStudies.PopZoneHeat import PopHeatEnv
import helpers as plotting
from collections import defaultdict
from pathlib import Path
import pickle
from gym.spaces import Discrete, Box
from gym import Env
import decimal
from ep_helpers import create_sensors,create_actuators


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






# Inizialize globals


####

# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf' # modified people wet zone at 35
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/eplusout'


# WestZoneTemp, IT_Equip_Power, Whole_Building_Power
sensors = \
    [{"variable_name" : u"Zone Mean Air Temperature","variable_key":u"WEST ZONE","name": "WestZoneTemp"},
     {"variable_name": "Facility Total Building Electricity Demand Rate","variable_key": "Whole Building", "name": "IT_Equip_Power" },
    {"variable_name": "Facility Total Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_Building_Power" },
    # {"variable_name": "Facility Total HVAC Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_HVAC_Power" }
           ]


# hay más actuadores pero voy a dejarlo así por ahora
# West Zone setpoint temperature between10ºC and 40ºC
# este actuator existe
actuators =[{"component_type":"System Node Setpoint",
             "control_type": "Temperature Setpoint",
             "actuator_key":"West Zone DEC Outlet Node",
             "name":"WestZoneDECOutletNode_setpoint" }]

class rl_handler():
    def __init__(self, environment, actuators, sensors, folder, Qtable_pickle_file = None):
        self.logfile = os.path.join(folder, "eplus_rl.log")
        self.environment = environment
        self.actuators = actuators
        self.sensors = sensors
        self.q_table_file = Qtable_pickle_file
        self.hour = None
        self.day =None
        self.month =None
        self.minute = None
        # Get Sensor Values
        self.observation = dict()

    def create_q_table(self, env):
        if self.q_table_file:
            myfile = open(self.q_table_file, 'rb')
            qtable = pickle.load(myfile)
            Q = defaultdict(lambda: np.zeros(env.action_space.n), qtable)
        else:
            # no me queda claro de estar haciendo bien esto
            # Q = np.zeros((env.observation_space.shape[0], env.action_space.n))
            Q = defaultdict(lambda: np.zeros(env.action_space.n))
        return Q

    def create_log_file(self):
        try:
            os.remove(self.logfile)
        finally:
            Path(self.logfile).touch()

    def init_stats(self):
        episode_rewards = 0
        # Keeps track of useful statistics
        stats = plotting.EpisodeStats(
            episode_lengths=list(),
            episode_rewards=list(),
            people=list(),
            peopleheat=list()
        )
        return stats

    def write_info_logs_episode(self,episode):
        log = f"**********************START EPISODE{episode}***************************\n " \
              f"resetting people actuator\n " \
              f"at {self.day}/{self.month} hour:{self.hour} minute:{self.minute}\n"
        return log

    def write_info_logs(self,episode,step_in_episode, count):
        log = f"observation in episode {episode} at iteration: {step_in_episode}:\n " \
               f"at {self.day}/{self.month}  at {self.hour}:{self.minute}\n" \
               f"count: {count}\n {str(self.observation)}"
        return log

    def choose_action(self,env,Q,epsilon):
        if np.random.random() > epsilon:  # EXPLOIT
            action = np.argmax(Q[obs])
        else:  # EXPLORE
            action = env.action_space.sample()
            # elige una acción randomly

        return action

    def Qlearning(self, state):
        # declare globals here
        # todo EPISON COMO GLOBAL O COMO VARIABLE DE CLASE?
        global one_time, first_step_in_episode, env, stats, Q, step_in_episode, episode, episode_reward, count, action, obs, EPSILON,LEARNING_RATE,DISCOUNT
        count += 1
        if api.exchange.api_data_fully_ready(state):
            if one_time:
                for sensor in sensors:
                    globals()[sensor["name"]] = api.exchange.get_variable_handle(state,
                                                                                 sensor["variable_name"],
                                                                                 sensor["variable_key"]
                                                                                 )
                    # exec("%s = api.exchange.get_variable_handle(state, u'%s', u'%s')" % (sensor["name"],
                    #                                                                 sensor["variable_name"],
                    #                                                                 sensor["variable_key"]))

                for actuator in actuators:
                    globals()[actuator["name"]] = api.exchange.get_actuator_handle(state,
                                                                                   actuator["component_type"],
                                                                                   actuator["control_type"],
                                                                                   actuator["actuator_key"]
                                                                                   )
                self.create_log_file()
                # estas tres cosas son variables GLOBALES
                # TODO puede una variable de objeto ser global?????
                env = self.environment()
                Q = self.create_q_table(env)
                stats = self.init_stats()
                ####
                one_time = False

            # general simulation info
            self.hour = api.exchange.hour(state)
            self.day = api.exchange.day_of_month(state)
            self.month = api.exchange.month(state)
            self.minute = api.exchange.minutes(state)
            # Get Sensor Values
            self.observation = dict()
            for sensor in sensors:
                # OPCIÓN 1:
                handler_sensor_name = sensor["name"] + "_value"
                # exec("%s = api.api.exchange.get_variable_value(state, %s)" % (self.observation[sensor["name"]], sensor["name"]))
                # TODO SIMPLEMENTE CARGAR A LA LISTA OBSERVATION????? Y DE ALGUNA FORMA MAPEAR EN UN DICT
                # OPCIÓN 2:
                self.observation[sensor["name"]] = api.exchange.get_variable_value(state, globals()[sensor["name"]])

            # Only entry here if is the very first step, is Done, Or day ends
            if first_step_in_episode == True:
                # stats.episode_lengths.append(step_in_episode)

                # Reset Episode
                step_in_episode = 0
                episode_reward = 0
                episode += 1

                # just reset reward to 0 and reset actuator
                env.reset()

                # Reset actuators
                for actuator in actuators:
                    # en vez de resetarlo lo voy a poner a 25º
                    # api.exchange.reset_actuator(state, globals()[actuator["name"]])
                    api.exchange.set_actuator_value(state, globals()[actuator["name"]],25)
                log = self.write_info_logs_episode(episode)

                first_step_in_episode = False
                log += self.write_info_logs(episode,step_in_episode,count)

                obs = env.set_obs(self.observation)

                action = self.choose_action(env,Q,EPSILON)

                log += f"action choosed: {action} \n"

                # en caso de que haya más de un actuador
                actuator_value = dict()
                new_actuator_value = dict()
                for actuator in actuators:
                    actuator_value[actuator["name"]] = api.exchange.get_actuator_value(state,globals()[actuator["name"]])
                    new_actuator_value[actuator["name"]] = env.apply_action(action, actuator_value[actuator["name"]])

            else:
                log = self.write_info_logs(episode,step_in_episode,count)
                reward, done, _ = env.get_reward(self.observation)

                step_in_episode +=1
                episode_reward +=reward
                # stats.episode_rewards.append(reward)

                if done or (self.hour == 0 and self.minute == 60):
                    first_step_in_episode = True
                    # TODO encapsular en función
                    file = open(self.logfile, 'a')
                    file.write(log)
                    file.close()

                else:
                    # estudio de la respuesta a la acción s'
                    next_obs = env.set_obs(self.observation)
                    log += f"next state: {next_obs},reward : {reward}, done? {done}\n "
                    log += f"***END ITERATION {step_in_episode}\n"


                    # TD Update
                    # Todo poner en funcion
                    current_q = Q[obs][action]
                    max_future_q = np.max(Q[next_obs])
                    if reward == -1:
                        new_Q = reward
                    else:
                        new_Q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
                    Q[obs][action] = new_Q
                    obs = next_obs

                    # choose action according to
                    # the probability distribution

                    action = self.choose_action(env,Q,EPSILON)
                    new_actuator_value = dict()
                    actuator_value = dict()
                    for actuator in actuators:
                        actuator_value[actuator["name"]] = api.exchange.get_actuator_value(state, globals()[actuator["name"]])
                        new_actuator_value[actuator["name"]] = env.apply_action(action,
                                                                                actuator_value[actuator["name"]])
                        api.exchange.set_actuator_value(state,globals()[actuator["name"]],new_actuator_value[actuator["name"]])


one_time = True
first_step_in_episode = True
stats = None
matplotlib.style.use('ggplot')
env = None
env_state = None
ith_episode = 0
Q = None
count = 0
obs = tuple()
action = 0
first_step = True
next_obs = tuple()
LEARNING_RATE = 0.1
DISCOUNT = 0.95
EPSILON = 0.1
episode_rewards = 0
episode = 0


if __name__ == '__main__':
    # final_stats = plotting.EpisodeStats(
    #     episode_lengths=list(),
    #     episode_rewards=list(),
    #     people=list(),
    #     peopleheat=list()
    # )
    api = EnergyPlusAPI()
    handler = rl_handler(Power_Consumption_Op,actuators,sensors,'/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/paper_replication')
    for _ in range(1):
        state = api.state_manager.new_state()
        print("this is called only once")
        api.runtime.callback_end_zone_timestep_after_zone_reporting(state, handler.Qlearning)
        for sensor in sensors:
            api.exchange.request_variable(state, sensor["variable_name"], sensor["variable_key"])

        # trim off this python script name when calling the run_energyplus function so you end up with just
        # the E+ args, like: -d /output/dir -D /path/to/input.idf

        api.runtime.run_energyplus(state, ['-d', output,'-w', epwfile, idffile])
        # with open(f"/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable_no_rwd.pickle", "wb") as f:
        #     pickle.dump(dict(Q), f)

        # final_stats.episode_lengths.extend(stats.episode_lengths)
        # final_stats.episode_rewards.extend(stats.episode_rewards)
        # final_stats.people.extend(stats.people)
        # final_stats.peopleheat.extend(stats.peopleheat)
        api.state_manager.reset_state(state)
        one_time = True
        first_step = True

    # añadí esto para borrar las variables globales.
    # realmente no sé si hace alguna diferencia
    # plotting.plot_episode_stats(final_stats)
    for name in dir():
        if not name.startswith('_'):
            del globals()[name]




























