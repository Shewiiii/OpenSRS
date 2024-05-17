from datetime import datetime, timezone
from fsrs import *


# https://github.com/open-spaced-repetition/py-fsrs

f = FSRS()

# core 2k : (0.2458, 1.7517, 3.6668, 15.2497, 5.0366, 1.4023, 1.0596, 0.0299, 1.7953, 0.1, 1.1838, 2.2312, 0.0384, 0.3658, 1.4031, 0.363, 2.8899)
# 194/sentence mining ? : (1.14, 1.01, 5.44, 14.67, 5.3024, 1.5662, 1.2503, 0.0028, 1.5489, 0.1763, 0.9953, 2.7473, 0.0179, 0.3105, 0.3976, 0.0, 2.0902)
# default: (0.4,0.6,2.4,5.8,4.93,0.94,0.86,0.01,1.49,0.14,0.94,2.18,0.05,0.34,1.26,0.29,2.61)
# jpdb : (0.3035, 4.7433, 8.8727, 45.4892, 4.9939, 1.5012, 0.755, 0.0, 1.6041, 0.1, 1.0249, 2.2375, 0.0419, 0.3747, 1.0551, 0.2335, 3.3913)
# jpdb updated (81430 reviews): (0.2229, 2.7301, 6.885, 57.8649, 4.9466, 1.4764, 0.7677, 0.0, 1.6366, 0.0081, 1.004, 2.5281, 0.0126, 0.2702, 1.6888, 0.2355, 4.4478)


class Carte():

    listeCartes = []

    f.p.w = (
        0.2229,
        2.7301,
        6.885,
        57.8649,
        4.9466,
        1.4764,
        0.7677,
        0.0,
        1.6366,
        0.0081,
        1.004,
        2.5281,
        0.0126,
        0.2702,
        1.6888,
        0.2355,
        4.4478,
    )
    # jpdb updated parameters

    def __init__(
        self,
        card_id: int = 1,
        created: datetime = datetime.now(timezone.utc)
    ) -> None:

        Carte.listeCartes.append(self)
        self.card = Card()
        self.scheduling_cards = f.repeat(self.card, created)
        self.card_id = card_id

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
        self.scheduling_cards = f.repeat(self.card, now)
        updated_card = self.scheduling_cards[rating].card
        self.card = updated_card

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
