from os import getenv

from models import db, Users, Polls, Votes, Options, UserPolls
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI

if getenv('APP_MODE') == 'PRODUCTION':
    from production_settings import SQLALCHEMY_DATABASE_URI


api = Blueprint('api', 'api', url_prefix='/api')


@api.route('/polls', methods=['GET', 'POST'])
# retrieves/adds polls from/to the database
def api_polls():
    if request.method == 'POST':
        # get the poll and save it in the database
        poll = request.get_json()

        # simple validation to check if all values are properly set
        for key, value in poll.items():
            if not value:
                return jsonify({'message': 'value for {} is empty'.format(key)})

        title = poll['title']
        options_query = lambda option: Options.query.filter(Options.name.like(option))

        options = [Votes(option=Options(name=option))
                   if options_query(option).count() == 0
                   else Votes(option=options_query(option).first()) for option in poll['options']
                   ]
        eta = datetime.utcfromtimestamp(poll['close_date'])
        new_poll = Polls(title=title, options=options, close_date=eta, voting_method=0)

        db.session.add(new_poll)
        db.session.commit()

        # run the task
        from tasks import close_poll

        close_poll.apply_async((new_poll.id, SQLALCHEMY_DATABASE_URI), eta=eta)

        return jsonify({'message': 'Poll was created succesfully'})

    else:
        # it's a GET request, return dict representations of the API
        polls = Polls.query.filter_by(status=True).join(Votes).order_by(Polls.id.desc()).all()
        all_polls = {'Polls':  [poll.to_json() for poll in polls]}

        return jsonify(all_polls)


@api.route('/polls/options')
def api_polls_options():

    all_options = [option.to_json() for option in Options.query.all()]

    return jsonify(all_options)


@api.route('/poll/vote', methods=['PATCH'])
def api_poll_vote():
    poll = request.get_json()

    poll_title, option_name = (poll['poll_title'], poll['option'])

    join_tables = Votes.query.join(Polls).join(Options)

    # Get votes, poll, username, and option from the database
    poll = Polls.query.filter_by(title=poll_title, status=True).first()
    user = Users.query.filter_by(username=session['user']).first()
    option = Options.query.filter_by(name=option_name).first()

    # if poll was closed in the background before user voted
    if not poll:
        return jsonify({'message': 'Sorry! this poll has been closed'})

    # filter option names
    option_name = join_tables.filter(Polls.title.like(poll_title), Polls.status == True).filter(Options.name.like(option_name)).first()
    
    if option_name:
        # check if the user has voted on this poll
        poll_count = UserPolls.query.filter_by(poll_id=poll.id).filter_by(user_id=user.id).filter_by(option_id=option.id).count()
        if poll_count > 0:
            return jsonify({'message': 'Sorry! multiple votes are not allowed'})
        
        # record userpoll and vote
        user_poll = UserPolls(poll_id=poll.id, user_id=user.id, option_id=option.id)
        user_vote = Votes(poll_id=poll.id, user_id=user.id, option_id=option.id, vote_count=0)
        
        db.session.add(user_poll)
        db.session.add(user_vote)

        # increment vote_count by 1 if the option was found
        option_name.vote_count += 1
        
        db.session.commit()

        return jsonify({'message': 'Thank you for voting'})
    
    return jsonify({'message': 'Option or poll was not found please try again'})


@api.route('/poll/<poll_name>')
def api_poll(poll_name):

    poll = Polls.query.filter(Polls.title.like(poll_name)).first()

    return jsonify({'Polls': [poll.to_json()]}) if poll else jsonify({'message': 'poll not found'})
