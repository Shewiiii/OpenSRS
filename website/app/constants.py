from fsrs import Rating
class Constants:
    cards_table = 'cards2'
    decks_table = 'decks'
    image_table = 'images'
    deck_session_table = 'deck_session'
    user_session_table = 'user_session'
    jpdb_table = 'jpdb'
    reviews_table = 'reviews'
    users_table = 'users'
    srs_table = 'srs'
    temp_user_id = 1
    temp_new_cards = 10
    default_new = 10
    rating_dict = {
        'Again': Rating.Again, 
        'Hard': Rating.Hard, 
        'Good': Rating.Good, 
        'Easy': Rating.Easy,
    }
    timezone = 'Europe/Paris'
    session_delay = 4
    new_cards_limit = 10
    new_cards_mode = 'shuffle'
    default_params = (
        0.4,
        0.6,
        2.4,
        5.8,
        4.93,
        0.94,
        0.86,
        0.01,
        1.49,
        0.14,
        0.94,
        2.18,
        0.05,
        0.34,
        1.26,
        0.29,
        2.61,
    )
    jpdb_updated_params = (
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
        4.4478
    )
    default_retention = 0.8