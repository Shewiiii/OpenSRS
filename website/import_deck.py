import requests
from app.manage_database import *
from bs4 import BeautifulSoup
import time
import re


def request(url: str, cookie: dict) -> BeautifulSoup:
    '''Crée une instance BeautifulSoup à partir d'un url.

        Paramètres:
            url (str): Lien vers le site.
            cookie (dict): Cookies à charger (ex: {'sid': [UN STRING]}).
    '''
    print(f'request: {url}')
    raw = requests.get(url, cookies=cookie)
    raw.encoding = 'UTF-8'
    return BeautifulSoup(raw.text, features='html.parser')


def get_pitchaccent_pattern_from_div(
    div: BeautifulSoup
) -> str:
    '''Retourne le pitch accent pattern sous forme d'un string.

        Paramètre:
            div (BeautifulSoup): La div contenant le motif du pitchaccent (jpdb).
    '''
    divs = div.find_all('div')
    moras = []
    kana = []
    pitchaccent_pattern = ''
    for div in divs:
        style = div['style']
        # div avec les divs
        if 'linear-gradient' in style:
            moras.append(div)

        # les divs avec les kana
        elif 'background-color' in style:
            kana.append(div.text)

    for mora in moras:
        if '--pitch-high-s' in str(mora):
            pitchaccent_pattern += 'H'
        elif '--pitch-low-s' in str(mora):
            pitchaccent_pattern += 'L'
        elif '--pitch-high-s' in str(mora):
            pitchaccent_pattern += 'H'

    final = ''
    # string de la longueur du mot
    for i in range(len(kana)):
        final += pitchaccent_pattern[i]*len(kana[i])

    return final


def import_deck(
    sid: str,
    jpdb_deck_id: int,
    cards_count: int,
    name: str = 'Deck jpdb importé',
    description: str = 'Ceci est un deck importé de jpdb.',
    user_id: str = Constants.temp_user_id,
    parameters: str = '&show_only=new&sort_by=by-frequency-global',
) -> None:
    '''Importe un deck présent sur jpdb vers OpenSRS.

        Paramètres:
            sid (str): Cookies du compte contenant les decks à importer.
            Note: Il est FORTEMENT recommandé d'utiliser les cookies d'un compte secondaire.

            jpdb_deck_id (id): L'id du deck, présent dans l'url du deck.

            cards_count (int): Nombre de cartes à importer.

            parameters (str):  Les paramètres de tri/filtrage de la page.
            Sont ajoutées après l'url du deck.

            name (str): Nom du deck sur OpenSRS.

            description (str): Description dur deck sur OpenSRS.

            user_id (int): L'id de l'utilisateur propriétaire du deck.
    '''
    if name == 'Deck jpdb importé':
        name += f' {jpdb_deck_id}'

    cookie = {'sid': sid}
    url = f'https://jpdb.io/deck?id={jpdb_deck_id}' + parameters

    pages = cards_count//50 + 1
    added_words = 0
    jpdb_words = []

    # Premier passage: on retient les mots à ajouter plus tard:
    for i in range(pages):
        raw = request(f'{url}&offset={pages*50}', cookie)
        divs = raw.find_all('div', {'class': 'entry new'})

        for new_div in divs:
            if added_words < cards_count:
                a = BeautifulSoup(
                    str(new_div.find('div', {'class': 'vocabulary-spelling'})),
                    features='html.parser'
                ).find('a')

                word = a.text
                word_id = re.findall(r'\d+', a['href'])[0]

                raw_a = str(a)
                reading = ''
                for letter in raw_a:
                    if 12354 <= ord(letter) <= 12538:
                        reading += letter

                meanings = new_div.find('div').find_all(
                    'div')[-1].text.split(';')
                for i in range(len(meanings)):
                    meanings[i] = meanings[i].strip()

                jpdb_words.append({
                    'word_id': word_id,
                    'word': word,
                    'meanings': meanings,
                    'reading': reading,
                })
            added_words += 1

        # Attendre entre chaque requête
        time.sleep(0.6)

    # Deuxième passage: on collecte les infos de chaque mot
    # à partir de la page vocabulary
    # (phrase, phrase traduite...pitch accent ?)
    cards = []
    for word in jpdb_words:
        url = f'https://jpdb.io/vocabulary/{word['word_id']}/{word['word']}'

        raw = request(url, cookie)
        example = raw.find('div', {'class': 'subsection-examples'})

        jp_sentence = example.find('div', {'class': 'jp'})
        if jp_sentence:
            jp_sentence = jp_sentence.text
        else:
            jp_sentence = ''

        en_sentence = example.find('div', {'class': 'en'})
        if en_sentence:
            en_sentence = en_sentence.text
        else:
            en_sentence = ''

        pitchaccent_div = raw.find(
            'div', {'style': 'word-break: keep-all; display: flex;'})
        pitchaccent = get_pitchaccent_pattern_from_div(pitchaccent_div)

        card = word
        card.update({
            'jp_sentence': jp_sentence,
            'en_sentence': en_sentence,
            'pitchaccent': pitchaccent,
        })
        cards.append(card)
        # Attendre entre chaque requête
        time.sleep(0.6)

    # Dernière étape: créer le deck
    deck_id = get_free_id()
    create_deck(
        user_id=user_id,
        deck_id=deck_id,
        name=name,
        description=description,
    )

    for card in cards:
        create_card(
            deck_id=deck_id,
            front=card['word'],
            front_sub=card['jp_sentence'],
            back=f"{card['reading']} - {card['meanings'][0]}",
            back_sub=card['en_sentence'],
            back_sub2=f'Pitch Accent: {card['pitchaccent']}',
            tag='jpdb',
            
        )
    return cards


# DELETE
# import_deck(
#     sid='89d5db349b4a16dbf792a34116236bdf',
#     jpdb_deck_id=151,
#     cards_count=5,
# )

# raw = BeautifulSoup('<div style="word-break: keep-all; display: flex;"><div style="display: flex; background-image: linear-gradient(to bottom,var(--pitch-high-s),var(--pitch-high-e)); padding-top: 2px; margin-bottom: 2px; margin-right: -2px; padding-right: 2px;"><div style="background-color: var(--background-color); padding-right: 2px;">け</div></div><div style="display: flex; background-image: linear-gradient(to top,var(--pitch-low-s),var(--pitch-low-e)); padding-bottom: 2px; margin-top: 2px;  padding-left: 2px;"><div style="background-color: var(--background-color); padding-left: 1px;">っしん</div></div></div>', features='html.parser')
# divs = raw.find_all('div')
# moras = []
# pitchaccent_pattern = ''
# for div in divs:
#     style = div['style']
#     if 'linear-gradient' in style:
#         moras.append(div)
# for mora in moras:
#     if '--pitch-high-s' in str(mora):
#         pitchaccent_pattern += 'H'
#     elif '--pitch-low-s' in str(mora):
#         pitchaccent_pattern += 'L'
# print(pitchaccent_pattern)
