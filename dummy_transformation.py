import time
from random import randint

def set_people():
    output = randint(0,10)
    print(f"Transforming input {''} to {output} by summy transform")
    print("witing 5s... to follow execution. checking linealaty in execution")
    time.sleep(0.5)
    return output

def simple_decision_people(radiant):
    if radiant>=0 and radiant<=500:
        return float(50.0)
    elif radiant>500 and radiant<700:
        return float(10.0)
    elif radiant>700:
        return float(0.0)

# TODO DE VERDAD CHECKEAR LINEALIDAD



