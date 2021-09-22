## Pop Zone Heat_1:

### Reward
Variable Reward: Calor desprendido por la gent

if 10000 <= people_heat <= 12000:
    self.reward = 50
    self.n_done += 0
elif people_heat < 0:
    self.reward = -100
else:
    self.reward = -1

1 rep:

10 repeticiones:


reward 1 y sin acumulación de done


## PopZoneHeat_1:

__He cerrado muchísimo más el rango para ver qué pasa__

if 10000 <= people_heat <= 10500:
    self.reward = 50
    self.n_done += 1
elif people_heat < 0:
    self.reward = -100
else:
    self.reward = -1


1 repeteción:
En el caso de una repetición, empieza bien pero pronto cae ene l caos.


## Reinforcement Learning Testbed for Power-Consumption Optimization: 18thAsia Simulation Conference, AsiaSim 2018, Kyoto, Japan, October 27–29, 2018,Proc


En  2ZoneDataCenterHVAC_wEconomizer.idf 
#### Actuator 





