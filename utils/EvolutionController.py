from utils.Player import Player
from utils.settings import *
import pygame
import math

class EvolutionController:
    def __init__(self, taillePopulation=20, taillePopulationMutate=9, taillePopulationBest=1):
        self.taillePopulation = taillePopulation
        self.taillePopulationMutate = taillePopulationMutate
        self.taillePopulationBest = taillePopulationBest
        self.taillePopulationRandom = self.getTaillePopulationRandom()

        self.generation = 0

        self.populationAlive = []
        self.populationDead = []

        self.font = pygame.font.Font(None, 30)
        self.font_sm = pygame.font.Font(None, 24)

    def getTaillePopulationRandom(self) -> int:
        ''' return size of random population '''
        return self.taillePopulation - self.taillePopulationMutate - self.taillePopulationBest

    def getBestPlayer(self) -> Player:
        ''' get the best player for the generation '''
        return max(self.populationDead, key=lambda item: item.score)

    def getNumberOfAlive(self) -> int:
        return len(self.populationAlive)

    def getNumberOfDead(self) -> int:
        return len(self.populationDead)

    def generateFirstPopulation(self):
        ''' generate a population of player of size taillePopulation '''
        for i in range(self.taillePopulation):
            self.populationAlive.append(Player(350, -1000))

    def allPlayerAreDead(self) -> bool:
        if self.getNumberOfAlive():
            return False
        return True

    def killPlayer(self, index):
        ''' kill a player with index and add him to deadPopulation '''
        deadPlayer = self.populationAlive.pop(index)
        self.populationDead.append(deadPlayer)

    def startNextGeneration(self):
        bestPlayer = self.getBestPlayer()

        self.populationAlive.append(bestPlayer)
        while len(self.populationAlive) <= self.taillePopulation:
            self.populationAlive.append(Player(350, -1000))

        self.generation += 1
        self.populationDead.clear()

        print(
            f"Generation {self.generation}   -   player alive : {self.getNumberOfAlive()}")

    def displayText(self, screen):
        generationText = self.font.render("Generation: " + str(self.generation), True, (255, 0, 0))
        screen.blit(generationText, (0,0))

        aliveText = self.font.render("Alive: " + str(self.getNumberOfAlive()), True, (255,0, 0))
        screen.blit(aliveText, (0,20))

        self.populationAlive.sort(key= lambda x: x.score, reverse=True) # sort by score

        for i in range(20):
            try:
                txt = self.font_sm.render(str(i+1) + " - " + self.populationAlive[i].name + " : " + str(round(self.populationAlive[i].score)), True, (255,0,0))
                screen.blit(txt, (0,50 +  i * 15))
            except:
                pass
            
