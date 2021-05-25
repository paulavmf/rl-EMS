# from https://github.com/NREL/EnergyPlus/blob/develop/tst/EnergyPlus/api/TestDataTransfer.py

import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')
from pyenergyplus.api import EnergyPlusAPI
from dummy_transformation import  set_people, simple_decision_people

one_time = True
solar_sensor = 0
people_actuator = 0
people_sensor = 0
n = 0
m = 0

idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf'
iddfile = '/usr/local/EnergyPlus-9-4-0/Energy+.idd'
epwfile = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/input/wheather_file/FRA_Paris.Orly.071490_IWEC.epw'
output = '/home/paula/Documentos/Doctorado/Desarrollo/EPProject/APItesting/'
# idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/1ZoneUncontrolled_win_1.idf'
# idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/1ZoneUncontrolled_win_1.idf'

def my_handler(state):
    global one_time, solar_sensor, people_actuator, n, m, people_sensor, people, Radiation_Rate
    sys.stdout.flush()
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
        one_time = False
        hour = api.exchange.hour(state)
        day = api.exchange.day_of_month(state)
        month = api.exchange.month(state)
        Radiation_Rate  = api.exchange.get_variable_value(state, solar_sensor)

        if hour == 8:
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            print(f"{people} average before actuator")
        if hour == 9:
            api.exchange.set_actuator_value(state,people_actuator,50)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"{people} average after actuator")
        if hour == 22:
            api.exchange.reset_actuator(state,people_actuator)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"{people} average after reset actuator")
        if Radiation_Rate > 700:
            api.exchange.set_actuator_value(state,people_actuator,set_people())
            print(f"demasiado {Radiation_Rate}")

def my_handler_function_decision(state):
    global one_time, solar_sensor, people_actuator, n, m, people_sensor, people, Radiation_Rate
    sys.stdout.flush()
    # TODO debería pedir el handle solo una vez ??? no entiendo xq
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
            if solar_sensor == -1 or people_actuator == -1:
                sys.exit(1)
        one_time = False
        hour = api.exchange.hour(state)
        day = api.exchange.day_of_month(state)
        month = api.exchange.month(state)
        Radiation_Rate  = api.exchange.get_variable_value(state, solar_sensor)
        if hour == 8:
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            print(f"{people} average before actuator")
        if hour == 9:
            value = simple_decision_people(Radiation_Rate)
            api.exchange.set_actuator_value(state,people_actuator,value)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"{people} average after actuator")
        if hour == 22:
            api.exchange.reset_actuator(state,people_actuator)
            print(f"Radiation rate in w/m2 at {day} de {month} a las {hour}  is {Radiation_Rate}")
            people = api.exchange.get_variable_value(state,people_sensor)
            print(f"{people} average after reset actuator")



if __name__ == '__main__':
    api = EnergyPlusAPI()
    state = api.state_manager.new_state()
    print("this is called only once")
    # new_temp = set_new_temp()
    api.runtime.callback_begin_system_timestep_before_predictor(state, my_handler)
    # api.runtime.callback_begin_system_timestep_before_predictor(state, my_handler_function_decision)
    # api.exchange.request_variable(state, "SITE OUTDOOR AIR DRYBULB TEMPERATURE", "ENVIRONMENT")
    # api.exchange.request_variable(state, "SITE OUTDOOR AIR DEWPOINT TEMPERATURE", "ENVIRONMENT")
    # api.exchange.request_variable(state, "Site Outdoor Air Humidity Ratio","ENVIRONMENT" )
    # api.exchange.request_variable(state, "Wind Speed", "ENVIRONMENT")
    api.exchange.request_variable(state, "Site Direct Solar Radiation Rate per Area", "ENVIRONMENT")
    api.exchange.request_variable(state, "Zone People Occupant Count", "West Zone")
    # trim off this python script name when calling the run_energyplus function so you end up with just
    # the E+ args, like: -d /output/dir -D /path/to/input.idf
    api.runtime.run_energyplus(state, ['-w', epwfile, idffile])