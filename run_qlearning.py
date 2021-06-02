
import sys
from rlStudies.QLearning import createEpsilonGreedyPolicy
from pyenergyplus.api import EnergyPlusAPI
from dummy_transformation import  set_people, simple_decision_people
from rlStudies.simplerl import applay_random_action, PopZoneEnv
import gym
import itertools
import matplotlib
import matplotlib.style
import numpy as np
import pandas as pd
from rlStudies.simplerl import PopZoneEnv
import helpers as plotting
from collections import defaultdict
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')


matplotlib.style.use('ggplot')

# GLOBAL VARIABLES

one_time = True
solar_sensor = 0
people_actuator = 0
people_sensor = 0
alpha=0.6
epsilon=0.1
discount_factor=1.0
num_episodes = 1000
policy = None
env = None
stats = None
env_state = None
ith_episode = 0
t = 0
episode_terminated = False
Q = None


# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf'
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/APItesting/'


def qLearning_handler(state):
    global one_time,solar_sensor,people_actuator, people_sensor,alpha, epsilon, discount_factor, num_episodes, policy, env, stats, env_state, ith_episode, t, episode_terminated, Q
    sys.stdout.flush()
    # handlers setting
    if api.exchange.api_data_fully_ready(state):
        if one_time:
            solar_sensor = api.exchange.get_variable_handle(
                state, u"Site Direct Solar Radiation Rate per Area", u"ENVIRONMENT"
            )
            people_actuator = api.exchange.get_actuator_handle(
                state ,"People","Number of People","WEST ZONE PEOPLE"
            )
            people_sensor = api.exchange.get_variable_handle(
                state,"Zone People Occupant Count", "West Zone" )

            """
            inicializo mi environment:

            Q-Learning algorithm: Off-policy TD control.
            Finds the optimal greedy policy while improving
            following an epsilon-greedy policy
            """
            people = api.exchange.get_variable_value(state, people_sensor)
            print(f"{people} sensore lecture")
            env = PopZoneEnv(people)
            # Action value function
            # A nested dictionary that maps
            # state -> (action -> action-value)
            # Q es una matiz
            Q = defaultdict(lambda: np.zeros(env.action_space.n))

            # Keeps track of useful statistics
            stats = plotting.EpisodeStats(
                episode_lengths=np.zeros(num_episodes),
                episode_rewards=np.zeros(num_episodes))

            # Create an epsilon greedy policy function
            # appropriately for environment action space
            policy = createEpsilonGreedyPolicy(Q, epsilon, env.action_space.n)
        api.exchange.set_actuator_value(state, people_actuator, 35)
        one_time = False
        hour = api.exchange.hour(state)
        day = api.exchange.day_of_month(state)
        month = api.exchange.month(state)
        min = api.exchange.minutes(state)

        # TODO no trabaja todos los días de mes. Why?
        if t == 0:
            print("starting an spisode")
            ith_episode += 1
            t += 1
            # todos los días 1 del mes hay un nuevo episodio
            people = api.exchange.get_variable_value(state, people_sensor)
            print(f"{people} sensore lecture")
            env_state = env.reset()
            api.exchange.set_actuator_value(state, people_actuator, env_state)
            print(f"reset number of people at {env_state}")
            # cada hora
        if t != 0:
            t += 1
            # get probabilities of all actions from current state
            action_probabilities = policy(env_state)

            # choose action according to
            # the probability distribution
            action = np.random.choice(np.arange(
                len(action_probabilities)),
                p = action_probabilities)

            # take action and get reward, transit to next state
            # por ahora vale porque solo estoy jugando para entender,
            # pero next state debe salir de la propia simulación
            next_state, reward, done, _ = env.step(action)
            print(f"next state: {next_state},reward : {reward}, done? {done} ")

            # Update statistics
            stats.episode_rewards[ith_episode] += reward
            stats.episode_lengths[ith_episode] = t

            # TD Update
            best_next_action = np.argmax(Q[next_state])
            td_target = reward + discount_factor * Q[next_state][best_next_action]
            td_delta = td_target - Q[state][action]
            Q[state][action] += alpha * td_delta

            # done is True if episode terminated
            if done:
                print("DONE")
                t = 0

            npop = next_state
            api.exchange.set_actuator_value(state, people_actuator,npop)
        if ith_episode == 65 :
            print(Q)
            print(stats)

if __name__ == '__main__':
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    print("this is called only once")
    api.runtime.callback_end_zone_timestep_after_zone_reporting(state, qLearning_handler)
    api.exchange.request_variable(state, "Site Direct Solar Radiation Rate per Area", "ENVIRONMENT")
    api.exchange.request_variable(state, "Zone People Occupant Count", "West Zone")
    # trim off this python script name when calling the run_energyplus function so you end up with just
    # the E+ args, like: -d /output/dir -D /path/to/input.idf
    api.runtime.run_energyplus(state, ['-w', epwfile, idffile])