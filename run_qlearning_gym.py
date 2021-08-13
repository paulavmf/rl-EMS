
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
from rlStudies.PopZoneHeat import PopHeatEnv
import helpers as plotting
from collections import defaultdict
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')


matplotlib.style.use('ggplot')
one_time = True
people_heat_sensor = 0
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
ini_environment = False
ini_simulation = False
count = 0


# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf'
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/APItesting/'


def qLearning_handler(state):
    global one_time,people_heat_sensor,people_actuator, people_sensor,alpha, epsilon, discount_factor, num_episodes, policy, env, stats, env_state, ith_episode, t, episode_terminated, Q, first_step,ini_environment, ini_simulation, count
    sys.stdout.flush()
    # handlers setting
    count += 1
    print(f"simulation number = {count}")
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

            people_heat_sensor = api.exchange.get_variable_handle(
                state, "Zone People Total Heating Rate", "West Zone"
            )

            """
            inicializo mi environment:

            Q-Learning algorithm: Off-policy TD control.
            Finds the optimal greedy policy while improving
            following an epsilon-greedy policy
            """
            initial_people= 35
            api.exchange.set_actuator_value(state, people_actuator, initial_people)
            one_time = False

        # SEGUNDO STEP: INICIALIZO ENVIRONMENT
        if api.exchange.zone_time_step_number(state) == 2 and ini_environment == False:
            heat = api.exchange.get_variable_value(state,people_heat_sensor)
            npop = api.exchange.get_variable_value(state,people_sensor)
            env = PopHeatEnv(npop, heat)
            Q = defaultdict(lambda: np.zeros(env.action_space.n))

            # Keeps track of useful statistics
            stats = plotting.EpisodeStats(
                episode_lengths=np.zeros(num_episodes),
                episode_rewards=np.zeros(num_episodes))

            # Create an epsilon greedy policy function
            # appropriately for environment action space
            policy = createEpsilonGreedyPolicy(Q, epsilon, env.action_space.n)
            ini_environment = True
            t = 0
        if api.exchange.zone_time_step_number(state) == 3:
            ini_simulation = True

        # SIMULACIÓN SIEMPRE
        hour = api.exchange.hour(state)
        day = api.exchange.day_of_month(state)
        month = api.exchange.month(state)
        if ini_simulation == True:
            if (hour == 0 and api.exchange.zone_time_step_number(state) == 3) or t == 0:
                print("starting an spisode")
                ith_episode += 1
                heat = api.exchange.get_variable_value(state, people_heat_sensor)
                people = api.exchange.get_variable_value(state, people_sensor)
                print(f"people : {people} sensore lecture; heat : {heat} sensore lecture  ")
                env_state = env.reset(people, heat)
            if not (hour == 0 and api.exchange.zone_time_step_number(state) == 3):
                t += 1
                # get probabilities of all actions from current state
                action_probabilities = policy(env_state)

                # choose action according to
                # the probability distribution
                action = np.random.choice(np.arange(
                    len(action_probabilities)),
                    p = action_probabilities)

                next_npop, reward, done, _ = env.step(action)
                print(f"next state: {next_npop},reward : {reward}, done? {done} ")

                # Update statistics
                stats.episode_rewards[ith_episode] += reward
                stats.episode_lengths[ith_episode] = t

                # TD Update
                best_next_action = np.argmax(Q[next_npop])
                td_target = reward + discount_factor * Q[next_npop][best_next_action]
                td_delta = td_target - Q[state][action]
                Q[state][action] += alpha * td_delta

                # done is True if episode terminated
                if done:
                    print("DONE")
                    t = 0

                api.exchange.set_actuator_value(state, people_actuator,next_npop)
                if month == 7 and day == 3 and hour == 0 :
                    print(Q)
                    print(stats)

if __name__ == '__main__':
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    print("this is called only once")
    api.runtime.callback_end_zone_timestep_after_zone_reporting(state, qLearning_handler)
    api.exchange.request_variable(state, "Site Direct Solar Radiation Rate per Area", "ENVIRONMENT")
    api.exchange.request_variable(state, "Zone People Total Heating Rate", "West Zone")
    api.exchange.request_variable(state, "Zone People Occupant Count", "West Zone")
    # trim off this python script name when calling the run_energyplus function so you end up with just
    # the E+ args, like: -d /output/dir -D /path/to/input.idf
    api.runtime.run_energyplus(state, ['-w', epwfile, idffile])