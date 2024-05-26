import mysql.connector
from datetime import datetime, timezone
from app.secret import Trucs
from app.constants import Constants
import re
from fsrs import Rating, State
from app.model import Carte
import os
import pathlib


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
              debug: bool = False,
              many: bool = False,
              ):
        if debug:
            print(sql)
            print(params)
        try:
            cursor = self.conn.cursor(buffered=True)
        except:
            self.connect()
            cursor = self.conn.cursor(buffered=True)
        if many:
            cursor.executemany(sql, params)
        else:
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
    img_id, _ = get_img(deck_id)
    if img_id == None:
        img_id = get_free_id(table=table)
    else:
        print(f"Image déjà existante à l'ID {img_id}, remplacage..")
        try:
            delete_image(deck_id)
        except:
            print('Erreur, image corrompue.')

    sql = f"""INSERT INTO {table} VALUES (%s,%s,%s);"""
    db.query(sql, (img_id, deck_id, extension))

    return img_id


def delete_image(deck_id: int) -> None:
    '''Supprime dans la table images l'entrée d'une image d'un deck donné. 
    '''
    img_id, extension = get_img(deck_id)
    if img_id != None:
        path = (pathlib.Path(__file__).parents[1] / 'static/img/uploads'
                / f'{img_id}{extension}')
        os.remove(path)
        db.query("""DELETE FROM images WHERE deck_id = %s;""", (deck_id, ))


def get_img(
        deck_id: int,
        table=Constants.image_table
) -> tuple[int, str] | None:
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
        params: str | tuple = Constants.default_params,
        retention: int = Constants.default_retention,
) -> None:
    '''Crée un deck associé à un utilisateur en ajoutant une entrée dans la table decks.
    '''
    if deck_id == None:
        deck_id = get_free_id(decks_table)
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")

    sql = (f"""INSERT INTO {decks_table} """
           f"""VALUES (%s,%s,%s,%s,%s,%s,%s);""")
    db.query(sql,
             (deck_id,
              user_id,
              name,
              description,
              created,
              str(params),
              retention)
             )


def get_deck_params(
    deck_id: int,
    user_id: int = Constants.temp_user_id,
) -> tuple:
    '''Renvoie les paramètres FSRS deck.
    '''
    deck_infos, _ = get_deck_from_id(deck_id, user_id)

    return eval(deck_infos['params'])


def get_deck_retention(
    deck_id: int,
    user_id: int = Constants.temp_user_id,
) -> tuple:
    '''Renvoie les paramètres FSRS deck.
    '''
    deck_infos, _ = get_deck_from_id(deck_id, user_id)

    return deck_infos['retention']


def update_deck(
    deck_id: int,
    user_id: int,
    new_values: dict,
    table: str = Constants.decks_table
) -> None:
    '''Met à jour les infos d'un deck.
    '''
    params = []
    new_values['params'] = str(new_values['params'])

    sql = f"""UPDATE {table} SET """
    for column, values in new_values.items():
        sql += f"""{column} = %s,"""
        params.append(values)
    sql = sql[:-1] + f""" WHERE deck_id = %s AND user_id = %s;"""
    params += [deck_id, user_id]
    db.query(sql, params, debug=True)


