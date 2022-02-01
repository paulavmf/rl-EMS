import matplotlib
import numpy as np
import pandas as pd
from collections import namedtuple
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
import os


EpisodeStats = namedtuple("Stats",["episode_lengths", "episode_rewards", "people", "peopleheat"])
# EpisodeStats = namedtuple("Stats",["episode_lengths", "episode_rewards", "power_consumption", "Temperature"])


def plot_cost_to_go_mountain_car(env, estimator, num_tiles=20):
    x = np.linspace(env.observation_space.low[0], env.observation_space.high[0], num=num_tiles)
    y = np.linspace(env.observation_space.low[1], env.observation_space.high[1], num=num_tiles)
    X, Y = np.meshgrid(x, y)
    Z = np.apply_along_axis(lambda _: -np.max(estimator.predict(_)), 2, np.dstack([X, Y]))

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                           cmap=matplotlib.cm.coolwarm, vmin=-1.0, vmax=1.0)
    ax.set_xlabel('Position')
    ax.set_ylabel('Velocity')
    ax.set_zlabel('Value')
    ax.set_title("Mountain \"Cost To Go\" Function")
    fig.colorbar(surf)
    plt.show()


def plot_value_function(V, title="Value Function"):
    """
    Plots the value function as a surface plot.
    """
    min_x = min(k[0] for k in V.keys())
    max_x = max(k[0] for k in V.keys())
    min_y = min(k[1] for k in V.keys())
    max_y = max(k[1] for k in V.keys())

    x_range = np.arange(min_x, max_x + 1)
    y_range = np.arange(min_y, max_y + 1)
    X, Y = np.meshgrid(x_range, y_range)

    # Find value for all (x, y) coordinates
    Z_noace = np.apply_along_axis(lambda _: V[(_[0], _[1], False)], 2, np.dstack([X, Y]))
    Z_ace = np.apply_along_axis(lambda _: V[(_[0], _[1], True)], 2, np.dstack([X, Y]))

    def plot_surface(X, Y, Z, title):
        fig = plt.figure(figsize=(20, 10))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                               cmap=matplotlib.cm.coolwarm, vmin=-1.0, vmax=1.0)
        ax.set_xlabel('Player Sum')
        ax.set_ylabel('Dealer Showing')
        ax.set_zlabel('Value')
        ax.set_title(title)
        ax.view_init(ax.elev, -120)
        fig.colorbar(surf)
        plt.show()

    plot_surface(X, Y, Z_noace, "{} (No Usable Ace)".format(title))
    plot_surface(X, Y, Z_ace, "{} (Usable Ace)".format(title))



def plot_episode_stats(stats, smoothing_window=500, noshow=False):
    folder = "/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/rlStudies/PopZoneHeat_2"
    now = str(datetime.now()).replace(" ","_").replace(".","_").replace(":","-")
    # Plot the episode length over time
    fig1 = plt.figure(figsize=(10,5))
    plt.plot(stats.episode_lengths)
    plt.xlabel("Episode")
    plt.ylabel("Episode Length")
    plt.title("Episode Length over Time")
    plt.savefig(os.path.join(folder, "Episode_Length_step" + now + ".png"))
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
    plt.savefig(os.path.join(folder, "Episode_reward" + now + ".png"))
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
    plt.savefig(os.path.join(folder, "Episode_time_step" + now + ".png"))
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
    plt.savefig(os.path.join(folder, "n_people" + now + ".png"))
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
    plt.savefig(os.path.join(folder, "people_heat" + now + ".png"))
    if noshow:
        plt.close(fig5)
    else:
        # plt.show(fig2)
        fig5.show()



    return fig1, fig2, fig3, fig4, fig5