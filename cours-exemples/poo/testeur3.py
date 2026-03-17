from essential import *

try :
    roms = ds_capteur.scan()            # scanne l'ensemble des capteurs
    print('Found DS devices: ', roms)   # affiche les codes ROM trouves
except :
    print('pas de capteur')

seuil_tp = 150

ancien_bpA = bpA.value()
ancien_bpB = bpB.value()
ancien_bpC = bpC.value()
ancien_bpD = bpD.value()

ancien_tp1 = tp1.read() < seuil_tp
ancien_tp2 = tp2.read() < seuil_tp
    
compt = 0 ; boucle_ms = 0 ; inc = 0 ; c = 10 ; led = 0 ; coef_neo = .6

while True :
    compt = compt + 1
    etat_bpA = bpA.value()
    etat_bpB = bpB.value()        
    etat_bpC = bpC.value()        
    etat_bpD = bpD.value()
    
    if not compt % 20 == 0 :
        display.fill_rect(0, 0, 127, 40, 0)
        display.text("Poussoirs ", 1, 0, 1)
        if etat_bpA : display.text("A", 80, 0, 1)
        if etat_bpB : display.text("B", 90, 0, 1)
        if etat_bpC : display.text("C", 100, 0, 1)
        if etat_bpD : display.text("D", 110, 0, 1)
        
        tension1 = p1.read()* 3.3/512     # calcul de la tension (9 bits)
        tension2 = p2.read()* 3.3/512     # calcul de la tension (9 bits)
        tension_ldr = ldr.read()* 3.3/512 # calcul de la tension (9 bits)
        display.text("Tens. ", 1, 21, 1)
        display.text(str(int(tension1*100)/100), 50, 21)
        display.text(str(int(tension2*100)/100), 90, 21)
        display.text("LDR ", 1, 31, 1)
        display.text(str(int(tension_ldr*100)/100), 90, 31)
        
    if (compt+8) % 20 == 0 : 
        try:
            ds_capteur.convert_temp()              # lance la lecture 
            print(compt, "         conversion")
        except :
            print('Pas de capteur')
    
    if (compt-1) % 1 == 0 : 
        display.fill_rect(0, 51, 127, 10, 0)
        display.text("Tps  ", 1, 51, 1)
        display.text(str(compt/10), 60, 51)
        display.text("s", 100, 51, 1)
    
    if compt % 20 == 0 : 
        try:
            print(compt, end="")
            for rom in roms:                       
            #print(rom)                      # affiche adresse ROM capteur    
                temperature = ds_capteur.read_temp(rom)
                print("          temperature : ",temperature)
                display.fill_rect(0, 41, 127, 10, 0)
                display.text("Temper ", 1, 41, 1)
                display.text( str(int(temperature*10)/10), 90, 41)
        except :
            print('Pas de capteur')    
    display.text("PinTouch ", 1, 10, 1)    

    etat_tp1 = tp1.read() < seuil_tp
    etat_tp2 = tp2.read() < seuil_tp
    
    if etat_tp1 : # j'appuie sur TP1
        display.text("1", 80, 11, 1)
        if compt % 4 ==0 : led_bleue.value(not led_bleue.value())
        if (compt -1) % 4 ==0 : led_verte.value(not led_verte.value())
        if (compt -2) % 4 ==0 : led_jaune.value(not led_jaune.value())
        if (compt -3) % 4 ==0 : led_rouge.value(not led_rouge.value())
    else : 
        led_bleue.value(bpA.value())
        led_verte.value(bpB.value())
        led_jaune.value(bpC.value())
        led_rouge.value(bpD.value())
    
    etat_bpA = bpA.value()
    etat_bpB = bpB.value()        
    etat_bpC = bpC.value()        
    etat_bpD = bpD.value()

    if etat_tp2 : # j'appuie sur TP2
        display.text("2", 90, 11, 1)
    
    if etat_tp2 and not ancien_tp2 :
        buzzer = PWM(Pin(5))
        buzzer.duty(100)
        print("                      HP ON")
    if not etat_tp2 and ancien_tp2 :
        buzzer.deinit()
        print("                      HP OFF")
        
    if etat_bpA and not ancien_bpA:
        buzzer.freq(liste_freq[0])
        for a in range(8):
            np[a] = (0, 0, int(3.99*(a+1)**2*coef_neo))  
        np.write()
    if etat_bpB and not ancien_bpB:
        buzzer.freq(liste_freq[4])
        for a in range(8):
            np[a] = (0, int(2.5*(a+1)**2*coef_neo), 0)  
        np.write()
    if etat_bpC and not ancien_bpC:
        buzzer.freq(liste_freq[7])
        for a in range(8):
            np[a] = (int(1.9*(a+1)**2*coef_neo), \
                     int(1.8*(a+1)**2*coef_neo), 0)  
        np.write()
    if etat_bpD and not ancien_bpD :
        buzzer.freq(liste_freq[11])
        for a in range(8):
            np[a] = (int(2.5*(a+1)**2*coef_neo), 0, 0)  
        np.write()
    if not (etat_bpA or etat_bpB or etat_bpC or etat_bpD):
        for a in range(8):
            np[a] = (0, 0, 0)  
        np.write()       

    ancien_bpA = etat_bpA    
    ancien_bpB = etat_bpB
    ancien_bpC = etat_bpC
    ancien_bpD = etat_bpD
    
    ancien_tp1  = etat_tp1
    ancien_tp2  = etat_tp2
    
    display.show() ; 
    synchro_ms(100)