def delete_deck(
        deck_id: int,
        deck_table: str = Constants.decks_table,
        card_table: str = Constants.cards_table,
        reviews_table: str = Constants.reviews_table,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Supprime un deck, son image et toutes ses cartes associées.
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
        deck_id = 0,
        card_id = None,
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
    '''Crée une carte associé à un deck et un utilisateur.
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
    ), debug=True)

    insert_card_srs(card_id, deck_id, user_id, srs_table=srs_table)


def create_cards(
    deck_id: int,
    cards: list,
    user_id: str = Constants.temp_new_cards,
    cards_table: str = Constants.cards_table,
    srs_table: str = Constants.srs_table,
) -> None:
    '''Crée des cartes à partir d'une liste de dico de cartes.
       Une carte doit posséder les clés suivantes:
       'front', 'front_sub', 'back', 'back_sub', 'back_sub2', 'tag'.
    '''
    # Table cartes
    card_count = len(cards)
    f_id = get_free_id()
    ids = [i for i in range(f_id,f_id+card_count)]
    sql = f"""INSERT INTO {cards_table} VALUES """
    params = []
    
    # Cartes FSRS
    card = Carte()
    p = card.card.to_dict()
    srs_params = []
    srsql = (f"""INSERT INTO {srs_table} VALUES """
             + "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL),"*card_count)[:-1]
    
    for i in range(card_count):
        now = datetime.now(timezone.utc)
        created = now.strftime("%Y-%m-%d %H:%M:%S")
        sql += f"""(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s),"""
        params += [
            ids[i],
            user_id,
            deck_id,
            cards[i]['front'],
            cards[i]['front_sub'],
            cards[i]['back'],
            cards[i]['back_sub'],
            cards[i]['back_sub2'],
            cards[i]['tag'],
            created,
        ]
        
        srs_params += [
            ids[i],
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
        ]
        
    sql = sql[:-1] + ';'
    
    db.query(sql, params)
    db.query(srsql, srs_params)

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
    '''Retourne tous les decks et ses infos d'un utilisateur.
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
            'params': row[5],
            'retention': row[6],
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
    '''Retourne à partir de son id les informations d'un deck et ses cartes.
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
            'created': firstRow[4],
            'params': firstRow[5],
            'retention': firstRow[6],
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
        state: int = -1,
        timestamp: int = 0,
        table=Constants.reviews_table,
) -> None:
    '''Ajoute une review dans la table reviews pour une carte,
        avec son deck et son utilisateur donné.
    '''
    # les ratings pouvant être: 'Again', 'Hard', 'Good', 'Easy'
    if timestamp == 0:
        now = datetime.now(timezone.utc)
        timestamp = int(datetime.timestamp(now)*1000)

    sql = (f"""INSERT INTO {table} VALUES """
           f"""(%s,%s,%s,%s,%s,%s);""")
    db.query(sql, (card_id, deck_id, user_id, rating, timestamp, state))


def add_review_entries(
    reviews: list,
    table=Constants.reviews_table,
) -> None:
    '''Ajoute plusieurs reviews.
       La variable reviews doit contenir des dictionnaires avec les clés
       suivantes: 
       'card_id', 'deck_id', 'user_id', 'rating', 'timestamp', 'state'.
    '''
    sql = f"""INSERT INTO {table} VALUES """
    params = []
    for review in reviews:
        sql += """(%s, %s, %s, %s, %s, %s),"""
        params += [
            review['card_id'],
            review['deck_id'],
            review['user_id'],
            review['rating'],
            review['timestamp'],
            review['state'],
        ]
    sql = sql[:-1]
    
    db.query(sql, params)


def update_card_srs_from_dict(
        card_id: int,
        variables: dict,
        user_id: int = Constants.temp_user_id,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Met à jour l'état d'une carte donnée à partir d'un dico de variables.
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


def bulk_update_cards_srs(
    cards_variables: dict,
    user_id: int = Constants.temp_user_id,
    srs_table: str = Constants.srs_table,
) -> None:
    '''Met à jour l'état de plusieurs cartes à partir d'un dico de variables.
        Paramètres:
            cards_variables (dict): Un dico avec en clé l'id de la carte et
            en valeur ses variables.

            srs_table (str): La table srs.
    '''
    columns = [
        'due',
        'stability',
        'difficulty',
        'elapsed_days',
        'scheduled_days',
        'reps',
        'lapses',
        'state',
        'last_review',
        'stability',
    ]
    # Alors c'est bizzare mais c'est pour minimiser les requêtes
    # Toujours 9 requêtes, au lieu du nombre de cartes O(n)
    for column in columns:
        sql = f"""UPDATE {srs_table} SET {column} = CASE card_id """
        inn = ''
        params = []
        for card_id, variables in cards_variables.items():
            inn += f'{card_id},'
            sql += f"""WHEN {card_id} THEN %s """
            params.append(variables[column])
        sql += (f"""ELSE {column} END WHERE card_id IN({inn[:-1]}) """
                f"""AND user_id = {user_id}""")

        db.query(sql, params)

    # sql = (
    #     f"""UPDATE {srs_table} SET """
    #     """due = %s,"""
    #     """stability = %s,"""
    #     """difficulty = %s,"""
    #     """elapsed_days = %s,"""
    #     """scheduled_days = %s,"""
    #     """reps = %s,"""
    #     """lapses = %s,"""
    #     """state = %s,"""
    #     """last_review = %s """
    #     """WHERE card_id = %s """
    #     """AND user_id = %s;"""
    # )
    # params = []
    # for card_id, variables in cards_variables.items():
    #     params += [(
    #         variables['due'],
    #         variables['stability'],
    #         variables['difficulty'],
    #         variables['elapsed_days'],
    #         variables['scheduled_days'],
    #         variables['reps'],
    #         variables['lapses'],
    #         variables['state'],
    #         variables['last_review'],
    #         card_id,
    #         user_id,
    #     )]

    # db.query(sql, params, many=True)


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
    # l'utilisation d'un dico rend la fonction bien plus intuitive à utiliser
    # et la rend future proof
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
            'timestamp': row[4]
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
            'timestamp': row[4]
        })

    return reviews


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


def add_jpdb_entry(
    vid: int,
    word: str,
    reading: str,
    meaning: str,
    jp_sentence: str,
    en_sentence: str,
    pitchaccent: str,
    table: str = Constants.jpdb_table,
) -> None:
    '''Ajoute un mot et ses informations de jpdb dans la table jpdb.
    '''
    db.query(f"""INSERT INTO {table} VALUES """
             """(%s, %s, %s, %s, %s, %s, %s)""",
             (vid, word, reading, meaning, jp_sentence, en_sentence, pitchaccent))


def add_jpdb_entries(
    entries: list,
    table: str = Constants.jpdb_table,
) -> None:
    '''Ajoute des mots et ses informations de jpdb dans la table jpdb.
       La liste rows doit contenir des dicos avec les clés suivantes:
       'vid', 'word', 'reading', 'meaning',
       'jp_sentence', 'en_sentence', 'pitch_accent'.
    '''
    sql = f"""INSERT INTO {table} VALUES """
    params = []
    for entry in entries:
        sql += """(%s, %s, %s, %s, %s, %s, %s),"""
        params += [
            entry['vid'],
            entry['word'],
            entry['reading'],
            entry['meaning'],
            entry['jp_sentence'],
            entry['en_sentence'],
            entry['pitchaccent'],
        ]
    sql = sql[:-1]
    
    db.query(sql, params)


def get_jpdb_data(table: str = Constants.jpdb_table) -> list:
    '''Récupère toute les données de la table jpdb.
    '''
    data = []
    cursor = db.query(f"""SELECT * FROM {table}""")
    result = cursor.fetchall()
    for row in result:
        data.append({
            'vid': row[0],
            'word': row[1],
            'reading': row[2],
            'meaning': row[3],
            'jp_sentence': row[4],
            'en_sentence': row[5],
            'pitch_accent': row[6],
        })

    return data


def delete_jpdb_data(table: str = Constants.jpdb_table) -> None:
    '''Supprime toutes les données de la table jpdb.
    '''
    db.query(f'DELETE FROM {table};')


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


def add_login(
    username: str,
    email: str,
    password: str,
    table: str = Constants.users_table
) -> int:
    '''Crée des identifiants dans la table users.
    '''
    created = datetime.now()
    user_id = get_free_id(table=table)
    sql = (f"""INSERT INTO {table} """
           f"""VALUES (%s,%s,%s,%s,%s);""")
    db.query(sql, (
        user_id,
        username,
        email,
        password,
        created,
    )
    )
    return user_id
