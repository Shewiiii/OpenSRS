from datetime import datetime, timedelta, UTC
from fsrs import *

#https://github.com/open-spaced-repetition/py-fsrs
#truc temporaire pour me repérer
f = FSRS()
card = Card() #définit ma nouvelle carte
now = datetime.now(UTC) #définit quand review cette nouvelle carte (mtn ici)
scheduling_cards = f.repeat(card, now) #définit les intervalles de répétition futures
card = scheduling_cards[Rating.Good].card #met dans la variable carte cette même carte mais avec l'intervalle celui correspondant au rating "good"
now = card.due #met dans la variable "now" le datetime mais du jour où cette carte va revenir
scheduling_cards = f.repeat(card, now) #définit les intervalles de répétition futures

liste = []

#core 2k : (0.2458, 1.7517, 3.6668, 15.2497, 5.0366, 1.4023, 1.0596, 0.0299, 1.7953, 0.1, 1.1838, 2.2312, 0.0384, 0.3658, 1.4031, 0.363, 2.8899)
#194/sentence mining ? : (1.14, 1.01, 5.44, 14.67, 5.3024, 1.5662, 1.2503, 0.0028, 1.5489, 0.1763, 0.9953, 2.7473, 0.0179, 0.3105, 0.3976, 0.0, 2.0902) 
#default: (0.4,0.6,2.4,5.8,4.93,0.94,0.86,0.01,1.49,0.14,0.94,2.18,0.05,0.34,1.26,0.29,2.61)
#jpdb : (0.3035, 4.7433, 8.8727, 45.4892, 4.9939, 1.5012, 0.755, 0.0, 1.6041, 0.1, 1.0249, 2.2375, 0.0419, 0.3747, 1.0551, 0.2335, 3.3913)
class Carte:
    listeCartes = []
    f.p.w = (0.3035, 4.7433, 8.8727, 45.4892, 4.9939, 1.5012, 0.755, 0.0, 1.6041, 0.1, 1.0249, 2.2375, 0.0419, 0.3747, 1.0551, 0.2335, 3.3913) #jpdb
    def __init__(self, card_id: int = 1, created: datetime = datetime.now(UTC)) -> None:
        Carte.listeCartes.append(self)
        self.card = Card()
        self.ratings = []
        self.startDate = created
        self.scheduling_cards = f.repeat(self.card, created)
        self.card_id = card_id

    def rate(self,rating: Rating):
        self.card = self.scheduling_cards[rating].card        
        self.scheduling_cards = f.repeat(self.card,self.card.due)
        self.ratings.append(rating)

    def rateDebug(self,rating: Rating):
        Carte.rate(self,rating)
        print(self.timeBeforeReview())
        print(self.card.due)

    def timeBeforeReview(self):
        delta = self.card.due - datetime.now(UTC)
        return delta.total_seconds()
    
    def due(self):
        return self.card.due

    def resetDueTime(self): 
        #à utiliser que pour test: reset pas la mémoire de la carte
        self.card.due = datetime.now(UTC)

    def reviewHistory(self,rating: Rating):
        return scheduling_cards[rating].review_log.rating
        

