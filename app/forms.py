from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

class SubcategoryForm(FlaskForm):
    name = StringField('产品名称', validators=[DataRequired(), Length(max=100)])
    code_letter = StringField('产品名称标识符', validators=[DataRequired(), Length(min=1, max=1)])
    description = TextAreaField('描述')

class ForgotPasswordForm(FlaskForm):
    username_or_email = StringField('用户名或邮箱', validators=[DataRequired()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('password', message='两次输入的密码不一致')]) 