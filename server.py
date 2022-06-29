"""Whenever we refer to clubs or competitions, we refer to dictionary
holding (possibly modified by user interaction) data about the clubs
or competitions from the JSON files. The keys of those dictionary are
always strings while the values can be strings, integers, booleans and
even dictionaries.
"""

import json
from datetime import datetime
from typing import Union

from flask import Flask, render_template, \
    request, redirect, flash, url_for

CLUB_PATH = "clubs.json"
COMPETITION_PATH = "competitions.json"


def load_clubs() -> list[dict[str, any]]:
    """Loads the JSON file containing data about the clubs and
    returns it in a list."""
    with open(CLUB_PATH) as clubs:
        list_of_clubs = json.load(clubs)['clubs']
        return list_of_clubs


def load_competitions() -> list[dict[str, any]]:
    """Loads the JSON file containing data about the competitions and
    returns it in a list."""
    with open(COMPETITION_PATH) as competitions:
        list_of_competitions = json.load(competitions)['competitions']
        return list_of_competitions


def search_club(field: str, value: any) -> Union[list, tuple[
    dict[str, any], list[dict[str, any]]]]:

    """Loads the JSON file containing data about the clubs and
    returns data about the club having the corresponding field and
    value. For convenience, also returns the list of clubs."""
    if field not in ["name", "email", "points", "reserved_places"]:
        raise ValueError("the value for the field arg isn't a valid one")

    clubs = load_clubs()
    try:
        club = [club for club in clubs if club[field] == value][0]
    except IndexError or KeyError:
        return []
    else:
        return club, clubs


def search_competition(field: str, value: any) -> Union[list, tuple[
    dict[str, any], list[dict[str, any]]]]:

    """Loads the JSON file containing data about the competitions and only
    returns data about the competition having the corresponding field and
    value. For convenience, also returns the list of clubs."""
    if field not in ["name", "date", "number_of_places", "taken_place"]:
        raise ValueError("the value for the field arg isn't a valid one")

    competitions = load_competitions()
    try:
        competition = [competition for competition in competitions
                       if competition[field] == value][0]
    except IndexError or KeyError:
        return []
    else:
        return competition, competitions


def update_all_competitions_taken_place_field(competitions):
    """Receives a list of competitions. Loops through each
    competition. If the taken_place field is set to False,
    compares the date field with datetime.now(). Sets the taken_place
    field to True if the date field is behind. Writes the list of
    competition to the JSON file and returns the list.  """
    for competition in competitions:
        if competition["taken_place"] is False:
            if datetime.strptime(
                    competition["date"], "%Y-%m-%d %H:%M:%S"
            ) < datetime.now():
                competition["taken_place"] = True
                with open(
                        COMPETITION_PATH, "w"
                ) as file_to_write_competitions:
                    json.dump({"competitions": competitions},
                              file_to_write_competitions,
                              indent=4)
    return competitions


"""TODO: this shall go in init.py"""
app = Flask(__name__)
app.secret_key = 'something_special'


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/backToSummary/<email>")
def come_back_welcome_page(email):
    """
    Loads the available competitions in welcome.html and the data about the
    club that was logged_in in booking.html.
    """
    competitions = load_competitions()
    club, clubs = search_club("email", email)
    return render_template('welcome.html',
                           club=club,
                           competitions=competitions)


@app.route('/showSummary', methods=['POST'])
def show_summary():
    """
    Loads the available competitions in welcome.html and the data about the
    club that just logged in in index.html. It handles the form in index.html.
    """
    club, clubs = search_club("email", request.form['email'])
    competitions = load_competitions()
    if club:
        competitions = update_all_competitions_taken_place_field(competitions)
        return render_template('welcome.html',
                               club=club,
                               clubs=clubs,
                               competitions=competitions)

    flash("we couldn't find your email in our database.")
    return render_template("index.html")


