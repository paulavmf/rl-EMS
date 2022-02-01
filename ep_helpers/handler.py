from pyenergyplus.api import EnergyPlusAPI
import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')
from pyenergyplus.api import EnergyPlusAPI
import matplotlib.style
import numpy as np
import helpers as plotting
from collections import defaultdict
from pathlib import Path
import pickle
import os

def set_globals():
    one_time = True
    first_step_in_episode = True
    step_in_episode = 0
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
    episode_reward = 0
    episode = 0
    return globals()

class rl_handler():
    def __init__(self,api, environment, actuators, sensors, folder, Qtable_pickle_file = None):
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
        self.api = api

    def create_q_table(self, env):
        if self.q_table_file:
            if os.path.isfile(self.q_table_file):
                myfile = open(self.q_table_file, 'rb')
                qtable = pickle.load(myfile)
                Q = defaultdict(lambda: np.zeros(env.action_space.n), qtable)
            else:
                # no me queda claro de estar haciendo bien esto
                # Q = np.zeros((env.observation_space.shape[0], env.action_space.n))
                Q = defaultdict(lambda: np.zeros(env.action_space.n))
        else:
            Q = defaultdict(lambda: np.zeros(env.action_space.n))
        return Q

    def create_log_file(self):
        try:
            os.remove(self.logfile)
        finally:
            Path(self.logfile).touch()


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
        if self.api.exchange.api_data_fully_ready(state):
            if one_time:
                for sensor in self.sensors:
                    globals()[sensor["name"]] = self.api.exchange.get_variable_handle(state,
                                                                                      sensor["variable_name"],
                                                                                      sensor["variable_key"]
                                                                                      )
                    # exec("%s = api.exchange.get_variable_handle(state, u'%s', u'%s')" % (sensor["name"],
                    #                                                                 sensor["variable_name"],
                    #                                                                 sensor["variable_key"]))

                for actuator in self.actuators:
                    globals()[actuator["name"]] = self.api.exchange.get_actuator_handle(state,
                                                                                   actuator["component_type"],
                                                                                   actuator["control_type"],
                                                                                   actuator["actuator_key"]
                                                                                   )
                self.create_log_file()
                # estas tres cosas son variables GLOBALES
                # TODO puede una variable de objeto ser global?????
                env = self.environment()
                Q = self.create_q_table(env)
                stats = env.init_stats()
                ####
                one_time = False

            # general simulation info
            self.hour = self.api.exchange.hour(state)
            self.day = self.api.exchange.day_of_month(state)
            self.month = self.api.exchange.month(state)
            self.minute = self.api.exchange.minutes(state)
            # Get Sensor Values
            self.observation = dict()
            for sensor in self.sensors:
                # OPCIÓN 1:
                handler_sensor_name = sensor["name"] + "_value"
                # exec("%s = api.api.exchange.get_variable_value(state, %s)" % (self.observation[sensor["name"]], sensor["name"]))
                # TODO SIMPLEMENTE CARGAR A LA LISTA OBSERVATION????? Y DE ALGUNA FORMA MAPEAR EN UN DICT
                # OPCIÓN 2:
                self.observation[sensor["name"]] = self.api.exchange.get_variable_value(state, globals()[sensor["name"]])

            stats = env.update_stats(stats,self.observation)

            # Only entry here if is the very first step, is Done, Or day ends
            if first_step_in_episode == True:
                stats.episode_lengths.append(step_in_episode)

                # Reset Episode
                step_in_episode = 0
                episode_reward = 0
                episode += 1

                # just reset reward to 0 and reset actuator
                env.reset()

                # Reset actuators
                for actuator in self.actuators:
                    # en vez de resetarlo lo voy a poner a 25º
                    self.api.exchange.reset_actuator(state, globals()[actuator["name"]])
                    # self.api.exchange.set_actuator_value(state, globals()[actuator["name"]],25)
                log = self.write_info_logs_episode(episode)

                first_step_in_episode = False
                log += self.write_info_logs(episode,step_in_episode,count)

                obs = env.set_obs(self.observation)

                action = self.choose_action(env,Q,EPSILON)

                log += f"action choosed: {action} \n"

                # en caso de que haya más de un actuador
                actuator_value = dict()
                new_actuator_value = dict()
                for actuator in self.actuators:
                    actuator_value[actuator["name"]] = self.api.exchange.get_actuator_value(state,globals()[actuator["name"]])
                    new_actuator_value[actuator["name"]] = env.apply_action(self.observation, action)

            else:
                log = self.write_info_logs(episode,step_in_episode,count)
                reward, done, _ = env.get_reward(self.observation)

                step_in_episode +=1
                episode_reward +=reward
                stats.episode_rewards.append(reward)

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
                    for actuator in self.actuators:
                        # actuator_value[actuator["name"]] = self.api.exchange.get_actuator_value(state, globals()[actuator["name"]])
                        new_actuator_value[actuator["name"]] = env.apply_action(self.observation, action
                                                                                )
                        # new_actuator_value[actuator["name"]] = env.apply_action(action,
                        #                                                         actuator_value[actuator["name"]])
                        self.api.exchange.set_actuator_value(state,globals()[actuator["name"]],new_actuator_value[actuator["name"]])