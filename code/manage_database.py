import mysql.connector

mydb = mysql.connector.connect(
  host='localhost',
  user="root",
  password = '!nxbTjiPw7@Pb8', 
  database = "cards"
)

print(mydb)
cursor = mydb.cursor()
cursor.execute("SELECT * FROM cards")

result = cursor.fetchall()

for i in result:
    print(i)

class Card:
    def __init__(self,id) -> None:
        self.id = id
        #...

def create_card(cursor=cursor,table="cards",id=1,deck="Japanese",front="front",front_sub="front_sub",back="back",back_sub="back_sub",back_sub2="back_sub2",tag="tag",user_id=1):
    print(f'INSERT INTO {table} VALUES ({id},"{deck}","{front}","{front_sub}","{back}","{back_sub}","{back_sub2}","{tag}",{user_id});')
    cursor.execute(f'INSERT INTO {table} VALUES ({id},"{deck}","{front}","{front_sub}","{back}","{back_sub}","{back_sub2}","{tag}",{user_id});')
    cursor.execute(f"CREATE TABLE card_{id} (rating ENUM('Again','Hard','Good','Easy'),rated_date TIMESTAMP(0), due_date TIMESTAMP(0));") #timestamp(0)=pas de décimales dans les secondes

def delete_card(id,cursor=cursor):
    cursor.execute(f"DELETE FROM cards WHERE id = {id};")
    cursor.execute(f"DROP TABLE card_{id};")