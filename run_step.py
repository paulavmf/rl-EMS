"""
mirar:
https://github.com/NREL/EnergyPlus/blob/develop/testfiles/PythonPluginCustomSchedule.py
https://unmethours.com/question/58313/how-can-i-simulate-just-one-time-step-dt-60s-with-the-e-api/


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
from pyenergyplus.plugin import EnergyPlusPlugin


one_time = True
people_heat_sensor = 0
people_actuator = 0
people_sensor = 0
solar_sensor = 0
count = 0


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

# TODO EMS Calling Point: BeginTimeStepBeforePredictor o EndOzZOneTimestepAfterZoneReportong



class HeatingSetPoint(EnergyPlusPlugin):
    def actuate(self, state, x):
        self.api.exchange.set_actuator_value(state, actuators[0]['name'], x)

    def on_begin_timestep_before_predictor(self, state) -> int:
        pass



