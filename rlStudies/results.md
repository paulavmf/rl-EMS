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
