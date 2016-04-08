from app_poll import (db, code_generator, slugify)


import datetime


def get_last_30_polls():
    polls = Poll.query.filter(Poll.is_public == True)[-30:]
    result_json = {}
    for poll in polls:
        choices = {}
        total_votes = 0
        for choice in poll.choices:
            count = len(choice.votes)
            total_votes += count
            choices[choice.choice_text] = count
        result_json[poll.url_str] = {
            'Question Text': poll.question_text,
            'Question Slug': slugify(poll.question_text),
            'Date Created': poll.pub_date,
            'Allow Multiple Choices': poll.allow_multi_choice,
            'Allow Repeat Vote': poll.allow_same_user,
            'Is Public': poll.is_public,
            'Choices': choices,
            }
    return result_json


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_str = db.Column(db.String(8), unique=True)
    question_text = db.Column(db.String(180), unique=False)
    allow_multi_choice = db.Column(db.Boolean)
    allow_same_user = db.Column(db.Boolean)
    use_captcha = db.Column(db.Boolean)
    is_public = db.Column(db.Boolean)
    pub_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    choices = db.relationship('Choice', backref='poll',
                              lazy='dynamic')

    def __init__(self, question_text,
                 allow_multi_choice, allow_same_user,
                 use_captcha, is_public):
        url_str = code_generator()
        while Poll.query.filter(Poll.url_str == url_str).first():
            url_str = code_generator()
        self.url_str = url_str
        self.question_text = question_text
        self.allow_multi_choice = allow_multi_choice
        self.allow_same_user = allow_same_user
        self.use_captcha = use_captcha
        self.is_public = is_public

    def __repr__(self):
        return '<Poll %r>' % self.question_text


votes = db.Table(
    'votes',
    db.Column('vote_id', db.Integer, db.ForeignKey('vote.id')),
    db.Column('choice_id', db.Integer, db.ForeignKey('choice.id'))
    )


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    choice_text = db.Column(db.String(150), unique=False)
    votes = db.relationship('Vote', secondary=votes,
                            backref=db.backref('choice', lazy='dynamic'))
    pub_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, choice_text, question_id):
        self.choice_text = choice_text
        self.question_id = question_id

    def __repr__(self):
        return '<Choice %r>' % self.choice_text


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ip = db.Column(db.String(15))
    choice_id = db.Column(db.Integer, db.ForeignKey('choice.id'), default='0')

    def __init__(self, user_ip, choice_id):
        self.user_ip = user_ip
        self.choice_id = choice_id

    def __repr__(self):
        return '<Vote %r>' % self.user_ip

db.create_all()
