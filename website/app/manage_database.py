import mysql.connector
from datetime import datetime, timezone
from app.secret import Trucs
from app.constants import Constants
import re
from fsrs import Rating, State
from app.model import Carte


class DB:
    # en gros: se connecte à la base de données quand nécessaire, pas de pb d'actualisation comme ça
    conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=Trucs.mdp,
            database='cards')

    def query(self, 
              sql: str, 
              params: tuple | None = None,
              debug: bool = False
    ):  
        if debug:
            print(sql)
        try:
            cursor = self.conn.cursor(buffered=True)
        except:
            self.connect()
            cursor = self.conn.cursor(buffered=True)
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor


db = DB()


class Card:
    def __init__(self, id) -> None:
        self.id = id
        # ...


def get_all_ids(table=Constants.cards_table) -> list:
    ids = []
    cursor = db.query(f"SELECT * FROM {table}")
    result = cursor.fetchall()
    for row in result:
        ids.append(row[0])
    return ids


def get_free_id(table=Constants.cards_table) -> int:
    cursor = db.query(f'SELECT * FROM {table};')
    result = cursor.fetchall()
    if len(result) == 0:
        return 0
    else:
        lastid = result[-1][0]
        return lastid+1


def remove_ghost_reviews(
        card_table=Constants.cards_table,
        reviews_table=Constants.reviews_table
) -> None:
    '''Ne devrait être utilisé que en cas d'erreurs.
    '''
    ids = get_all_ids(card_table)
    cursor = db.query(f'SELECT card_id FROM {reviews_table};')
    result = cursor.fetchall()
    for row in result:
        card_id = row[0]
        if card_id not in ids:
            db.query(
                f"""DELETE FROM {reviews_table} """
                """WHERE card_id = %s;""",
                (card_id, )
            )


def add_image(
        deck_id: int,
        extension: str,
        table=Constants.image_table
) -> int:
    '''Associe une image sous format .jpg, .png ou .gif à un deck donné.

        Retourne l'id de l'image dans la table images.
    '''
    sql = f"""SELECT img_id FROM {table} WHERE deck_id = %s"""
    cursor = db.query(sql, (deck_id))
    result = cursor.fetchall()

    if len(result) != 0:
        print(f"image déjà existante à l'ID {result[0][0]}, remplacage..")
        sql = f"""UPDATE {table} SET extension = %s WHERE deck_id = %s;"""
        db.query(sql, (extension, deck_id))
        return result[0][0]

    else:
        img_ig = get_free_id(table=table)
        sql = f"""INSERT INTO {table} VALUES (%s,%s,%s);"""
        db.query(sql, (img_ig, deck_id, extension))

        return img_ig


def delete_image(deck_id: int) -> None:
    '''Supprime dans la table images l'entrée d'une image d'un deck donné. 
    '''
    db.query("""DELETE FROM images WHERE deck_id = %s;""", (deck_id, ))


def get_img(
        deck_id: int,
        table=Constants.image_table
) -> tuple[int, str]:
    '''Retourne un tuple contenant l'id de l'image dans la table image, et son extension.
    '''
    sql = (f"""SELECT img_id, extension """
           f"""FROM {table} WHERE deck_id = %s;""")
    cursor = db.query(sql, (deck_id, ))
    result = cursor.fetchall()

    if len(result) == 0:
        return (None, None)

    else:
        return (result[0][0], result[0][1])


def create_deck(
        user_id: str = Constants.temp_user_id,
        deck_id: int | None = None,
        name: str = 'name',
        description: str = 'description',
        decks_table: str = Constants.decks_table,
) -> None:
    '''Crée un deck associé à un utilisateur en ajoutant une entrée dans la table decks.
    '''
    if deck_id == None:
        deck_id = get_free_id(decks_table)
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")

    sql = (f"""INSERT INTO {decks_table} """
           f"""VALUES (%s,%s,%s,%s,%s);""")
    db.query(sql, (deck_id, user_id, name, description, created))


