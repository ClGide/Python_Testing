import json
from flask import Flask, render_template,\
    request, redirect, flash, url_for
from datetime import datetime


CLUB_PATH = "clubs.json"
COMPETITION_PATH = "competitions.json"


def load_clubs():
    with open(CLUB_PATH) as clubs:
        list_of_clubs = json.load(clubs)['clubs']
        return list_of_clubs


def load_competitions():
    with open(COMPETITION_PATH) as competitions:
        list_of_competitions = json.load(competitions)['competitions']
        return list_of_competitions


def search_club(field, value):
    if field not in ["name", "email", "points", "reserved_places"]:
        raise ValueError("the value for the field arg isn't a valid one")

    clubs = load_clubs()
    try:
        club = [club for club in clubs if club[field] == value][0]
    except IndexError or KeyError:
        return []

    return club, clubs


def search_competition(field, value):
    if field not in ["name", "date", "number_of_places", "taken_place"]:
        raise ValueError("the value for the field arg isn't a valid one")

    competitions = load_competitions()
    try:
        competition = [competition for competition in competitions
                       if competition[field] == value][0]
    except IndexError or KeyError:
        return []

    return competition, competitions


"""TODO: this shall go in init.py"""
app = Flask(__name__)
app.secret_key = 'something_special'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def show_summary():
    """
    loads the available competitions in welcome.html and the data about the
    club that just logged in in index.html. It handles the form in index.html.
    """
    competitions = load_competitions()
    club, clubs = search_club("email", request.form['email'])
    if club:
        for competition in competitions:
            if competition["taken_place"] is False:
                if datetime.strptime(
                        competition["date"], "%Y-%m-%d %H:%M:%S"
                ) < datetime.now():
                    competition["taken_place"] = True
                    with open(
                            COMPETITION_PATH, "w"
                    ) as to_be_updated_competitions:
                        json.dump({"competitions": competitions},
                                  to_be_updated_competitions,
                                  indent=4)
        return render_template('welcome.html',
                               club=club,
                               competitions=competitions)
    flash("we couldn't find your email in our database.")
    return render_template("index.html")


@app.route('/book/<competition_to_be_booked_name>/<club_making_reservation_name>')
def book(competition_to_be_booked_name, club_making_reservation_name):
    """
    Shows the user which competition he can book places to.

    In the previous implementation there was an if statement that seemed
    superfluous to me. The logic was the following. If for some reason, the
    webpage shows some competition which disappeared, and the user tries to
    book a place at that competition, the flash message will them that something
    went wrong. But I don't see any reason for that to happen. The user never
    manually enters a competition's name.
    Ideally, I shouldn't even have to reload the JSON file. But for the moment
    it seems I can only send a str repr of a dict and not a dict through url_for.
    In other words, the value passed to competition_to_be_booked isn't a dict
    but a str repr of a dict or a dict.
    """

    competition, competitions = search_competition("name", competition_to_be_booked_name)
    club, clubs = search_club("name", club_making_reservation_name)
    return render_template('booking.html',
                           club=club,
                           competition=competition)


@app.route('/purchasePlaces', methods=['POST'])
def purchase_places():
    """Handles the form in booking.html."""
    competition_to_be_booked_name = request.form['competition']
    competition, competitions = search_competition("name", competition_to_be_booked_name)
    club, clubs = search_club("name", request.form["club"])
    places_required = int(request.form['places'])
    club_number_of_points = int(club["points"])
    to_be_reserved_total_places = club["reserved_places"][competition_to_be_booked_name] + places_required

    if to_be_reserved_total_places > 12:
        flash("you required more than 12 places !")
        return render_template("booking.html",
                               club=club,
                               competition=competition)

    if competition["taken_place"] is False:
        if datetime.strptime(
                competition["date"], "%Y-%m-%d %H:%M:%S"
        ) < datetime.now():
            competition["taken_place"] = True
            with open(
                    COMPETITION_PATH, "w"
            ) as to_be_updated_competitions:
                json.dump({"competitions": competitions},
                          to_be_updated_competitions,
                          indent=4)
            flash("the competition already took place !")
            return render_template("booking.html",
                                   club=club,
                                   competition=competition)

    if places_required > club_number_of_points:
        flash("you required more places than you have available !")
        return render_template("booking.html",
                               club=club,
                               competition=competition)

    competition['number_of_places'] = int(
        competition['number_of_places']) - places_required
    club["points"] = club_number_of_points - places_required
    club["reserved_places"][competition_to_be_booked_name] = to_be_reserved_total_places

    with open(CLUB_PATH, "w") as to_be_updated_clubs:
        json.dump({"clubs": clubs},
                  to_be_updated_clubs,
                  indent=4)

    with open(COMPETITION_PATH, "w") as to_be_updated_competitions:
        json.dump({"competitions": competitions},
                  to_be_updated_competitions,
                  indent=4)

    flash('Great-booking complete!')
    return render_template('welcome.html',
                           club=club,
                           competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))
