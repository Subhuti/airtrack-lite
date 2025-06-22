# /app/routes/add_aircraft_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from sqlalchemy import text
from extensions import db
from utils.airport_utils import format_airport_display as airport_display

add_aircraft_bp = Blueprint("add_aircraft", __name__, url_prefix="/aircraft")

@add_aircraft_bp.route("/new", methods=["GET", "POST"])
def add_aircraft():
    session.pop('_flashes', None)
    registration = request.args.get("registration", "").strip().upper()

    airlines = []
    try:
        result = db.session.execute(
            text("SELECT AirlineID, AirlineName FROM airlines ORDER BY AirlineName")
        )
        airlines = [dict(row._mapping) for row in result.fetchall()]
    except Exception:
        flash("Could not retrieve airlines.", "danger")

    if request.method == "POST":
        registration_form = request.form.get("Registration", "").strip().upper()

        existing = db.session.execute(
            text("SELECT 1 FROM aircraft WHERE Registration = :reg"),
            {"reg": registration_form}
        ).scalar()

        if existing:
            flash(f"An aircraft with registration {registration_form} already exists.", "warning")
            return render_template("add_aircraft.html", registration=registration_form, airlines=airlines)

        try:
            # Extract form values
            flight_number = request.form.get("FlightNumber", "").strip().upper()
            aircraft_type = request.form.get("Aircraft_Type")
            country_of_reg = request.form.get("Country_of_Reg")
            airline_id_raw = request.form.get("AirlineID")
            airline_id = int(airline_id_raw) if airline_id_raw and airline_id_raw.isdigit() else None
            departure = request.form.get("Departure", "").strip()
            arrival = request.form.get("Arrival", "").strip()

            aircraft_updated = datetime.now()
            first_sighted = aircraft_updated

            db.session.execute(text("""
                INSERT INTO aircraft (
                    AirlineID, Registration, FlightNumber, Aircraft_Type,
                    Country_of_Reg, Departure, Arrival,
                    First_Sighted, Aircraft_Updated
                ) VALUES (
                    :AirlineID, :Registration, :FlightNumber, :Aircraft_Type,
                    :Country_of_Reg, :Departure, :Arrival,
                    :First_Sighted, :Aircraft_Updated
                )
            """), {
                "AirlineID": airline_id,
                "Registration": registration_form,
                "FlightNumber": flight_number,
                "Aircraft_Type": aircraft_type,
                "Country_of_Reg": country_of_reg,
                "Departure": departure,
                "Arrival": arrival,
                "First_Sighted": first_sighted,
                "Aircraft_Updated": aircraft_updated
            })

            db.session.commit()
            flash("Aircraft added successfully!", "success")
            return redirect(url_for("aircraft.aircraft_table"))

        except Exception as e:
            db.session.rollback()
            flash(f"Failed to add aircraft: {str(e)}", "danger")
            return render_template("add_aircraft.html", registration=registration_form, airlines=airlines)

    return render_template("add_aircraft.html", airlines=airlines, registration=registration)
