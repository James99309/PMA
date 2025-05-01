from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class SubcategoryForm(FlaskForm):
    name = StringField('产品名称', validators=[DataRequired(), Length(max=100)])
    code_letter = StringField('产品名称标识符', validators=[DataRequired(), Length(min=1, max=1)])
    description = TextAreaField('描述') 