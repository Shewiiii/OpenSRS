from datetime import datetime, timezone
from fsrs import *
from app.constants import Constants

# https://github.com/open-spaced-repetition/py-fsrs


# core 2k : (0.2458, 1.7517, 3.6668, 15.2497, 5.0366, 1.4023, 1.0596, 0.0299, 1.7953, 0.1, 1.1838, 2.2312, 0.0384, 0.3658, 1.4031, 0.363, 2.8899)
# 194/sentence mining ? : (1.14, 1.01, 5.44, 14.67, 5.3024, 1.5662, 1.2503, 0.0028, 1.5489, 0.1763, 0.9953, 2.7473, 0.0179, 0.3105, 0.3976, 0.0, 2.0902)
# default: (0.4,0.6,2.4,5.8,4.93,0.94,0.86,0.01,1.49,0.14,0.94,2.18,0.05,0.34,1.26,0.29,2.61)
# jpdb : (0.3035, 4.7433, 8.8727, 45.4892, 4.9939, 1.5012, 0.755, 0.0, 1.6041, 0.1, 1.0249, 2.2375, 0.0419, 0.3747, 1.0551, 0.2335, 3.3913)
# jpdb updated (81430 reviews): (0.2229, 2.7301, 6.885, 57.8649, 4.9466, 1.4764, 0.7677, 0.0, 1.6366, 0.0081, 1.004, 2.5281, 0.0126, 0.2702, 1.6888, 0.2355, 4.4478)


class Carte():

    def __init__(
        self,
        card_id: int = 1,
        created: datetime = datetime.now(timezone.utc),
        params: tuple = Constants.default_params,
        retention: int = Constants.default_retention,
    ) -> None:
        self.f = FSRS()
        self.f.p.request_retention = retention
        self.f.p.w = params

        self.card = Card()
        self.scheduling_cards = self.f.repeat(self.card, created)
        self.card_id = card_id
        self.retention = retention
        self.params = params

    def set_variables(self, variables: dict) -> None:
        '''Change les variables de la carte à partir d'un dico de variables.
        '''
        self.card.due = variables['due']
        self.card.stability = variables['stability']
        self.card.difficulty = variables['difficulty']
        self.card.elapsed_days = variables['elapsed_days']
        self.card.scheduled_days = variables['scheduled_days']
        self.card.reps = variables['reps']
        self.card.lapses = variables['lapses']
        self.card.state = variables['state']
        if variables['last_review']:
            self.card.last_review = variables['last_review']

    def get_variables(self) -> dict:
        '''Retourne les variables de la carte sous forme de dictionnaire.
        '''
        return self.card.to_dict()

    def rate(
        self,
        rating: Rating,
        now: datetime = datetime.now(timezone.utc)
    ) -> None:
        scheduling_cards = self.f.repeat(self.card, now)
        self.card = scheduling_cards[rating].card

    def rate_debug(
        self,
        rating: Rating,
        now: datetime = datetime.now(timezone.utc)
    ) -> None:
        self.rate(rating, now)
        print(self.time_before_review())
        print(self.card.due)

    def time_before_review(self) -> int:
        delta = self.card.due - datetime.now(timezone.utc)
        return delta.total_seconds()

    def due(self) -> datetime:
        return self.card.due

    def reset_due_time(self) -> None:
        # à utiliser que pour test: reset pas la mémoire de la carte
        self.card.due = datetime.now(timezone.utc)

    def review_history(self, rating: Rating) -> int:
        return self.scheduling_cards[rating].review_log.rating


# ratings = (
#             Rating.Good,
#             Rating.Good,
#             Rating.Good,
#             Rating.Good,
#             Rating.Good,
# )

# now = datetime.now(timezone.utc)

# f1 = FSRS()
# f1.p.w = Constants.default_params
# card1 = Card()

# for rating in ratings:
#     now = card1.due
#     scheduling_cards = f1.repeat(card1, now)
#     card1 = scheduling_cards[rating].card
#     # print(card1.due)


# f2 = FSRS()
# f2.p.w = Constants.jpdb_updated_params

# card2 = Card()
# for rating in ratings:
#     now = card2.due
#     scheduling_cards = f2.repeat(card2, now)
#     card2 = scheduling_cards[rating].card
#     # print(card2.due)

# carte1 = Carte(params=Constants.default_params)
# carte2 = Carte(params=Constants.jpdb_updated_params, retention=0.8)

# for rating in ratings:
#     carte1.rate(rating, now=carte1.due())
#     carte2.rate(rating, now=carte2.due())

# print("Après 5 bonnes reviews d'une carte, une carte sera planifié:")
# print(f'avec les paramètres par défaut et une rétention de {0.8}:',carte1.due())
# print(f'avec les paramètres optimisées et une rétention de {0.8}:',carte2.due())
