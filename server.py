"""
Whenever we refer to clubs or competitions, we refer to dictionary
holding (possibly modified by user interaction) data about the clubs
or competitions from the JSON files. The keys of those dictionary are
always strings while the values can be strings, integers, booleans and
even dictionaries.

Don't change the import names or file paths, they are relative to Project11
directory; the place from which we run the app.
"""

from flask import Blueprint, render_template, \
    request, redirect, flash, url_for
from development.utils import load_clubs, search_club, \
    load_competitions, search_competition, \
    run_checks, update_all_competitions_taken_place_field, \
    record_changes


CLUB_PATH = "development/clubs.json"
COMPETITION_PATH = "development/competitions.json"

bp = Blueprint("gudlft", __name__, url_prefix="")


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route("/backToSummary/<email>")
def come_back_welcome_page(email):
    """
    Loads the available competitions in welcome.html and the data about the
    club that was logged_in in booking.html.
    """
    competitions = load_competitions(COMPETITION_PATH)
    club, clubs = search_club("email", email, CLUB_PATH)
    return render_template('welcome.html',
                           club=club,
                           competitions=competitions)


@bp.route('/showSummary', methods=['POST'])
def show_summary():
    """
    Loads the available competitions in welcome.html and the data about the
    club that just logged in in index.html. It handles the form in index.html.
    """
    club, clubs = search_club("email", request.form['email'], CLUB_PATH)
    competitions = load_competitions(COMPETITION_PATH)
    if club:
        competitions = update_all_competitions_taken_place_field(competitions)
        return render_template('welcome.html',
                               club=club,
                               clubs=clubs,
                               competitions=competitions)

    flash("we couldn't find your email in our database.")
    return render_template("index.html")


@bp.route(
    '/book/<competition_to_be_booked_name>/<club_making_reservation_name>'
)
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
        competition_to_be_booked_name,
        COMPETITION_PATH
    )
    club, clubs = search_club("name", club_making_reservation_name, CLUB_PATH)
    return render_template('booking.html',
                           club=club,
                           competition=competition)


@bp.route('/purchasePlaces', methods=['POST'])
def purchase_places():
    """Handles the form in booking.html."""

    competition_to_be_booked_name = request.form['competition']
    competition, competitions = search_competition(
        "name",
        competition_to_be_booked_name,
        COMPETITION_PATH
    )
    club, clubs = search_club("name", request.form["club"], CLUB_PATH)
    places_required = int(request.form['places'])
    club_number_of_points = int(club["points"])

    failed_checks = run_checks(competition, club, places_required,
                               club_number_of_points)
    if failed_checks:
        return failed_checks

    competitions, club = record_changes(competitions, competition, clubs, club,
                                        places_required, club_number_of_points)
    flash('Great-booking complete!')
    return render_template('welcome.html',
                           club=club,
                           clubs=clubs,
                           competitions=competitions)


@bp.route("/points")
def points():
    clubs_to_display = load_clubs(CLUB_PATH)
    return render_template("points.html",
                           clubs=clubs_to_display)


@bp.route('/logout')
def logout():
    return redirect(url_for('gudlft.index'))

