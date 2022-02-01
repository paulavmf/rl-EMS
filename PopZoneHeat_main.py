import os
import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')

from pyenergyplus.api import EnergyPlusAPI
import matplotlib.style
from ep_helpers.handler import rl_handler
from environments.PopZoneHeat import PopHeatEnv, plot_episode_stats
import pickle



"""

The state vector contains the following:
    –Outdoor air temperature between -20ªC and 50ªC 
    –West Zone air temperature between -20 C and 50ºC  <-- 
    –East Zone air temperature between -20ºC and 50ºC
    –Total electric demand power between 0W and 1GW <--
    –Non-HVAC electric demand power between 0W and 1GW <--
    –HVAC electric demand power between 0W and 1GW 
    PATA UN PRIMER ESTUDIO SOLO UTILIZARÉ TRES
"""

# Inizialize globals


####

# FILES
idffile = '/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/2ZoneDataCenterHVAC_wEconomizer.idf' # modified people wet zone at 35
# idffile = "/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/Model/1ZoneUncontrolled_win_1.idf"
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



if __name__ == '__main__':
    q_file = f"/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable.pickle"
    api = EnergyPlusAPI()
    handler = rl_handler(api, PopHeatEnv,actuators,sensors,'/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/rlStudies',Qtable_pickle_file= q_file)
    sim_env = PopHeatEnv()
    final_stats = sim_env.init_stats()
    for _ in range(2):
        state = api.state_manager.new_state()
        print("this is called only once")
        api.runtime.callback_end_zone_timestep_after_zone_reporting(state, handler.Qlearning)
        for sensor in sensors:
            api.exchange.request_variable(state, sensor["variable_name"], sensor["variable_key"])

        # trim off this python script name when calling the run_energyplus function so you end up with just
        # the E+ args, like: -d /output/dir -D /path/to/input.idf

        api.runtime.run_energyplus(state, ['-d', output,'-w', epwfile, idffile])
        from ep_helpers.handler import Q
        with open(q_file, "wb") as f:
            pickle.dump(dict(Q), f)
        from ep_helpers.handler import stats
        sim_env.update_simulation_stats(final_stats,stats)
        api.state_manager.reset_state(state)
        import ep_helpers.handler as variables
        variables.first_step = False
        variables.one_time = False

    # añadí esto para borrar las variables globales.
    # realmente no sé si hace alguna diferencia
    plot_episode_stats(final_stats)
    for name in dir():
        if not name.startswith('_'):
            del globals()[name]




























