from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.manage_database import get_deck_list_from_user


class Deckform(FlaskForm):
    name = StringField('Nom du deck*', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Créer !')
