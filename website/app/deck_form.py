from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


class Deckform(FlaskForm):
    name = StringField('Nom du deck*', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Créer !')
