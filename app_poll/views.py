from flask import (render_template, request,
                   abort, redirect, url_for, flash, jsonify)

from app_poll.models import (Poll, Choice, Vote, get_last_30_polls)
from app_poll import (app, db, slugify)


@app.route('/api/public/')
def api_public_view():
    return jsonify(get_last_30_polls())


@app.route('/public/')
def public_view():
    result_json = get_last_30_polls()
    return render_template('public.html', polls=result_json)


@app.route('/api/results/<poll_url>', methods=['GET', 'POST'])
def api_results(poll_url):
    poll = Poll.query.filter(Poll.url_str == poll_url).first()
    if not poll:
        return jsonify({'Erorr': 'Poll does not exist.'})
    result_json = {
        'Question Text': poll.question_text,
        'Question Slug': slugify(poll.question_text),
        'Date Created': poll.pub_date,
        'Allow Multiple Choices': poll.allow_multi_choice,
        'Allow Repeat Vote': poll.allow_same_user,
        'Is Public': poll.is_public}
    to_add = {}
    for choice in poll.choices:
        to_add[choice.choice_text] = {
            'Choice Slug': slugify(choice.choice_text),
            'Votes': len(choice.votes)}
    result_json['Choices'] = to_add
    return jsonify(result_json)


@app.route('/results/<poll_url>', methods=['GET', 'POST'])
def results(poll_url):
    from collections import OrderedDict
    poll = Poll.query.filter(Poll.url_str == poll_url).first()
    if not poll:
        flash("Poll doesn't exist!")
        return redirect(url_for('home'))
    result_json = {
        'Question Text': poll.question_text,
        'Question Slug': slugify(poll.question_text),
        'Date Created': poll.pub_date,
        'Allow Multiple Choices': poll.allow_multi_choice,
        'Allow Repeat Vote': poll.allow_same_user,
        'Is Public': poll.is_public}
    to_add = {}
    for choice in poll.choices:
        to_add[choice.choice_text] = {
            'Choice Slug': slugify(choice.choice_text),
            'Votes': len(choice.votes)}
    to_add = OrderedDict(sorted(to_add.items(),
                                key=lambda t: t[1]['Votes'], reverse=True))
    result_json['Choices'] = to_add
    return render_template('results.html', poll=poll,
                           result_json=result_json,
                           domain=app.config['DOMAIN_NAME'])


@app.route('/vote/<poll_url>', methods=['GET', 'POST'])
def vote_poll(poll_url):
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    poll = Poll.query.filter(Poll.url_str == poll_url).first()
    if not poll:
        flash("Poll doesn't exist!")
        return redirect(url_for('home'))

    if request.method == 'POST':
        if poll.use_captcha:
            if not recaptcha.verify():
                flash("Please fill in the ReCaptcha!")
                return redirect(url_for('vote_poll', poll_url=poll_url))

        data = dict((key, request.form.getlist(key) if
                    len(request.form.getlist(key)) > 1 else
                    request.form.getlist(key)[0])
                    for key in request.form.keys())
        if not poll.allow_same_user:
            vote = Vote.query.filter(Vote.user_ip == ip).first()
            if vote:
                choice = Choice.query.filter(
                    Choice.id == vote.choice_id).first()
                if choice.question_id == poll.id:
                    # Don't allow dup voting
                    flash("You have already voted on this poll!")
                    return redirect(url_for('results', poll_url=poll_url))

        for choice in poll.choices:
            try:
                data[choice.choice_text]
                if data[choice.choice_text] == "on":
                    vote = Vote(user_ip=ip, choice_id=choice.id)
                    db.session.add(vote)
                    choice.votes.append(vote)
                    if not poll.allow_multi_choice:
                        break
            except KeyError as e:
                continue

        db.session.commit()
        return redirect(url_for('results', poll_url=poll_url))

    return render_template('vote.html', poll=poll)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if not recaptcha.verify():
            flash("Please fill in the ReCaptcha!")
            return render_template('home.html')

        question_text = request.form['question_text']
        data = dict((key, request.form.getlist(key) if
                    len(request.form.getlist(key)) > 1 else
                    request.form.getlist(key)[0])
                    for key in request.form.keys())
        question_text = data['question_text']
        allow_multi_choice = data.get('allow_multi_choice', False)
        if allow_multi_choice == "on":
            allow_multi_choice = True
        allow_same_user = data.get('allow_same_user', False)
        if allow_same_user == "on":
            allow_same_user = True
        use_captcha = data.get('use_captcha', False)
        if use_captcha == "on":
            use_captcha = True
        is_public = data.get('public_form', False)
        if is_public == "on":
            is_public = True
        poll = Poll(question_text, allow_multi_choice, allow_same_user,
                    use_captcha, is_public)
        if data['option_text_one'] == data['option_text_two']:
            flash("You can't have the same two options!")
            return render_template('home.html')

        already_optios = [data['option_text_one'],  data['option_text_two']]
        choice_saves = [data['option_text_one'],  data['option_text_two']]
        u = Choice(data['option_text_one'], poll.id)
        db.session.add(u)
        poll.choices.append(u)
        u = Choice(data['option_text_two'], poll.id)
        db.session.add(u)
        poll.choices.append(u)
        if isinstance(data['option_text'], str):
            data['option_text'] = [data['option_text']]
        for option in data['option_text']:
            if option.strip() == "":
                continue
            if option in already_optios:
                # No dups
                continue
            already_optios.append(option)
            u = Choice(option, poll.id)
            choice_saves.append(u)
            db.session.add(u)
            poll.choices.append(u)
        if len(choice_saves) < 2:
            flash("You need to select more than one option!")
            return render_template('home.html')
        db.session.add(poll)
        db.session.commit()
        flash("Start by clicking on the share button!")
        return redirect(url_for('results', poll_url=poll.url_str))

    return render_template('home.html')
