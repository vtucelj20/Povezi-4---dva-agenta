from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from spade import quit_spade

import argparse
import json
import random
from time import sleep


class Igrac(Agent):
    """Sudionik u igri."""

    retci = 6
    stupci = 7

    def __init__(self, *args, vrsta, suigrac, provjeraPobjedeSuigraca,**kwargs):
        super().__init__(*args, **kwargs)
        self.suigrac = suigrac
        self.mojaPloca = [
                            [0, 0, 0, 0, 0, 0, 0], 
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0]
                         ]
        self.vrsta = vrsta
        self.provjeraPobjedeSuigraca = provjeraPobjedeSuigraca

    class InicijalniKorak(OneShotBehaviour):
        """Slanje ploče s prvim odigranim korakom."""

        async def run(self):
            prviPotez = self.agent.randomBroj()

            plocaP = [
                            [0, 0, 0, 0, 0, 0, 0], 
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0]
                         ]

            """plocaP = [
                            [0, 0, 0, 0, 0, 0, 0], 
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0, 0],
                            [0, 1, 0, 2, 0, 0, 0],
                            [2, 2, 1, 1, 0, 1, 0]
                         ]"""
            
            self.agent.mojaPloca = self.agent.popuniPolje(prviPotez, 1, plocaP)
            msg = Message(
                to=self.agent.suigrac,
                metadata={"ontology": "igra"},
                body=f"{self.agent.mojaPloca}")
            self.agent.say(f"Šaljem svoj prvi odigrani potez: {prviPotez}")
            self.agent.printajMatricu(self.agent.mojaPloca)
            await self.send(msg)

    class Igranje(CyclicBehaviour):
        """Ponašanje koje vodi proces igre i obrađuje poruke i poteze iz procesa igre."""

        async def run(self):
            msg = Message()
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body in ["odbij", "pobjeda"]:
                    self.agent.say(f"Suigrač kaže: {msg.body}")
                    await self.agent.stop()
                else:
                    self.agent.say(f"Dobio sam plocu: ")
                    poruka_Body = json.loads(msg.body)
                    self.agent.printajMatricu(poruka_Body)
                    ploca = json.loads(msg.body)
                    sleep(3)
                    interpretacija = self.interpretirajPlocu(ploca)

                    msg = msg.make_reply()

                    if interpretacija in ["odbij", "pobjeda"]:
                        msg.body = interpretacija
                        await self.send(msg)
                        await self.agent.stop()
                    else:
                        msg.body = f"{interpretacija}"
                        await self.send(msg)

        def interpretirajPlocu(self, ploca):
            if self.provjeri_plocu(ploca) == True:
                self.agent.say(f"Odbijam igru zbog pune ploče: ")
                self.agent.printajMatricu(ploca)
                return "odbij"
            else:
                self.agent.potez += 1
                print(f"# {self.agent.potez}")
                self.agent.mojaPloca = self.generirajPlocu(ploca)
                if self.agent.vrsta in ["zuti", "z"]:
                    if self.evaluiraj(self.agent.mojaPloca, 1):
                        self.agent.say(f"Pobjedio sam: ")
                        self.agent.printajMatricu(self.agent.mojaPloca)
                        return "pobjeda"
                    else:
                        self.agent.printajMatricu(self.agent.mojaPloca)
                        return self.agent.mojaPloca
                else:
                    if self.evaluiraj(self.agent.mojaPloca, 2):
                        self.agent.say(f"Pobjedio sam: ")
                        self.agent.printajMatricu(self.agent.mojaPloca)
                        return "pobjeda"
                    else:
                        self.agent.printajMatricu(self.agent.mojaPloca)
                        return self.agent.mojaPloca


        #Funkcija za evaluaciju ploče
        def evaluiraj(self, ploca, boja_zetona):
            if self.agent.pobjeda(ploca, boja_zetona):
                return 1
            else: 
                return 0


        #Funkcija za generiranje novog poteza i update ploče
        def generirajPlocu(self, ploca):
            generiranaPloca = ploca

            if self.agent.vrsta in ["zuti", "z"]:
                #žuti random bira brojeve od 1 do 7 za ubacivanje žetona 
                potezRandom = self.agent.randomBroj()
                if self.agent.odabir_je_dobar(ploca, potezRandom) == 0:
                    print(f"Taj stupac {potezRandom} je već popunjeni! Odaberi neki drugi stupac za ispuštanje žetona.")
                    while self.agent.odabir_je_dobar(ploca, potezRandom) == 0:
                        potezRandom = self.agent.randomBroj()
                    self.agent.say(f"Igram svoj potez: {potezRandom}")
                    plocaP = self.agent.popuniPolje(potezRandom, 1, ploca)
                    generiranaPloca = plocaP
                else:
                    self.agent.say(f"Igram svoj potez: {potezRandom}")
                    plocaP = self.agent.popuniPolje(potezRandom, 1, ploca)
                    generiranaPloca = plocaP
            else:
                #crveni koristi scoring za odabir stupca
                #provjera dobrog odabira (stupac nije pun) odrađena u funkciji za generiranje poteza
                potezScoring = self.agent.generirajPotez_Scoring(ploca)
                self.agent.say(f"Igram svoj potez: {potezScoring}")
                plocaP = self.agent.popuniPolje(potezScoring, 2, ploca)
                generiranaPloca = plocaP

            return generiranaPloca

        #Funkcija za provjeru da li je ploča puna
        def provjeri_plocu(self, ploca):
            puna = True

            for i in range(self.agent.retci):
                for j in range(self.agent.stupci):
                    if ploca[i][j] == 0:
                        puna = False

            return puna


    #Funkcija za ispis s imenom, tj. bojom žetona igrača
    def say(self, msg):
        print(f"{self.name}: {msg}")


    #Funkcija za ispis ploče u obliku matrice
    def printajMatricu(self,matrica):
        for row in matrica:
                redak = " ".join(str(element) for element in row)
                print(f" {redak}")
        print("\n")


    #Funkcija za generiranje random broja
    def randomBroj(self):
        randBroj = random.randint(1, self.stupci)
        return randBroj


    #Funkcija za odabir stupca korištenjem scoringa (crveni tako igra)
    def generirajPotez_Scoring(self, ploca):
        potezStupac = 0
        najboljiRezultat = 0
        puniStupac = False
        
        for column in range(self.stupci):
            rezultat = 0
            igrani_redak = 0
            testnaPloca = [row[:] for row in ploca]
            testnaPloca1 = [row[:] for row in ploca]

            #popuni trenutni stupac za testiranje i dodjelu rezultata tom stupcu
            for row in range(self.retci):
                if row == 0 and testnaPloca[row][column] != 0:
                    puniStupac = True
                    break
                elif row < 5:
                    if testnaPloca[row][column] != 0:
                        testnaPloca[row - 1][column] = 2
                        if self.provjeraPobjedeSuigraca == "da":
                            testnaPloca1[row - 1][column] = 1
                        igrani_redak = row - 1
                        break
                else:
                    if testnaPloca[row][column] != 0:
                        testnaPloca[row - 1][column] = 2
                        if self.provjeraPobjedeSuigraca == "da":
                            testnaPloca1[row - 1][column] = 1
                        igrani_redak = row - 1
                    else:
                        testnaPloca[row][column] = 2
                        if self.provjeraPobjedeSuigraca == "da":
                            testnaPloca1[row][column] = 1
                        igrani_redak = row

            if puniStupac != True:
                self.printajMatricu(testnaPloca)

                #dodaj 100 bodova ako dolazi do pobjede
                if self.pobjeda(testnaPloca, 2):
                    print(f"plus 100")
                    rezultat += 100

                #dodaj 10 bodova ako je srednji stupac
                if column == 3:
                    print(f"plus 10")
                    rezultat += 10

                #dodaj po 2 boda za svaku liniju od 2 žetona
                rezultatZa2 = self.provjeri2(testnaPloca, column, igrani_redak) 
                if rezultatZa2 > 0:
                    rezultat += rezultatZa2

                #dodaj po 3 boda za svaku liniju od 3 žetona
                rezultatZa3 = self.provjeri3(testnaPloca, column, igrani_redak)
                if rezultatZa3 > 0:
                    rezultat += rezultatZa3

                #ako je odabrano da želimo gledati i mogućnost pobjede suigrača u sljedećem koraku
                if self.provjeraPobjedeSuigraca == "da":
                    if self.pobjeda(testnaPloca1, 1):
                        print(f"plus 50")
                        rezultat += 50

                #provjeri je li rezultat stupca veći od trenutno najvećeg zapamćenog rezultata
                print(f"Rezultat: {rezultat}\n")
                if rezultat >= najboljiRezultat:
                    najboljiRezultat = rezultat
                    potezStupac = column + 1
            else:
                print(f"Stupac {column + 1} je pun! Tražim dalje!")
                puniStupac = False

        return potezStupac


    #Funkcija za provjeru čini li odabir liniju od dva crvena (broj 2)žetona za pobjedu
    def provjeri2(self, ploca, igrani_stupac,igrani_redak):
        rezultat2 = 0

        #boja žetona stavljena kao 4 samo da se razlikuje u provjerama --> zna se koji uvjet koristiti
        if self.horizontalna_linija(ploca, 4, igrani_stupac, igrani_redak) == 1:
            print(f"plus horizontalan 2")
            rezultat2 += 2

        if self.vertikalna_linija(ploca, 4, igrani_stupac, igrani_redak) == 1:
            print(f"plus vertikalan 2")
            rezultat2 += 2

        if self.dijagonalna_linija(ploca, 4, igrani_stupac, igrani_redak) == 1:
            print(f"plus dijagonalan 2")
            rezultat2 += 2

        return rezultat2


    #Funkcija za provjeru čini li odabir liniju od tri crvena (broj 2) žetona za pobjedu
    def provjeri3(self, ploca, igrani_stupac, igrani_redak):
        rezultat3 = 0

        #boja žetona stavljena kao 5 samo da se razlikuje u provjerama --> zna se koji uvjet koristiti
        if self.horizontalna_linija(ploca, 5, igrani_stupac, igrani_redak) == 1:
            print(f"plus horizontalan 3")
            rezultat3 += 3

        if self.vertikalna_linija(ploca, 5, igrani_stupac, igrani_redak) == 1:
            print(f"plus vertikalan 3")
            rezultat3 += 3

        if self.dijagonalna_linija(ploca, 5, igrani_stupac, igrani_redak) == 1:
            print(f"plus dijagonalan 3")
            rezultat3 += 3

        return rezultat3


    #Funkcija za provjeru točnosti unosa i da li taj stupac još ima slobodnih mjesta
    def odabir_je_dobar(self, ploca, odabir):
        if ploca[0][odabir - 1] != 0:
            return 0
        else:
            return 1


    #Funkcija za provjeru da li je došlo do horizontalne pobjede
    def horizontalna_pobjeda(self, ploca, boja_zetona):
        zastavica = 0

        for i in range(self.retci):
            for j in range(self.stupci - 3):
                if ploca[i][j] == boja_zetona and ploca[i][j + 1] == boja_zetona and ploca[i][j + 2] == boja_zetona and \
                ploca[i][j + 3] == boja_zetona:
                    zastavica = 1
                    break

        return zastavica

    #Funkcija za provjeru da li je došlo do horizontalne linije od 2 ili 3 žetona
    def horizontalna_linija(self, ploca, boja_zetona, igrani_stupac, igrani_redak):
        zastavica = 0

        #provjera za 2 u liniji
        if boja_zetona == 4:
            if igrani_stupac > 0 and igrani_stupac < self.stupci - 1:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac + 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac - 1] == 2 and ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    
            elif igrani_stupac == 0:
                if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac + 1] == 2:
                    zastavica = 1
                    
            else:
                if ploca[igrani_redak][igrani_stupac - 1] == 2 and ploca[igrani_redak][igrani_stupac] == 2:
                    zastavica = 1
                    


        #provjera za 3 u liniji
        elif boja_zetona == 5:
            if igrani_stupac > 1 and igrani_stupac < self.stupci - 2:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac + 1] == 2 and \
                    ploca[igrani_redak][igrani_stupac + 2] == 2) or (ploca[igrani_redak][igrani_stupac - 2] == 2 and \
                    ploca[igrani_redak][igrani_stupac - 1] == 2 and ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    
            elif igrani_stupac == 0 or igrani_stupac == 1:
                if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac + 1] == 2 and \
                ploca[igrani_redak][igrani_stupac + 2] == 2:
                    zastavica = 1
                    
            elif igrani_stupac == self.stupci - 1 or igrani_stupac == self.stupci - 2:
                if ploca[igrani_redak][igrani_stupac - 2] == 2 and ploca[igrani_redak][igrani_stupac - 1] == 2 and \
                ploca[igrani_redak][igrani_stupac] == 2:
                    zastavica = 1

            if igrani_stupac > 0 and igrani_stupac < self.stupci - 1:
                if ploca[igrani_redak][igrani_stupac - 1] == 2 and ploca[igrani_redak][igrani_stupac] == 2 and \
                ploca[igrani_redak][igrani_stupac + 1] == 2:
                    zastavica = 1
                    

        return zastavica


    #Funkcija za provjeru da li je došlo do vertikalne pobjede ili vertikalne linije 2 ili 3 žetona
    def vertikalna_pobjeda(self, ploca, boja_zetona):
        zastavica = 0

        #provjera pobjede
        for i in range(self.stupci):
            for j in range(self.retci - 3):
                if ploca[j][i] == boja_zetona and ploca[j + 1][i] == boja_zetona and ploca[j + 2][i] == boja_zetona and \
                ploca[j + 3][i] == boja_zetona:
                    zastavica = 1
                    break

        return zastavica


    #Funckija za provjeru da li je došlo do vertikalne linije od 2 ili 3 žetona
    def vertikalna_linija(self, ploca, boja_zetona, igrani_stupac, igrani_redak):
        zastavica = 0

        #provjera za 2 u liniji
        if boja_zetona == 4:
            if igrani_redak > 0 and igrani_redak < self.retci - 1:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac] == 2) or \
                (ploca[igrani_redak - 1][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    
            elif igrani_redak == 0:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac] == 2):
                    zastavica = 1
                    
            else:
                if (ploca[igrani_redak - 1][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    

        #provjera za 3 u liniji
        elif boja_zetona == 5:
            if igrani_redak > 1 and igrani_redak < self.retci - 2:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac] == 2 and \
                    ploca[igrani_redak + 2][igrani_stupac] == 2) or (ploca[igrani_redak][igrani_stupac - 2] == 2 and \
                    ploca[igrani_redak - 1][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    
            elif igrani_redak == 0 or igrani_redak == 1:
                if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac] == 2 and \
                ploca[igrani_redak + 2][igrani_stupac] == 2:
                    zastavica = 1
                    
            elif igrani_redak == self.retci - 1 or igrani_redak == self.retci - 2:
                if (ploca[igrani_redak - 2][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac] == 2 and \
                    ploca[igrani_redak][igrani_stupac] == 2):
                    zastavica = 1
                    

            if igrani_redak > 0 and igrani_redak < self.retci - 1:
                if (ploca[igrani_redak - 1][igrani_stupac] == 2 and ploca[igrani_redak][igrani_stupac] == 2 and \
                    ploca[igrani_redak + 1][igrani_stupac] == 2):
                    zastavica = 1
                    

        return zastavica

    #Funkcija za provjeru da li je došlo do dijagonalne pobjede
    def dijagonalna_pobjeda(self, ploca, boja_zetona):
        zastavica = 0

        #s lijeva na desno
        for i in range(self.retci - 3):
            for j in range(self.stupci - 3):
                if ploca[i][j] == boja_zetona and ploca[i + 1][j + 1] == boja_zetona and ploca[i + 2][j + 2] == boja_zetona and \
                ploca[i + 3][j + 3] == boja_zetona:
                    zastavica = 1
                    break

        #s desna na lijevo
        for i in range(3, self.retci):
            for j in range(self.stupci - 3):
                if ploca[i][j] == boja_zetona and ploca[i - 1][j + 1] == boja_zetona and ploca[i - 2][j + 2] == boja_zetona and \
                ploca[i - 3][j + 3] == boja_zetona:
                    zastavica = 1
                    break

        return zastavica

    #Funkcija za provjeru da li je došlo do dijagonalne linije od 2 ili 3 žetona
    def dijagonalna_linija(self, ploca, boja_zetona, igrani_stupac, igrani_redak):
        zastavica = 0

        #provjera za 2 u liniji
        if boja_zetona == 4:
            if igrani_stupac > 0 and igrani_redak > 0 and igrani_stupac < self.stupci - 1 and igrani_redak < self.retci - 1:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac + 1] == 2) or \
                (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac - 1] == 2) or \
                (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac - 1] == 2) or \
                (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac + 1] == 2):
                    zastavica = 1
                    
            elif igrani_stupac == 0:
                if igrani_redak == 0:
                    if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac + 1] == 2:
                        zastavica = 1
                        
                elif igrani_redak == self.retci - 1:
                    if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac + 1] == 2:
                        zastavica = 1
                        
                else:
                    if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac + 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac + 1] == 2):
                        zastavica = 1
                        
            elif igrani_stupac == self.stupci - 1:
                if igrani_redak == 0:
                    if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac - 1] == 2:
                        zastavica = 1
                        
                elif igrani_redak == self.retci - 1:
                    if ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac - 1] == 2:
                        zastavica = 1
                        
                else:
                    if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac - 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac - 1] == 2):
                        zastavica = 1
                        
            elif igrani_redak == 0:
                if igrani_stupac > 0 and igrani_stupac < self.stupci - 1:
                    if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac - 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak + 1][igrani_stupac + 1] == 2):
                        zastavica = 1
                        
            elif igrani_redak == self.retci - 1:
                if igrani_stupac > 0 and igrani_stupac < self.stupci - 1:
                    if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac - 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac + 1] == 2):
                        zastavica = 1
                    

        #provjera za 3 u liniji
        elif boja_zetona == 5:
            
            brojac = 1
            r = igrani_redak - 1
            c = igrani_stupac - 1
            while r >= 0 and c >= 0 and ploca[r][c] == 2:
                brojac += 1
                if brojac == 3:
                    zastavica = 1
                r -= 1
                c -= 1

            brojac = 1
            r = igrani_redak + 1
            c = igrani_stupac + 1
            while r < self.retci and c < self.stupci and ploca[r][c] == 2:
                brojac += 1
                if brojac == 3:
                    zastavica = 1
                r += 1
                c += 1

            brojac = 1
            r = igrani_redak + 1
            c = igrani_stupac - 1
            while r < self.retci and c >= 0 and ploca[r][c] == 2:
                brojac += 1
                if brojac == 3:
                    zastavica = 1
                r += 1
                c -= 1

            brojac = 1
            r = igrani_redak - 1
            c = igrani_stupac + 1
            while r >= 0 and c < self.stupci and ploca[r][c] == 2:
                brojac += 1
                if brojac == 3:
                    zastavica = 1
                r -= 1
                c += 1

            if igrani_redak > 0 and igrani_stupac > 0 and igrani_redak < self.retci - 1 and igrani_stupac < self.stupci - 1:
                if (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac - 1] == 2 and  \
                    ploca[igrani_redak + 1][igrani_stupac + 1] == 2) or \
                    (ploca[igrani_redak][igrani_stupac] == 2 and ploca[igrani_redak - 1][igrani_stupac + 1] == 2 and  \
                    ploca[igrani_redak + 1][igrani_stupac - 1] == 2):
                    zastavica = 1


        return zastavica


    #Funkcija za provjeru da li je došlo do pobjede
    def pobjeda(self, ploca, boja_zetona):
        if self.horizontalna_pobjeda(ploca, boja_zetona) or \
        self.vertikalna_pobjeda(ploca, boja_zetona) or \
        self.dijagonalna_pobjeda(ploca, boja_zetona):
            return 1
        else:
            return 0


    #Funkcija za popunjavanje odabranog polja
    def popuniPolje(self, odabir, boja_zetona, ploca):
        novaPloca = ploca

        #traži prvo slobodno mjesto/prvi redak s 0 u odabranom stupcu 
        for i in range(self.retci):
            if ploca[i][odabir - 1] == 0:
                slobodno = i

        #postavi 'žeton'
        novaPloca[slobodno][odabir - 1] = boja_zetona

        return novaPloca


    async def setup(self):
        self.say("Spreman sam!")
        self.potez = 0

        ponasanjeIgranje = self.Igranje()
        predlozakIgranje = Template(metadata={"ontology": "igra"})
        self.add_behaviour(ponasanjeIgranje, predlozakIgranje)

        if self.vrsta in ["zuti", "z"]:
            ponasanjeInicijalniKorak = self.InicijalniKorak()
            self.add_behaviour(ponasanjeInicijalniKorak)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Primjer pokretanja: %(prog)s -v z -s crveni@localhost -jid zuti@localhost -pwd tajna")
    parser.add_argument("-v", "--vrsta", type=str, help="Vrsta agenta (z ili c)")
    parser.add_argument("-s", "--suigrac", type=str, help="JID prodavača", default="crveni@localhost")
    parser.add_argument("-jid", type=str, help="JID agenta")
    parser.add_argument("-pwd", type=str, help="Lozinka agenta", default="tajna")
    parser.add_argument("-pps", type=str, help="Želim koristiti i provjeru pobjede suigrača u sljedećem koraku")
    args = parser.parse_args()

    agent = Igrac(args.jid, args.pwd, vrsta=args.vrsta, provjeraPobjedeSuigraca=args.pps, suigrac=args.suigrac)
    future = agent.start()
    future.result()

    while agent.is_alive():
        try:
            sleep(10)
        except KeyboardInterrupt:
            agent.stop()
            break

    quit_spade()
