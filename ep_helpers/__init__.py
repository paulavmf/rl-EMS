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


def create_sensors(sensors,api,state):
    for sensor in sensors:
        globals()[sensor["name"] + "_handler"] = api.exchange.get_variable_handle(state,
                                                                     sensor["variable_name"],
                                                                     sensor["variable_key"]
                                                                     )

def create_actuators(actuators,api,state):
    for actuator in actuators:
        globals()[actuator["name"]+"_handler"] = api.exchange.get_actuator_handle(state,
                                                                       actuator["component_type"],
                                                                       actuator["control_type"],
                                                                       actuator["actuator_key"]
                                                                       )

# WestZoneTemp, IT_Equip_Power, Whole_Building_Power








