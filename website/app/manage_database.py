import mysql.connector
from datetime import datetime


class DB:
    # en gros: se connecte à la base de données quand nécessaire, pas de pb d'actualisation comme ça
    conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='!nxbTjiPw7@Pb8',
            database='cards')

    def query(self, sql):
        print(sql)
        try:
            cursor = self.conn.cursor(buffered=True)
        except:
            self.connect()
            cursor = self.conn.cursor(buffered=True)
        cursor.execute(sql)
        self.conn.commit()
        return cursor


db = DB()


class Constants:
    card_table = 'cards2'
    decks_table = 'decks'
    temp_user_id = 1


class Card:
    def __init__(self, id) -> None:
        self.id = id
        # ...


def get_all_ids(table=Constants.card_table) -> list:
    ids = []
    cursor = db.query(f"SELECT * FROM {table}")
    result = cursor.fetchall()
    for row in result:
        ids.append(row[0])
    return ids


def get_free_id(table=Constants.card_table) -> int:

    cursor = db.query(f'SELECT * FROM {table};')
    result = cursor.fetchall()
    if len(result) == 0:
        return 0
    else:
        lastid = result[-1][0]
        print("lastid:", lastid)
        return lastid+1

def getDecks(table=Constants.decks_table) -> list[tuple[int,str]]:
    cursor = db.query(f'SELECT * FROM {table};')
    result = cursor.fetchall()
    liste = []
    for row in result:
        liste.append((row[0],row[2]))
    return liste

def create_deck(user_id=Constants.temp_user_id, name='name', description='description', decks=Constants.decks_table) -> None:
    deck_id = get_free_id(decks)
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")
    string = f'INSERT INTO {decks} VALUES ({deck_id},{user_id},"{name}","{description}","{created}");'
    db.query(string)


def create_card(deck_id=1, front="front", front_sub="front_sub", back="back", back_sub="back_sub", back_sub2="back_sub2", tag="tag", table=Constants.card_table, user_id=Constants.temp_user_id) -> None:
    card_id = get_free_id()
    string = f'INSERT INTO {table} VALUES ({card_id},{user_id},"{deck_id}","{front}","{front_sub}","{back}","{back_sub}","{back_sub2}","{tag}");'
    db.query(string)


def delete_card(card_id, table=Constants.card_table) -> None:
    db.query(f"DELETE FROM {table} WHERE card_id = {card_id};")


def delete_all_cards(table=Constants.card_table) -> None:
    ids = get_all_ids(table)
    for card_id in ids:
        delete_card(card_id)
