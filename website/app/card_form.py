from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from manage_database import getDecks

class Cardform(FlaskForm):
    deckid = SelectField('Deck*', choices=getDecks(),validators=[DataRequired()]) #devra être précisé avant (chaque deck aura sa page pour rajouter des cartes, donc cela ne devrait pas être précisé par l'utilisateur)
    front = StringField('Front*', validators=[DataRequired()])
    front_sub = StringField('Front Sub')
    back = StringField('Back*', validators=[DataRequired()])
    back_sub = StringField('Back Sub')
    back_sub2 = StringField('Back Sub 2')
    tag = StringField('Tag')
    submit = SubmitField('Créer !')