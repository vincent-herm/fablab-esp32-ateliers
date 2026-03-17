from machine import Pin, PWM
from time import sleep

f_init = 880
hp = PWM(Pin(5))
hp.duty(40)      # rapport cyclique a 40 sur 1023, soit environ 4%

gamme_majeure = [0, 2, 4, 5, 7, 9, 11, 12] # do re mi fa sol la si 
gamme_dorienne = [0, 2, 3, 5, 7, 9, 10, 12] # do re mib fa sol la sib
gamme_phrygienne = [0, 1, 3, 4, 6, 8, 10, 12] # do reb mib fa sol lab sib
gamme_lydienne = [0, 2, 4, 6, 7, 9, 11, 12] # do re mi fa# sol la si
gamme_mixolydienne = [0, 2, 4, 5, 7, 9, 10, 12] # do re mi fa sol la sib
gamme_eolienne = [0, 2, 3, 5, 7, 8, 10, 12] # do re mib fa sol lab sib
gamme_locrienne = [0, 1, 3, 5, 6, 8, 10, 12] # do reb mib fa solb lab sib

for rang, x in enumerate(gamme_lydienne):
    print("Rang : {0} - Note : {1}".format(rang, x))
    f = int(f_init * 2**(x/12))
    hp.freq(f)
    sleep(.2- .08* (rang % 2 == 1))        
hp.deinit()