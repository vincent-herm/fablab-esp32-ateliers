from  machine import *
from time import sleep

hp = PWM(Pin(5)) 
hp.duty(40)          # rapport cyclique a 40 sur 1023, soit environ 4%

#  creation d'une liste en comprehension de 13 notes (suite geometrique)
liste_freq = [int(2**(x/12)*880) for x in range (0,13)]  
print("Liste des frequences : ", liste_freq)   # affichage des 13 notes

for compt, x in enumerate(liste_freq) :
    print("Note {0:2d} - frequence : {1:4d} Hz".format(compt, x))
    hp.freq(x)
    sleep(.2 - .08 * (compt % 2 != 0))   # creation du swing
hp.deinit()