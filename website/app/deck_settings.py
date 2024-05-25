from collections.abc import Sequence
from typing import Any, Mapping
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired


class Decksettings(FlaskForm):
    name = StringField('Nom du deck*', validators=[DataRequired()])

    description = StringField('Description')

    params = StringField(
        'Paramètres FSRS (ne pas modifier si '
        'vous ne savez pas ce que vous faites)')

    def validate_params(form, field):
        s_params = form.data['params']
        try:
            params = eval(s_params)
            if len(params) != 17:
                raise ValidationError('invalid FSRS parameters')
        except Exception as e:
            print(e)
            raise ValidationError('invalid FSRS parameters')

    retention = StringField("Rétention souhaitée")
    
    # (de 0 à 1, correspond à "
    #     "la probablité que vous vous souveniez d'un mot "
    #     "lors de votre review, impacte le nombre de reviews à faire."
    #     "Recommandé: entre 0.75 et 0.9)"

    def validate_retention(form, field):
        s_retention = form.data['retention']
        try:
            retention = float(s_retention)
            if not 0 <= retention <= 1:
                raise ValidationError('invalid retention')   
        except Exception as e:
            print(e)
            raise ValidationError('invalid retention')

    submit = SubmitField('Appliquer')
