from utils.Player import Player
from utils.settings import *
import pygame
import math
import sys


class EvolutionController:
    def __init__(self, taillePopulation=20, taillePopulationMutate=9, taillePopulationBest=1, displaySprites=True):
        self.taillePopulation = taillePopulation
        self.taillePopulationMutate = taillePopulationMutate
        self.taillePopulationBest = taillePopulationBest
        self.taillePopulationRandom = self.getTaillePopulationRandom()

        self.generation = 1

        self.populationAlive = []
        self.populationDead = []

        self.font = pygame.font.Font(None, 30)
        self.font_sm = pygame.font.Font(None, 24)

        self.displaySprites = displaySprites

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
            self.populationAlive.append(
                Player(displaySprites=self.displaySprites))

    def allPlayerAreDead(self) -> bool:
        if self.getNumberOfAlive():
            return False
        return True

    def killPlayer(self, index):
        ''' kill a player with index and add him to deadPopulation '''
        deadPlayer = self.populationAlive.pop(index)
        self.populationDead.append(deadPlayer)

    def sortPopulationByScore(self, populationArray: [Player]):
        ''' sort either populationAlive or populationDead by score '''
        populationArray.sort(key=lambda x: x.score, reverse=True)

    def selectBestPlayers(self) -> [Player]:
        ''' returns the n best player defined by self.taillePopulationBest '''
        bestPlayers = []
        self.sortPopulationByScore(self.populationDead)
        for i in range(self.taillePopulationBest):
            best = self.populationDead[i]
            bestPlayers.append(best)
        return bestPlayers

    def mutateWeights(self, weights):
        return weights

    def mutate(self, selectedBestPlayers) -> [Player]:
        mutatedPopulation = []
        if self.taillePopulationMutate < self.taillePopulationBest:
            print("Le nombre de fils mutés doit être supérieur ou égal au nombre de bestJoueurs sélectionné (self.taillePopulationBest<self.taillePopulationMutate)")
            sys.exit()

        numberChildPerBestPlayer: int = self.taillePopulationMutate // self.taillePopulationBest
        numberRemainderChild: int = self.taillePopulationMutate % self.taillePopulationBest

        for bestPlayer in selectedBestPlayers:
            for i in range(numberChildPerBestPlayer):
                weights = bestPlayer.getWeights()
                weights = self.mutateWeights(weights)
                tmpPlayer = Player(displaySprites=self.displaySprites)
                tmpPlayer.setWeights(weights)
                mutatedPopulation.append(tmpPlayer)

        for i in range(numberRemainderChild):
            weights = selectedBestPlayers[0].getWeights()
            weights = self.mutateWeights(weights)
            tmpPlayer = Player(displaySprites=self.displaySprites)
            tmpPlayer.setWeights(weights)
            mutatedPopulation.append(tmpPlayer)

        return mutatedPopulation

    def startNextGeneration(self):
        self.generation += 1
        bestPlayers = self.selectBestPlayers()
        mutatedPlayers = self.mutate(bestPlayers)
        self.populationDead.clear()

        for player in bestPlayers:
            weights = player.getWeights()
            oldName = player.name

            newPlayer = Player(
                name=oldName, displaySprites=self.displaySprites)
            newPlayer.setWeights(weights)
            newPlayer.bestPlayer = True

            self.populationAlive.append(newPlayer)

        for player in mutatedPlayers:
            tmpPlayer = player
            tmpPlayer.mutatedPlayer = True
            self.populationAlive.append(tmpPlayer)

        while self.getNumberOfAlive() < self.taillePopulation:
            self.populationAlive.append(
                Player(displaySprites=self.displaySprites))

    def displayText(self, screen):
        generationText = self.font.render(
            "Generation: " + str(self.generation), True, (255, 0, 0))
        screen.blit(generationText, (0, 0))

        aliveText = self.font.render(
            "Alive: " + str(self.getNumberOfAlive()), True, (255, 0, 0))
        screen.blit(aliveText, (0, 20))

        self.sortPopulationByScore(self.populationAlive)

        for index, player in enumerate(self.populationAlive):
            if(index > 30):
                break
            if player.bestPlayer:
                txt = self.font_sm.render(str(
                    index+1) + " - " + player.name + " : " + str(round(player.score)), True, (255, 0, 0))
            elif player.mutatedPlayer:
                txt = self.font_sm.render(str(
                    index+1) + " - " + player.name + " : " + str(round(player.score)), True, (0, 255, 0))
            else:
                txt = self.font_sm.render(str(
                    index+1) + " - " + player.name + " : " + str(round(player.score)), True, (0, 0, 255))

            screen.blit(txt, (0, 50 + index * 15))