def delete_deck(
        deck_id: int,
        deck_table: str = Constants.decks_table,
        card_table: str = Constants.cards_table,
        reviews_table: str = Constants.reviews_table,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Supprime un deck, son image et toutes ses cartes associées les tables correspondantes.
    '''
    db.query(f"""DELETE FROM {deck_table} WHERE deck_id = %s;""",
             (deck_id, ))
    db.query(f"""DELETE FROM {card_table} WHERE deck_id = %s;""",
             (deck_id, ))
    db.query(f"""DELETE FROM {reviews_table} WHERE deck_id = %s;""",
             (deck_id, ))
    db.query(f"""DELETE FROM {srs_table} WHERE deck_id = %s;""",
             (deck_id, ))
    delete_image(deck_id)


def create_card(
        deck_id=1,
        card_id=None,
        front: str = "front",
        front_sub: str = "front_sub",
        back: str = "back",
        back_sub: str = "back_sub",
        back_sub2: str = "back_sub2",
        tag: str = "tag",
        cards_table: str = Constants.cards_table,
        srs_table: str = Constants.srs_table,
        user_id: str = Constants.temp_user_id,
) -> None:
    '''Crée une carte associé à un deck et un utilisateur en ajoutant une entrée dans la table cards2.
    '''
    if card_id == None:
        card_id = get_free_id()
    now = datetime.now(timezone.utc)
    created = now.strftime("%Y-%m-%d %H:%M:%S")
    sql = f"""INSERT INTO {cards_table} VALUES (
           %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    db.query(sql, (
        card_id,
        user_id,
        deck_id,
        front,
        front_sub,
        back,
        back_sub,
        back_sub2,
        tag,
        created,
    ))

    insert_card_srs(card_id, deck_id, user_id, srs_table=srs_table)


def delete_card(
        card_id: int,
        card_table: str = Constants.cards_table,
        review_table: str = Constants.reviews_table,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Supprime toutes les cartes d'un deck donné.
    '''

    db.query(f"""DELETE FROM {card_table}
             WHERE card_id = %s;""", (card_id, ))
    db.query(f"""DELETE FROM {review_table}
             WHERE card_id = %s;""", (card_id, ))
    db.query(f"""DELETE FROM {srs_table}
             WHERE card_id = %s;""", (card_id, ))


def delete_all_cards(table: str = Constants.cards_table) -> None:
    '''Supprime toutes les cartes de tous les decks.
    '''
    ids = get_all_ids(table)
    for card_id in ids:
        delete_card(card_id)


def delete_everything(
    decks_table: str = Constants.decks_table,
    card_table: str = Constants.cards_table,
    review_table: str = Constants.reviews_table,
    srs_table: str = Constants.srs_table
) -> None:
    '''Supprime TOUS les decks, reviews, images et cartes.
    '''
    db.query(f'DELETE FROM {decks_table};')
    db.query(f'DELETE FROM {card_table};')
    db.query(f'DELETE FROM {review_table};')
    db.query(f'DELETE FROM {srs_table};')


def get_card_from_card_id(
        card_id: int,
        table=Constants.cards_table
) -> None | dict:
    '''Retourne les informations d'une carte sous forme d'un dictionnaire 
        à partir de son id.
    '''
    cursor = db.query(f"""SELECT * FROM {table} """
                      f"""WHERE card_id = %s;""",
                      (card_id, ))
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        row = result[0]
        dico = {
            'card_id': row[0],
            'user_id': row[1],
            'deck_id': row[2],
            'front': row[3],
            'front_sub': row[4],
            'back': row[5],
            'back_sub': row[6],
            'back_sub2': row[7],
            'tag': row[8],
            'created': row[9],
        }

        return dico


def get_cards_from_list(
    card_ids: list,
    deck_id: int,
    table=Constants.cards_table
) -> None | dict:
    '''Retourne les informations d'une carte sous forme d'un dictionnaire 
        à partir d'une liste d'ids.
    '''
    params = [deck_id]
    sql = (f"""SELECT * FROM {table} """
           """WHERE deck_id = %s AND """)
    for card_id in card_ids:
        params.append(card_id)
        sql += """card_id = %s OR """

    sql = sql[:-3] + ';'
    cursor = db.query(sql, params)
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        cards = []
        for row in result:
            dico = {
                'card_id': row[0],
                'deck_id': row[2],
                'front': row[3],
                'front_sub': row[4],
                'back': row[5],
                'back_sub': row[6],
                'back_sub2': row[7],
                'tag': row[8],
                'created': row[9]
            }
            cards.append(dico)

        return cards


def get_decks_from_user(
    request,
    user_id=Constants.temp_user_id,
    table=Constants.decks_table,
    cards_table=Constants.cards_table,
) -> dict:
    '''Retourne tous les decks associé à un utilisateur, à partir de son id, sous forme d'un dictionnaire.
    '''
    from app.reviews import get_cards_srs_to_review_from_deck_id, get_review_stats
    cursor = db.query(f'SELECT * FROM {table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    decks = []
    for row in result:
        img_id, extension = get_img(row[0])

        sql = (f"""SELECT COUNT(front) FROM {cards_table} """
               f"""WHERE deck_id = %s;""")
        count = db.query(sql, (row[0], )).fetchall()[0][0]

        deck_id = row[0]
        if f'NEW_CARDS_COUNT{deck_id}' in request.cookies:
            new_cards_count = int(request.cookies.get(
                f'NEW_CARDS_COUNT{deck_id}'))
        else:
            new_cards_count = 0
        due_cards_srs = get_cards_srs_to_review_from_deck_id(
            deck_id,
            new_cards_mode=Constants.new_cards_mode,
            new_cards_limit=Constants.new_cards_limit - new_cards_count,
        )
        stats = get_review_stats(due_cards_srs)

        decks.append({
            'deck_id': deck_id,
            'name': row[2],
            'description': row[3],
            'created': row[4],
            'card_count': count,
            'img_id': img_id,
            'extension': extension,
            'new': stats['new'],
            'review': stats['review'],
        })

    return decks


def get_deck_from_id(
        deck_id: int,
        user_id: int,
        decks_table=Constants.decks_table,
        cards_table=Constants.cards_table,
) -> None | tuple[dict, list[dict]]:
    '''Retourne à partir de son id les informations d'un deck, ainsi que toutes les cartes contenues dans ce dernier.
    '''
    # 1ère requête pour vérifier si un deck existe pour un utilisateur donné
    sql = (f"""SELECT * FROM {decks_table} """
           f"""WHERE {decks_table}.deck_id = %s """
           f"""AND {decks_table}.user_id = %s;""")
    cursor = db.query(sql, (deck_id, user_id))
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        firstRow = result[0]
        # garde les infos du deck dans une variable
        deckInfos = {
            'deck_id': firstRow[0],
            'name': firstRow[2],
            'description': firstRow[3],
            'created': firstRow[4]
        }
        # 2ème requête pour obtenir toutes les cartes de ce deck, met les les cartes dans une liste cards
        sql = (f"""SELECT * FROM {cards_table} """
               f"""WHERE {cards_table}.deck_id = %s """
               f"""AND {cards_table}.user_id = %s;""")
        cursor = db.query(sql, (deck_id, user_id))

        result = cursor.fetchall()
        cards = []

        for row in result:
            cards.append({
                'card_id': row[0],
                'front': row[3],
                'front_sub': row[4],
                'back': row[5],
                'back_sub': row[6],
                'back_sub2': row[7],
                'tag': row[8],
                'created': row[9]
            })

        return (deckInfos, cards)


def get_card_ids_from_deck_id(
        deck_id: int,
        user_id: int = Constants.temp_user_id,
) -> list[int]:
    '''Retourne tous les identifiants des cartes associées à un deck.
    '''
    deckInfos, cards = get_deck_from_id(deck_id, user_id)
    card_ids = []
    for card in cards:
        card_ids.append(card['card_id'])
    return card_ids


def add_review_entry(
        card_id: int,
        deck_id: int,
        user_id: int,
        rating: str,
        state: int,
        timestamp: int = 0,
        reviews_table=Constants.reviews_table,
) -> None:
    '''Ajoute une review dans la table reviews pour une carte,
        avec son deck et son utilisateur donné.
    '''
    # les ratings pouvant être: 'Again', 'Hard', 'Good', 'Easy'
    if timestamp == 0:
        now = datetime.now(timezone.utc)
        timestamp = int(datetime.timestamp(now)*1000)

    sql = (f"""INSERT INTO {reviews_table} VALUES """
           f"""(%s,%s,%s,%s,%s,%s);""")
    db.query(sql, (card_id, deck_id, user_id, rating, timestamp, state))


def update_card_srs_from_dict(
        card_id: int,
        variables: dict,
        user_id: int = Constants.temp_user_id,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Met à jour l'état d'une carte donnée dans la table srs à partir d'un dico de variables.
    '''
    assert 'last_review' in variables, 'Erreur: last_review manquant.'
    db.query(
        f"""UPDATE {srs_table} SET """
        """due = %s,"""
        """stability = %s,"""
        """difficulty = %s,"""
        """elapsed_days = %s,"""
        """scheduled_days = %s,"""
        """reps = %s,"""
        """lapses = %s,"""
        """state = %s,"""
        """last_review = %s """
        """WHERE card_id = %s """
        """AND user_id = %s;""",
        (variables['due'],
         variables['stability'],
         variables['difficulty'],
         variables['elapsed_days'],
         variables['scheduled_days'],
         variables['reps'],
         variables['lapses'],
         variables['state'],
         variables['last_review'],
         card_id,
         user_id,
         )
    )


def insert_card_srs(
        card_id: int,
        deck_id: int,
        user_id: int = Constants.temp_user_id,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Ajoute une entrée dans la table srs
        pour une carte et ses valeurs données.
    '''
    card = Carte()
    p = card.card.to_dict()

    db.query(
        f"""INSERT INTO {srs_table} VALUES ("""
        """%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"""
        """NULL);""",
        (card_id,
         deck_id,
         user_id,
         p['due'],
         p['stability'],
         p['difficulty'],
         p['elapsed_days'],
         p['scheduled_days'],
         p['reps'],
         p['lapses'],
         p['state'],
         )
    )


def get_card_variables(
    card_id: int,
    user_id: int = Constants.temp_user_id,
    srs_table: str = Constants.srs_table,
) -> dict:
    '''Retourne les variables d'une carte donnée à partir de la table srs.
    '''
    cursor = db.query(
        f"""SELECT * FROM {srs_table} """
        """WHERE card_id = %s """
        """AND user_id = %s;""",
        (card_id,
         user_id,
         )
    )
    result = cursor.fetchall()
    row = result[0]
    variables = {
        'due': row[3].replace(tzinfo=timezone.utc),
        'stability': row[4],
        'difficulty': row[5],
        'elapsed_days': row[6],
        'scheduled_days': row[7],
        'reps': row[8],
        'lapses': row[9],
        'state': State(row[10]),
    }
    if row[11]:
        variables['last_review'] = row[11].replace(tzinfo=timezone.utc)
    else:
        variables['last_review'] = None
    return variables


def forget_card(
        card_id: int,
        reviews_table=Constants.reviews_table,
        srs_table=Constants.srs_table,
) -> None:
    '''Supprime toutes les reviews dans la table reviews d'une carte donnée.
    '''
    card = get_card_from_card_id(card_id)
    deck_id, user_id = card['deck_id'], card['user_id']

    db.query(f"""DELETE FROM {reviews_table} """
             """WHERE card_id = %s;""",
             (card_id, ))
    db.query(f"""DELETE FROM {srs_table} """
             """WHERE card_id = %s;""",
             (card_id, ))
    insert_card_srs(card_id, deck_id, user_id, srs_table=srs_table)


def get_ratings_from_card_id(
        card_id: int,
        table=Constants.reviews_table,
        stringForm: bool = False,
) -> list:
    '''Retourne les Rating d'une carte donnée, sous forme de strings ou non. 
    '''
    cursor = db.query(
        f"SELECT * FROM {table} WHERE card_id = %s;""",
        (card_id, )
    )
    result = cursor.fetchall()
    ratings = []
    if stringForm == True:
        for row in result:
            ratings.append(row[2])
    else:
        for row in result:
            dico = {
                'Again': Rating.Again,
                'Hard': Rating.Hard,
                'Good': Rating.Good,
                'Easy': Rating.Easy,
            }
            ratings.append(dico[row[3]])

    return ratings


def get_reviews_from_deck_id(
        deck_id: int,
        table=Constants.reviews_table,
) -> dict:
    '''Retourne les reviews des cartes d'un deck donnée.
    '''
    # l'utilisation d'un dico rend la fonction bien plus intuitive à utiliser et la rend future proof
    cursor = db.query(f"""SELECT * FROM {table} WHERE deck_id = %s;""",
                      (deck_id, ))
    result = cursor.fetchall()
    reviews = []
    for row in result:
        reviews.append({
            'card_id': row[0],
            'deck_id': row[1],
            'user_id': row[2],
            'rating': row[3],
            'date': row[4]
        })

    return reviews


def get_reviews_from_list(
        card_ids: list,
        deck_id: int,
        table=Constants.reviews_table,
) -> dict:
    '''Retourne les reviews des cartes données dans une liste.
    '''
    params = [deck_id]
    sql = (f"""SELECT * FROM {table} """
           """WHERE deck_id = %s AND """)
    for card_id in card_ids:
        params.append(card_id)
        sql += """card_id = %s OR """

    sql = sql[:-3] + ';'
    cursor = db.query(sql, params)
    result = cursor.fetchall()

    reviews = []

    for row in result:
        reviews.append({
            'card_id': row[0],
            'deck_id': row[1],
            'user_id': row[2],
            'rating': row[3],
            'date': row[4]
        })


def get_cards_srs_from_deck_id(
    deck_id: int,
    user_id: int = Constants.temp_user_id,
    table=Constants.srs_table
) -> dict:
    '''Retourne un dictionnaire contenant les informations srs des cartes d'un deck donné.
    '''
    cards_srs = []
    cursor = db.query(f"""SELECT * FROM {table} """
                      """WHERE deck_id = %s """
                      """AND user_id = %s;""",
                      (deck_id, user_id))
    result = cursor.fetchall()
    for card in result:
        card_dict = {
            'card_id': card[0],
            'deck_is': card[1],
            'user_id': card[2],
            'due': card[3],
            'stability': card[4],
            'difficulty': card[5],
            'elapsed_days': card[6],
            'scheduled_days': card[7],
            'reps': card[8],
            'lapses': card[9],
            'state': card[10],
        }
        if card[11]:
            card_dict['last_review'] = card[11]
        else:
            card_dict['last_review'] = None
        cards_srs.append(card_dict)

    return cards_srs


def test_login(
    username: str,
    password: str,
    table: str = Constants.users_table
) -> str:
    '''Teste des identifiants de connection,
        renvoie l'user_id sous forme de string si ces derniers sont valides. 
    '''
    cursor = db.query(
        f"""SELECT * FROM {table} """
        """WHERE username = %s AND password = %s;""",
        (username, password)
    )
    result = cursor.fetchall()

    if len(result) == 0:
        return None
    else:
        return str(result[0][0])