@app.route(
    '/book/<competition_to_be_booked_name>/<club_making_reservation_name>')
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
    competition, competitions = search_competition(
        "name",
        competition_to_be_booked_name
    )
    club, clubs = search_club("name", club_making_reservation_name)
    return render_template('booking.html',
                           club=club,
                           competition=competition)


def more_than_12_reserved_places(club_reserved_places: int, required_places: int):
    """ Flashes a message if the club did reserve more than 12 places.


    Args:
        club_reserved_places: the number of places the club already reserved at
            the tournament before this operation.
        required_places: the number of places the club wants to reserve at the
            tournament within this operation.

    Returns: A string used in run_checks() if the club tries to reserve more
        than 12 places.
    """
    to_be_reserved_total_places = club_reserved_places + required_places
    if to_be_reserved_total_places > 12:
        flash("you required more than 12 places !")
        return "failed_check"


def not_enough_points(required_places: int, club_number_of_points: int):
    """ Flashes the corresponding message if the club wants to purchase more
    places than they have points.

    Args:
        required_places: the number of places the club wants to reserve at the
            tournament within this operation
        club_number_of_points: the number of points the club has before this
            operation.

    Returns: A string used in run_checks() if the club wants to purchase more
    places than they have points.

    """
    if required_places > club_number_of_points:
        flash("you do not have enough points!")
        return "failed_check"


def no_more_available_places(places_required, places_available):
    if places_available - places_required < 0:
        flash("there are no more places available !")
        return "failed_check"


def competition_took_place(competition):
    if competition["taken_place"] is False:
        if datetime.strptime(
                competition["date"], "%Y-%m-%d %H:%M:%S"
        ) < datetime.now():
            competition["taken_place"] = True
    if competition["taken_place"]:
        flash("the competition already took place !")
        return "failed_check"


def run_checks(competition, club, places_required, club_number_of_points):
    failed_checks = more_than_12_reserved_places(club["reserved_places"][competition["name"]], places_required) or not_enough_points(
        places_required,
        club_number_of_points) or no_more_available_places(places_required, competition["number_of_places"]) or competition_took_place(competition)
    if failed_checks:
        return render_template("booking.html",
                               club=club,
                               competition=competition)


def record_changes(competitions, competition, clubs, club, places_required,
                   club_number_of_points):
    competition_to_be_booked_name = competition["name"]
    competition['number_of_places'] = int(
        competition['number_of_places']
    ) - places_required
    club["points"] = club_number_of_points - places_required
    club["reserved_places"][
        competition_to_be_booked_name] = club["reserved_places"][
                                             competition_to_be_booked_name] + places_required

    with open(CLUB_PATH, "w") as to_be_updated_clubs:
        json.dump({"clubs": clubs},
                  to_be_updated_clubs,
                  indent=4)

    with open(COMPETITION_PATH, "w") as to_be_updated_competitions:
        json.dump({"competitions": competitions},
                  to_be_updated_competitions,
                  indent=4)

    return competitions, club


@app.route('/purchasePlaces', methods=['POST'])
def purchase_places():
    """Handles the form in booking.html."""

    competition_to_be_booked_name = request.form['competition']
    competition, competitions = search_competition(
        "name",
        competition_to_be_booked_name
    )
    club, clubs = search_club("name", request.form["club"])
    places_required = int(request.form['places'])
    club_number_of_points = int(club["points"])

    failed_checks = run_checks(competition, club, places_required,
                               club_number_of_points)
    if failed_checks:
        return failed_checks

    competitions, club = record_changes(
        competitions, competition,
        clubs, club,
        places_required, club_number_of_points
    )
    flash('Great-booking complete!')
    return render_template('welcome.html',
                           club=club,
                           clubs=clubs,
                           competitions=competitions)


# TODO: Add route for points display
@app.route("/points")
def points():
    clubs_to_display = load_clubs()
    return render_template("points.html",
                           clubs=clubs_to_display)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))
