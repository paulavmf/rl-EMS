import gym
import itertools
import matplotlib
import matplotlib.style
import numpy as np
import pandas as pd
from rlStudies.testing_dummy_env import PopZoneEnv
import helpers as plotting


from collections import defaultdict


matplotlib.style.use('ggplot')

# https://www.geeksforgeeks.org/q-learning-in-python/

def createEpsilonGreedyPolicy(Q, epsilon, num_actions):
    """
    Creates an epsilon-greedy policy based
    on a given Q-function and epsilon.

    Returns a function that takes the state
    as an input and returns the probabilities
    for each action in the form of a numpy array
    of length of the action space(set of possible actions).
    """

    def policyFunction(state):
        Action_probabilities = np.ones(num_actions,
                                       dtype=float) * epsilon / num_actions

        best_action = np.argmax(Q[state[0]])
        Action_probabilities[best_action] += (1.0 - epsilon)
        return Action_probabilities

    return policyFunction

def inizialize_qLearning(env, num_episodes, discount_factor=1.0,
              alpha=0.6, epsilon=0.1):
    # Action value function
    # A nested dictionary that maps
    # state -> (action -> action-value).
    Q = defaultdict(lambda: np.zeros(env.action_space.n))

    # Keeps track of useful statistics
    stats = plotting.EpisodeStats(
        episode_lengths=np.zeros(num_episodes),
        episode_rewards=np.zeros(num_episodes))

    # Create an epsilon greedy policy function
    # appropriately for environment action space
    policy = createEpsilonGreedyPolicy(Q, epsilon, env.action_space.n)
    return Q,stats, policy


2
def qLearning(env, num_episodes, discount_factor=1.0,
              alpha=0.6, epsilon=0.1):
    """
    Q-Learning algorithm: Off-policy TD control.
    Finds the optimal greedy policy while improving
    following an epsilon-greedy policy"""

    # Action value function
    # A nested dictionary that maps
    # state -> (action -> action-value).
    Q = defaultdict(lambda: np.zeros(env.action_space.n))

    # Keeps track of useful statistics
    stats = plotting.EpisodeStats(
        episode_lengths=np.zeros(num_episodes),
        episode_rewards=np.zeros(num_episodes))

    # Create an epsilon greedy policy function
    # appropriately for environment action space
    policy = createEpsilonGreedyPolicy(Q, epsilon, env.action_space.n)

    # For every episode
    '''
    qu?? diferencia hay entre episodio... cada episodio vuelvo a resetear el environment
    le doy un cierto n??mero de intentos para que intente regular el n??mero de gente seg??n la camntidad de calor
    
    '''
    for ith_episode in range(num_episodes):

        # Reset the environment and pick the first action
        state = env.reset()

        # esto tiene que ocurrir en cada step de la simulaci??n
        for t in itertools.count():

            # get probabilities of all actions from current state
            action_probabilities = policy(state)

            # choose action according to
            # the probability distribution
            action = np.random.choice(np.arange(
                len(action_probabilities)),
                p=action_probabilities)

            # take action and get reward, transit to next state
            # next state es el nuevo n??mero de ocupantes que tengo que meter en
            # energy plus a la misma vez que saco next state tengo que actualizar
            # las condiciones en energy plus
            '''
            cada step calculo el reward de ese step y el pr??ximo state resultado de la acci??n
            '''
            # next_state ser??a la predicci??n del d??a siguiente por ejemplo?
            next_state, reward, done, _ = env.step(action)

            # Update statistics
            stats.episode_rewards[ith_episode] += reward
            stats.episode_lengths[ith_episode] = t

            # TD Update
            '''
            mejor acci??n a tomar seg??n la Q table
            '''
            best_next_action = np.argmax(Q[next_state])
            td_target = reward + discount_factor * Q[next_state][best_next_action]
            td_delta = td_target - Q[state][action]
            Q[state][action] += alpha * td_delta

            # done is True if episode terminated
            if done:
                break

            state = next_state

    return Q, stats

# Q, stats = qLearning(env, 1000) # environment se actualiza en cada time step