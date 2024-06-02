import json


'''Json schema:

{'vid': 1465410,
   'spelling': '入り',
   'reading': 'いり',
   'reviews': [{'timestamp': 1672613991,
        'grade': 'something',
        'from_anki': False},
    {'timestamp': 1672699282, 'grade': 'okay', 'from_anki': False},
    {'timestamp': 1673912061, 'grade': 'okay', 'from_anki': False},
    {'timestamp': 1682722378, 'grade': 'okay', 'from_anki': False}]},

'''

'''FSRS Optimizer schema:

card_id,review_time,review_rating,review_state,review_duration
1465410,1672613991,1
1465410,1672699282,3
1465410,1673912061,3
1465410,1682722378,3

'''

'''Guide vers FSRS optimizer: https://github.com/open-spaced-repetition/fsrs-optimizer

python -m fsrs_optimizer "[NOM DU FICHIER].csv"

timezone: Europe/Paris
used next day start hour: 0 (reset à minuit avec jpdb)
the date at which before reviews will be ignored | YYYY-MM-DD (default: 2006-10-05): [Rien]
filter out suspended cards?: n
Save graphs?: y

'''


ratings = {'fail': 1, 'nothing': 1, 'something': 1,
           'hard': 2, 'okay': 3, 'easy': 4}


def jpdb_to_csv(
    filename: str,
    input_repo: str = 'jpdb',
    output_repo: str = 'converted',
) -> None:
    '''Convert jpdb reviews into a csv file.
    '''
    ratings = {'fail': 1, 'nothing': 1, 'something': 1,
           'hard': 2, 'okay': 3, 'easy': 4}
    labels = ("card_id,review_time,review_rating"
              ",review_state,review_duration\n")
    data = json.load(
        open(f"{input_repo}/{filename}.json", "r", encoding="UTF-8")
    )
    word_count = len(data["cards_vocabulary_jp_en"])
    review_count = 0

    for reviewNumber in range(word_count):
        id = data["cards_vocabulary_jp_en"][reviewNumber]["vid"]
        data_mot = data["cards_vocabulary_jp_en"][reviewNumber]["reviews"]
        for review in data_mot:
            try:
                string = f"{id},{review["timestamp"]}000,{
                    ratings[review["grade"]]},{0},{5}"
                labels = labels + string + "\n"
                review_count += 1
                if review_count % 5000 == 0:
                    print(f'{review_count} reviews analysées...')
            except Exception as e:
                print(e)

    open(f"{output_repo}/{filename}.csv", "w+", encoding="UTF-8").write(labels)
    print(f'Fini ! {word_count} mots analysés, avec un total de'
          f'{review_count} reviews effectuées')
