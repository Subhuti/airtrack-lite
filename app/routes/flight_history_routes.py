from flask import Blueprint, redirect, url_for, flash, render_template
from datetime import datetime
from sqlalchemy import text
from extensions import db

flight_history_bp = Blueprint("flight_history", __name__, url_prefix="/add_flight_history")

@flight_history_bp.route("/view/<int:aircraft_id>", methods=["GET"])
def view_flight_history(aircraft_id):
    try:
        aircraft_result = db.session.execute(
            text("SELECT * FROM aircraft WHERE AircraftID = :id"),
            {"id": aircraft_id}
        ).fetchone()

        if not aircraft_result:
            flash("Aircraft not found.", "danger")
            return redirect(url_for("aircraft.aircraft_table"))

        aircraft = dict(aircraft_result._mapping)

        result = db.session.execute(text("""
            SELECT f.*, a.AirlineName 
            FROM flights f
            LEFT JOIN airlines a ON f.AirlineID = a.AirlineID
            WHERE f.AircraftID = :id
            ORDER BY f.Timestamp DESC
        """), {"id": aircraft_id})

        history = [dict(row._mapping) for row in result.fetchall()]

        return render_template("flight_history.html", aircraft=aircraft, history=history)

    except Exception as e:
        print(f"❌ Error fetching flight history: {e}")
        flash("Error loading flight history.", "danger")
        return redirect(url_for("aircraft.aircraft_table"))

@flight_history_bp.route("/<int:aircraft_id>", methods=["GET"])
def add_flight_history(aircraft_id):
    try:
        result = db.session.execute(
            text("SELECT * FROM aircraft WHERE AircraftID = :id"),
            {"id": aircraft_id}
        ).fetchone()

        if not result:
            flash("Aircraft not found for flight history.", "danger")
            return redirect(url_for("aircraft.aircraft_table"))

        aircraft = dict(result._mapping)
        timestamp = datetime.now()

        db.session.execute(text("""
            INSERT INTO flights (
                AircraftID, AirlineID, FlightNumber, Registration,
                Aircraft_Type, Departure, Arrival,
                Country_of_Reg, Timestamp, Spotted_At
            ) VALUES (
                :AircraftID, :AirlineID, :FlightNumber, :Registration,
                :Aircraft_Type, :Departure, :Arrival,
                :Country_of_Reg, :Timestamp, :Spotted_At
            )
        """), {
            "AircraftID": aircraft["AircraftID"],
            "AirlineID": aircraft["AirlineID"],
            "FlightNumber": aircraft["FlightNumber"],
            "Registration": aircraft["Registration"],
            "Aircraft_Type": aircraft["Aircraft_Type"],
            "Departure": aircraft["Departure"],
            "Arrival": aircraft["Arrival"],
            "Country_of_Reg": aircraft["Country_of_Reg"],
            "Timestamp": timestamp,
            "Spotted_At": aircraft["Spotted_At"]
        })

        db.session.commit()
        flash("Flight history recorded.", "success")

    except Exception as e:
        print(f"❌ Failed to insert flight history: {e}")
        db.session.rollback()
        flash("Failed to insert flight history.", "danger")

    return redirect(url_for("aircraft.aircraft_table"))
