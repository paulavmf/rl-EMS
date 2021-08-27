import os
import sys
from rlStudies.QLearning import createEpsilonGreedyPolicy
from pyenergyplus.api import EnergyPlusAPI
import logging
import matplotlib.style
import numpy as np
from rlStudies.PopZoneHeat import PopHeatEnv
import helpers as plotting
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')

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
obs = tuple()
next_obs = tuple()

# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf' # modified people wet zone at 35
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/APItesting/'




def qLearning_handler(state):
    global one_time,people_heat_sensor,people_actuator, people_sensor, solar_sensor, alpha, epsilon, discount_factor, num_episodes, policy, env, stats, env_state, ith_episode, t, Q, first_step, count,obs, action, finish, obs, next_obs
    sys.stdout.flush()

    count += 1
    # print(f"simulation number = {count}")
    if api.exchange.api_data_fully_ready(state):
        if one_time:
            solar_sensor = api.exchange.get_variable_handle(
                state, u"Site Direct Solar Radiation Rate per Area", u"ENVIRONMENT"
            )
            people_actuator = api.exchange.get_actuator_handle(
                state, "People", "Number of People", "WEST ZONE PEOPLE"
            )
            people_sensor = api.exchange.get_variable_handle(
                state, "Zone People Occupant Count", "West Zone")

            people_heat_sensor = api.exchange.get_variable_handle(
                state, "Zone People Total Heating Rate", "West Zone"
            )

            """
            inicializo mi environment:

            Q-Learning algorithm: Off-policy TD control.
            Finds the optimal greedy policy while improving
            following an epsilon-greedy policy
            """
            try:
                os.remove("/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/eplus_rl.log")
            finally:
                Path("/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/eplus_rl.log").touch()
            # SEGUNDO STEP: INICIALIZO ENVIRONMENT
            env = PopHeatEnv()
            Q = defaultdict(lambda: np.zeros(env.action_space.n))

            # Keeps track of useful statistics
            stats = plotting.EpisodeStats(
                episode_lengths=np.zeros(num_episodes),
                episode_rewards=np.zeros(num_episodes),
                people = list(),
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
        solar = api.exchange.get_variable_value(state, solar_sensor)
        # runned only first step, when a day finished or when done condition is true
        if first_step == True:
            # ¢ount of steps every episode
            stats.episode_lengths[ith_episode] = t
            t = 0
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
            action_probabilities = policy(obs)

            # choose action according to
            # the probability distribution
            action = np.random.choice(np.arange(
                len(action_probabilities)),
                p=action_probabilities)

            log += f"action choosed: {action} \n"

            new_people = env.apply_action(action)

            api.exchange.set_actuator_value(state, people_actuator, new_people)

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
            stats.episode_rewards[ith_episode] += reward


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
                best_next_action = np.argmax(Q[next_obs])
                td_target = reward + discount_factor * Q[next_obs][best_next_action]
                td_delta = td_target - Q[obs][action]
                Q[obs][action] += alpha * td_delta

                obs = next_obs
                action_probabilities = policy(obs)

                # choose action according to
                # the probability distribution
                action = np.random.choice(np.arange(
                    len(action_probabilities)),
                    p=action_probabilities)

                new_people = env.apply_action(action)

                api.exchange.set_actuator_value(state, people_actuator, new_people)

                log += f"taking action at {ith_episode} at iteration: {t}:\n " \
                       f"at {day}/{month} hour:{hour} minute:{minute}\n" \
                       f"action taked {action}\n "

                file = open('eplus_rl.log', 'a')
                file.write(log)
                file.close()






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
    plotting.plot_episode_stats(stats)



