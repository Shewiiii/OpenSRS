from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.manage_database import get_deck_list_from_user

class Cardform(FlaskForm):
    front = StringField('Front*', validators=[DataRequired()])
    front_sub = StringField('Front Sub')
    back = StringField('Back*', validators=[DataRequired()])
    back_sub = StringField('Back Sub')
    back_sub2 = StringField('Back Sub 2')
    tag = StringField('Tag')
    submit = SubmitField('Créer !')
