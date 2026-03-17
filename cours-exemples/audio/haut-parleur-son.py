from  machine import * # on importe toutes les classes du module machine
from time import sleep

hp = PWM(Pin(5))       # creation de l'instance hp de la classe PWM
hp.duty(0)             # rapport cyclique 0 sur 1023 : on arrete le son

frequence = int(input("Quelle frequence voulez-vous generer ? : ")) 

hp.duty(40)            # rapport cyclique a 40 sur 1023, soit environ 4%
hp.freq(frequence)     # la frequence est mise a la valeur choisie
sleep(1)               # on genere le signal durant une seconde
hp.deinit()            # on libere les ressources du PWM -> arret 
    

