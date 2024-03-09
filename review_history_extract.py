import json
data = json.load(open("reviews (1).json","r",encoding="UTF-8"))

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
# total = 0
# for i in range(6182):
#     r = len(data["cards_vocabulary_jp_en"][0]["reviews"])
#     total = total + r

ratings = {'fail':1,'nothing':1,'something':1,'hard':2,'okay':3,'easy':4}

tout = "card_id,review_time,review_rating,review_state,review_duration\n"
for reviewNumber in range(len(data["cards_vocabulary_jp_en"])):
    id = data["cards_vocabulary_jp_en"][reviewNumber]["vid"]
    data_mot = data["cards_vocabulary_jp_en"][reviewNumber]["reviews"]
    for review in data_mot:
        try:
            string = f"{id},{review["timestamp"]}000,{ratings[review["grade"]]},{0},{5}"
            tout = tout + string + "\n"
        except Exception as e:
            print(e)

open("output.csv","w+",encoding="UTF-8").write(tout)