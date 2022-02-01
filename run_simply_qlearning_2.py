"""

"""



import os
import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')

from testing_random_decision import createEpsilonGreedyPolicy
from pyenergyplus.api import EnergyPlusAPI
import matplotlib.style
import numpy as np
from environments.PopZoneHeat_2 import PopHeatEnv
import helpers as plotting
from collections import defaultdict
from pathlib import Path
import pickle

matplotlib.style.use('ggplot')
one_time = True
people_heat_sensor = 0
people_actuator = 0
people_sensor = 0
solar_sensor = 0
alpha=0.6
epsilon=0.1
discount_factor=1.0
num_episodes = 500
policy = None
env = None
stats = None
env_state = None
ith_episode = 0
t = 0
Q = None
count = 0
obs = tuple()
action = 0
first_step = True
next_obs = tuple()
LEARNING_RATE = 0.1
DISCOUNT = 0.95
episode_rewards = 0

# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf' # modified people wet zone at 35
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/eplusout'

sensors = \
    [{"variable_name" : u"Site Direct Solar Radiation Rate per Area","variable_key":u"ENVIRONMENT","name": "solar_sensor"},
     {"variable_name": "Zone People Occupant Count","variable_key": "West Zone", "name": "people_sensor" },
    {"variable_name": "Zone People Total Heating Rate","variable_key": "West Zone", "name": "people_heat_sensor" }
           ]

actuators =[{"component_type":"People",
             "control_type": "Number of People",
             "actuator_key":"WEST ZONE PEOPLE",
             "name":"people_actuator" }]

def qLearning_handler(state):
    global one_time, alpha, epsilon, discount_factor, num_episodes, policy, env, stats, env_state, ith_episode, t, Q, first_step, count,obs, action, finish, obs, next_obs, LEARNING_RATE, DISCOUNT, episode_rewards
    sys.stdout.flush()

    count += 1
    # print(f"simulation number = {count}")
    if api.exchange.api_data_fully_ready(state):
        if one_time:
            # todo estas variables son globales
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
                exec("%s = api.exchange.get_actuator_handle(state, '%s', u'%s', u'%s')" % (actuator["name"],
                                                                                   actuator["component_type"],
                                                                                   actuator["control_type"],
                                                                                   actuator["actuator_key"]))

            # solar_sensor = api.exchange.get_variable_handle(
            #     state, u"Site Direct Solar Radiation Rate per Area", u"ENVIRONMENT"
            # )
            # people_actuator = api.exchange.get_actuator_handle(
            #     state, "People", "Number of People", "WEST ZONE PEOPLE"
            # )
            # people_sensor = api.exchange.get_variable_handle(
            #     state, "Zone People Occupant Count", "West Zone")
            #
            # people_heat_sensor = api.exchange.get_variable_handle(
            #     state, "Zone People Total Heating Rate", "West Zone"
            # )

            """
            inicializo mi environment:

            Q-Learning algorithm: Off-policy TD control.
            Finds the optimal greedy policy while improving
            following an epsilon-greedy policy
            """
            try:
                os.remove("eplus_rl.log")
            finally:
                Path("eplus_rl.log").touch()
            # SEGUNDO STEP: INICIALIZO ENVIRONMENT
            env = PopHeatEnv()
            if os.path.isfile("/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable.pickle"):
                myfile = open("/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable.pickle", 'rb')
                qtable = pickle.load(myfile)
                Q = defaultdict(lambda: np.zeros(env.action_space.n), qtable)
            else:
                # no me queda claro de estar haciendo bien esto
                # Q = np.zeros((env.observation_space.shape[0], env.action_space.n))
                Q = defaultdict(lambda: np.zeros(env.action_space.n))
            episode_rewards = 0
            # Keeps track of useful statistics
            stats = plotting.EpisodeStats(
                episode_lengths=list(),
                episode_rewards=list(),
                people = list(),
                peopleheat=list()
            )

            # Create an epsilon greedy policy function
            # appropriately for environment action space
            policy = createEpsilonGreedyPolicy(Q, epsilon, env.action_space.n)
            # aquí defino tmb la Q table
            one_time = False

        # SIMULACIÓN SIEMPRE
        hour = api.exchange.hour(state)
        time = api.exchange.current_time(state)
        day = api.exchange.day_of_month(state)
        month = api.exchange.month(state)
        minute = api.exchange.minutes(state)
        people_heat = api.exchange.get_variable_value(state, people_heat_sensor)
        people = api.exchange.get_variable_value(state, people_sensor)
        stats.people.append(people)
        stats.peopleheat.append(people_heat)
        solar = api.exchange.get_variable_value(state, solar_sensor)
        # runned only first step, when a day finished or when done condition is true
        if first_step == True:
            # ¢ount of steps every episode
            stats.episode_lengths.append(t)
            t = 0
            episode_rewards = 0
            ith_episode += 1
            # just reset reward to 0 and reset actuator
            env.reset()
            api.exchange.reset_actuator(state, people_actuator)
            log = f"**********************START EPISODE{ith_episode}***************************\n " \
                  f"resetting people actuator\n " \
                  f"at {day}/{month} hour:{hour} minute:{minute}\n"

            first_step = False # TODO look for a better name than first step
            # ******
            # get probabilities of all actions from current state
            log += f"observation in episode {ith_episode} at iteration: {t}:\n " \
                  f"at {day}/{month}  at {hour}:{minute}\n" \
                  f"count: {count}\n people_heat: {people_heat}\n " \
                  f"people_count: {people}\n solar: {solar}\n"


            # estudio del estado s del entorno
            obs = env.set_obs(people, people_heat, solar)

            # Selección de la acción
            # action_probabilities = policy(obs)

            # choose action according to
            # the probability distribution
            if np.random.random() > epsilon:  # EXPLOIT
                action = np.argmax(Q[obs])
            else:  # EXPLORE
                action = np.random.randint(0, 3)
                # elige una acción randomly

            log += f"action choosed: {action} \n"

            new_people = env.apply_action(action)
            # api.exchange.set_actuator_value(state, people_actuator, new_people)

            log += f"new number of people in next state {new_people}"

            file = open('eplus_rl.log', 'a')
            file.write(log)
            file.close()

        # runnend after first step or only when Q has been updated in the previous step
        else:
            log = f"reading observation after action in episode {ith_episode} at iteration: {t}:\n " \
                  f"at {day}/{month} hour:{hour} minute:{minute}\n" \
                  f"count: {count}\n {day}/{month} at {hour}\n " \
                  f"new people_heat: {people_heat}\n new people_count: {people}\n"
            # recompensa

            reward, done, _ = env.get_reward(people_heat)

            # Update statistics
            t += 1
            episode_rewards += reward
            stats.episode_rewards.append(reward)


            if done or (hour == 0 and minute == 60):
                first_step = True
                file = open('eplus_rl.log', 'a')
                file.write(log)
                file.close()
            else:
                # estudio de la respuesta a la acción s'
                next_obs = env.set_obs(people, people_heat, solar)

                log += f"next state: {next_obs},reward : {reward}, done? {done}\n "
                log += f"***END ITERATION {t}\n"

                # TD Update
                current_q = Q[obs][action]
                max_future_q = np.max(Q[next_obs])
                if reward == -1:
                    new_Q = reward
                else:
                    new_Q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
                Q[obs][action] = new_Q

                obs = next_obs
                action_probabilities = policy(obs)

                # choose action according to
                # the probability distribution
                if np.random.random() > epsilon:  # EXPLOIT
                    action = np.argmax(Q[obs])
                else:  # EXPLORE
                    action = np.random.randint(0, 3)
                    # elige una acción randomly

                new_people = env.apply_action(action)

                api.exchange.set_actuator_value(state, people_actuator, new_people)

                log += f"taking action at {ith_episode} at iteration: {t}:\n " \
                       f"at {day}/{month} hour:{hour} minute:{minute}\n" \
                       f"action taked {action}\n "

                file = open('eplus_rl.log', 'a')
                file.write(log)
                file.close()






