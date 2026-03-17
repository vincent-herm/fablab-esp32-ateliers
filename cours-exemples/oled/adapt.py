def  adaptEchelle(e, e1, e2, s1, s2) :     
    """ Cette fonction ... """
    s = (e - e1) * (s2 - s1) / (e2 - e1) + s1  # e : entree , s : sortie
    return s                                   # renvoie la valeur sortie
        
print("sortie s : ", adaptEchelle(-0.6, -1, 1, 60, 4))