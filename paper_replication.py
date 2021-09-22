import os
import sys
sys.path.insert(0, '/usr/local/EnergyPlus-9-4-0')

from pyenergyplus.api import EnergyPlusAPI
import matplotlib.style
from ep_helpers.handler import rl_handler
from environments.power_consumption_opt import Power_Consumption_Op, plot_power_opt_stats



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
    [{"variable_name" : u"Zone Mean Air Temperature","variable_key":u"WEST ZONE","name": "WestZoneTemp"},
     {"variable_name": "Facility Total Building Electricity Demand Rate","variable_key": "Whole Building", "name": "IT_Equip_Power" },
    {"variable_name": "Facility Total Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_Building_Power" },
    {"variable_name": "Facility Total HVAC Electricity Demand Rate","variable_key": "Whole Building", "name": "Whole_HVAC_Power" }
           ]


# hay más actuadores pero voy a dejarlo así por ahora
# West Zone setpoint temperature between10ºC and 40ºC
# este actuator existe
actuators =[{"component_type":"System Node Setpoint",
             "control_type": "Temperature Setpoint",
             "actuator_key":"West Zone DEC Outlet Node",
             "name":"WestZoneDECOutletNode_setpoint" }]


if __name__ == '__main__':
    # final_stats = plotting.EpisodeStats(
    #     episode_lengths=list(),
    #     episode_rewards=list(),
    #     people=list(),
    #     peopleheat=list()
    # )
    api = EnergyPlusAPI()
    handler = rl_handler(api, Power_Consumption_Op,actuators,sensors,'/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/paper_replication')
    for _ in range(1):
        state = api.state_manager.new_state()
        print("this is called only once")
        api.runtime.callback_end_zone_timestep_after_zone_reporting(state, handler.Qlearning)
        for sensor in sensors:
            api.exchange.request_variable(state, sensor["variable_name"], sensor["variable_key"])

        # trim off this python script name when calling the run_energyplus function so you end up with just
        # the E+ args, like: -d /output/dir -D /path/to/input.idf

        api.runtime.run_energyplus(state, ['-d', output,'-w', epwfile, idffile])
        # with open(f"/home/paula/Documentos/Doctorado/Desarrollo/rl-cacharreo/qtable_no_rwd.pickle", "wb") as f:
        #     pickle.dump(dict(Q), f)

        api.state_manager.reset_state(state)
        one_time = True
        first_step = True

    # añadí esto para borrar las variables globales.
    # realmente no sé si hace alguna diferencia
    from ep_helpers.handler import stats
    plot_power_opt_stats(stats)
    for name in dir():
        if not name.startswith('_'):
            del globals()[name]




























