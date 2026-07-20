from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import HiddenField, IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, Regexp, ValidationError

from .models import User


USERNAME_RULE = Regexp(
    r"^[A-Za-z0-9_]+$", message="아이디는 영문, 숫자, 밑줄만 사용할 수 있습니다."
)


class RegisterForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(min=3, max=32), USERNAME_RULE])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(min=10, max=128)])
    confirm = PasswordField("비밀번호 확인", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("가입")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("이미 사용 중인 아이디입니다.")


class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(max=32)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("로그인")


class ProfileForm(FlaskForm):
    bio = TextAreaField("소개글", validators=[Length(max=500)])
    submit = SubmitField("저장")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("현재 비밀번호", validators=[DataRequired(), Length(max=128)])
    new_password = PasswordField("새 비밀번호", validators=[DataRequired(), Length(min=10, max=128)])
    confirm = PasswordField("새 비밀번호 확인", validators=[DataRequired(), EqualTo("new_password")])
    submit = SubmitField("비밀번호 변경")


class ProductForm(FlaskForm):
    title = StringField("상품명", validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField("설명", validators=[DataRequired(), Length(min=2, max=2000)])
    price = IntegerField("가격(원)", validators=[DataRequired(), NumberRange(min=1, max=1_000_000_000)])
    image = FileField("상품 이미지")
    submit = SubmitField("저장")


class ChatForm(FlaskForm):
    body = StringField("메시지", validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField("전송")


class ReportForm(FlaskForm):
    reason = TextAreaField("신고 사유", validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField("신고")


class TransferForm(FlaskForm):
    receiver = StringField("받는 사용자", validators=[DataRequired(), Length(min=3, max=32), USERNAME_RULE])
    amount = IntegerField("금액(원)", validators=[DataRequired(), NumberRange(min=1, max=1_000_000_000)])
    submit = SubmitField("송금")


class ActionForm(FlaskForm):
    action = HiddenField("action", validators=[DataRequired(), Length(max=32)])
    submit = SubmitField("처리")

