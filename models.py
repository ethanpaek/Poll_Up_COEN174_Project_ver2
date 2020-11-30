from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func
import uuid

# create a new SQLAlchemy object
db = SQLAlchemy()


# Base model that for other models to inherit from
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())


# Model to store user details
class Users(Base):
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(300))  # incase password hash becomes too long

    def __repr__(self):
        return self.username


# Model for polls
class Polls(Base):
    title = db.Column(db.String(500))
    status = db.Column(db.Boolean, default=True)  # to mark poll as open or closed
    create_uid = db.Column(db.ForeignKey('users.id'))
    close_date = db.Column(db.DateTime)
    voting_method = db.Column(db.Integer)  # 0: fptp, 1: approval, 2: irv, 3: rp, 4: borda, 5: score

    created_by = db.relationship('Users', foreign_keys=[create_uid],
                                 backref=db.backref('user_votes',
                                                    lazy='dynamic'))

    # user friendly way to display the object
    def __repr__(self):
        return self.title

    # returns dictionary that can easily be jsonified
    def to_json(self):
        return {
            'title': self.title,
            'options': [{'name': option.option.name,
                         'vote_count': option.vote_count}
                        for option in self.options.all()],
            'close_date': self.close_date,
            'status': self.status,
            'voting_method': self.voting_method,
            'total_vote_count': self.total_vote_count,
            'winner': self.winner
        }

    @hybrid_property
    def winner(self):
        test = {}
        for option in self.options.all():
            if not option.option.name in test:
                test[option.option.name] = option.vote_count
            else:
                test[option.option.name] += option.vote_count
        return max(test, key=test.get)

    @hybrid_property
    def total_vote_count(self, total=0):
        for option in self.options.all():
            total += option.vote_count
        return total

    @total_vote_count.expression
    def total_vote_count(cls):
        return select([func.sum(Votes.vote_count)]).where(Votes.poll_id == cls.id)

    @winner.expression
    def winner(cls):
        return select([func.sum(Votes.vote_count)]).where(Votes.poll_id == cls.id)


# Model for poll options
class Options(Base):
    name = db.Column(db.String(200))

    def __repr__(self):
        return self.name

    def to_json(self):
        return {
            'id': uuid.uuid4(),  # Generates a random uuid
            'name': self.name
        }


# Votes model to connect polls, options, and users together
class Votes(Base):
    # Columns declaration
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'))
    vote_count = db.Column(db.Integer, default=0)

    # Relationship declaration (makes it easier for us to access the votes model
    # from the other models it's related to)
    poll = db.relationship('Polls', foreign_keys=[poll_id],
                           backref=db.backref('options', lazy='dynamic'))
    user = db.relationship('Users', foreign_keys=[user_id])
    option = db.relationship('Options', foreign_keys=[option_id])

    def __repr__(self):
        # a user friendly way to view our objects in the terminal
        return self.option.name


class UserPolls(Base):
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'))

    polls = db.relationship('Polls', foreign_keys=[poll_id],
                            backref=db.backref('voted_on_by', lazy='dynamic'))

    users = db.relationship('Users', foreign_keys=[user_id],
                            backref=db.backref('voted_on', lazy='dynamic'))

    options = db.relationship('Options', foreign_keys=[option_id],
                              backref=db.backref('voted_on_by', lazy='dynamic'))