if __name__ == '__main__':
    final_stats = plotting.EpisodeStats(
        episode_lengths=list(),
        episode_rewards=list(),
        people=list(),
        peopleheat=list()
    )
    api = EnergyPlusAPI()
    for _ in range(5):
        state = api.state_manager.new_state()
        print("this is called only once")
        api.runtime.callback_end_zone_timestep_after_zone_reporting(state, qLearning_handler)
        api.exchange.request_variable(state, "Site Direct Solar Radiation Rate per Area", "ENVIRONMENT")
        api.exchange.request_variable(state, "Zone People Total Heating Rate", "West Zone")
        api.exchange.request_variable(state, "Zone People Occupant Count", "West Zone")
        # trim off this python script name when calling the run_energyplus function so you end up with just
        # the E+ args, like: -d /output/dir -D /path/to/input.idf

        api.runtime.run_energyplus(state, ['-d', output,'-w', epwfile, idffile])
        with open("/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable.pickle", "wb") as f:
            pickle.dump(dict(Q), f)
        final_stats.episode_lengths.extend(stats.episode_lengths)
        final_stats.episode_rewards.extend(stats.episode_rewards)
        final_stats.people.extend(stats.people)
        final_stats.peopleheat.extend(stats.peopleheat)
        api.state_manager.reset_state(state)
        one_time = True
        first_step = True

    # añadí esto para borrar las variables globales.
    # realmente no sé si hace alguna diferencia
    plotting.plot_episode_stats(final_stats)

    for name in dir():
        if not name.startswith('_'):
            del globals()[name]



