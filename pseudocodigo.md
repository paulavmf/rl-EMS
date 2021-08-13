## a qué he llegago:
mediante runtime api establezco los momentos en los que quiero irrumpir en tiempo de ejeución

Irrumpo durante una simulación en con

a estos callbachs les declaro funciones e las que defino handles que serán los espacio en memoria a los que tendré acceso. Serán los sensores o actuadores.

estos handles que declare en python deberán ser variables globales


elegir callback, seguir con el mismo
hacer un algoritmo mínimo de decisión con este tema de la gente


## Primer caso de control:

### Posibles Actuators interesantes
¿qué era exactamente el SetPoint?
EnergyManagementSystem:Actuator Available,WEST ZONE,Zone Temperature Control,Heating Setpoint,[C]
EnergyManagementSystem:Actuator Available,WEST ZONE,Zone Temperature Control,Cooling Setpoint,[C]
EnergyManagementSystem:Actuator Available,EAST ZONE,Zone Temperature Control,Heating Setpoint,[C]
EnergyManagementSystem:Actuator Available,EAST ZONE,Zone Temperature Control,Cooling Setpoint,[C]

### Posibles Sensores Interesantes

Para empezar¡ puedo darle cosas previsibles y darles ruido y actuarlos 
ASí simulo una situación mucho más real
la cantidad de gente en la zona pueede ser la entrada (el environment)

El reward puede ser mantener la temperatura ambiente

Querre sacar cuenta tmb de estas variables:
Output:Variable,*,Zone People Occupant Count,hourly; !- Zone Average []
Output:Variable,*,Zone People Radiant Heating Energy,hourly; !- Zone Sum [J]
Output:Variable,*,Zone People Radiant Heating Rate,hourly; !- Zone Average [W]
Output:Variable,*,Zone People Convective Heating Energy,hourly; !- Zone Sum [J]
Output:Variable,*,Zone People Convective Heating Rate,hourly; !- Zone Average [W]
Output:Variable,*,Zone People Sensible Heating Energy,hourly; !- Zone Sum [J]
Output:Variable,*,Zone People Sensible Heating Rate,hourly; !- Zone Average [W]
Output:Variable,*,Zone People Latent Gain Energy,hourly; !- Zone Sum [J]
Output:Variable,*,Zone People Latent Gain Rate,hourly; !- Zone Average [W]
Output:Variable,*,Zone People Total Heating Energy,hourly; !- Zone Sum [J]
Output:Variable,*,Zone People Total Heating Rate,hourly; !- Zone Average [W]

aunque no en tiempo de ejecución


# Simulación

### Horas 0 - 23
### 4 simulaciones por hora

__IF FIRST TIME:__
## Primer step:
HORA = 0
STEP = 1
asigno handlers 
inicializo el número de personas
HEAT = 0
PEOPLE = INIT

## Segundo step:
ya con datos normales de heat y people puedo inicializar mi environment
HORA = 0
STEP = 2
HEAT = XXXX
PEOPLE= INI
Inicializo environment
Inicializo Q dictionary
inicializo stats
inicializo policy

step == 3 do nothing
step == 4 do nothing

__IF NOT FIRST TIME:__

CADA EPISODIO DURARÁ UN DÍA COMO MÁXIMO
IF HOUR == 0 AND step == 1:
    EMPIZA UN EPISODIO
----

# Q learning algorithm

## Q Learning

Q-Values or Action-Values: Q-values are defined for states and actions.
is an estimation of how good is it to take the action A at the state S. 
This estimation of Q(S, A) will be iteratively computed using the __TD- Update rule__

## Rewards y acciones

el agente empieza desde un estado inicial. En cada estado el escoge una acción y observa una recompensa y transita hacia
otro estado.


*** lo que me falta es decidir una serie de estados intermedios entre la acción escogida y la observación ***

## TD- Update rule (Temporal Difference)


__Esto se aplica cada vez que el agente interacciona con el environment.__

Q(S,A) <- Q(S,A) + \alpha(R + \gamma(S',A') - Q(S,A))

S: estado actual del agente
- heat y número de personas en step
A: Acción elegida según una policy
  
S': Siguiente estado
- (personas correspondientes a la acción y calor correspondientes a esas personas)
A': Mejor siguiente acción usando Q la estimación Q-values
  
R: Reward en ese step observado en respuesta a la acción A.
$\gamma$(>0 and <=1): Factor de descuento de los siguientes rewards. Q values es una estimación de los siguientes rewrds.
$\alpha$ : Step length taken to update the estimation of Q(S, A)
- esto no sé muy bien

## Choosing the Action to take using $\epsilon$-greedy policy:

Elige una acción usando la estimación de Q-values

con probabilid (1 - \epsilon ) elige la acción con el mayor Q value __exploitation__
con probabilidad \epsilon elige una acción random __exploration__


## Q Learning Algotithm
env, 
num_episodes, 
discount_factor = 1.0,
alpha = 0.6, epsilon = 0.1

- inicializo Q  : Action- Value function Q(S,A)
    A nested dictionary that maps:
    __state -> (action -> action-value)__
- inicializo Policy -> es la función que discirne entre la acción con la mejor Q value o una random
  
__for__ cada simulación:
*** cada episidio debería ser, por ejemplo, un invierno y repetir la simulación muchas veces ***
- inicializo environment
    - valores iniciales de people y heat ( en mi caso esa inicialización es la de la propia simulación __o sería
      empezar la simulación de nuevo??????__)
      
      __for__ cada step en simulación:
        action_probabilities= polycy(stado)
        elegir acción -> random choice de las acción teniendo encuenta las probabilidades
        next_state, reward, done? = step .... -> dependiendo de la acción encontraré un next_state 
        (que será el numero de gente, y el heat pero el heat no lo tendré hasta el step siguiente)
      
        #### TD Update:
        best_next_action = al mejor Q value según el siguiente estado
        td_target = reawrd * discount_factor*Q(next_state,best_action)
        td_delta = td_target - Q(state,action)
        if done:
            paso al siguiente episodio
        state = next_state
      
CADA EPISODIO SERÍA CADA SIMULACIÓN O CADA DÍA????

Un episodop por cada simulación:
- inicializar 


In episodio por cada día en circunstancias parecidas i.e invierno:













