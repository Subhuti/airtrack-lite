from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from sqlalchemy import text
from extensions import db

edit_aircraft_bp = Blueprint("edit_aircraft", __name__, url_prefix="/edit_aircraft")

@edit_aircraft_bp.route("/<int:aircraft_id>", methods=["GET", "POST"])
def edit_aircraft(aircraft_id):
    try:
        result = db.session.execute(text("SELECT AirlineID, AirlineName FROM airlines ORDER BY AirlineName"))
        airlines = [dict(row._mapping) for row in result.fetchall()]

        if request.method == "POST":
            registration = request.form.get("Registration", "").strip().upper()
            flight_number = request.form.get("FlightNumber", "").strip().upper()
            aircraft_type = request.form.get("Aircraft_Type", "").strip()
            spotted_at = request.form.get("Spotted_At", "").strip()
            country_of_reg = request.form.get("Country_of_Reg", "").strip()
            airline_id = int(request.form.get("AirlineID", "") or 0) or None
            departure = request.form.get("Departure", "").strip().upper()
            arrival = request.form.get("Arrival", "").strip().upper()
            aircraft_updated = datetime.now()
            save_as_new_flight = request.form.get("save_as_new_flight") == "true"

            try:
                db.session.execute(text("""
                    UPDATE aircraft
                    SET AirlineID = :AirlineID,
                        Registration = :Registration,
                        FlightNumber = :FlightNumber,
                        Aircraft_Type = :Aircraft_Type,
                        Country_of_Reg = :Country_of_Reg,
                        Spotted_At = :Spotted_At,
                        Departure = :Departure,
                        Arrival = :Arrival,
                        Aircraft_Updated = :Aircraft_Updated
                    WHERE AircraftID = :AircraftID
                """), {
                    "AirlineID": airline_id,
                    "Registration": registration,
                    "FlightNumber": flight_number,
                    "Aircraft_Type": aircraft_type,
                    "Country_of_Reg": country_of_reg,
                    "Spotted_At": spotted_at,
                    "Departure": departure,
                    "Arrival": arrival,
                    "Aircraft_Updated": aircraft_updated,
                    "AircraftID": aircraft_id
                })

                if save_as_new_flight:
                    db.session.execute(text("""
                        INSERT INTO flights (AircraftID, FlightNumber, Departure, Arrival, Timestamp, Spotted_At)
                        VALUES (:AircraftID, :FlightNumber, :Departure, :Arrival, :Timestamp, :Spotted_At)
                    """), {
                        "AircraftID": aircraft_id,
                        "FlightNumber": flight_number,
                        "Departure": departure,
                        "Arrival": arrival,
                        "Timestamp": datetime.utcnow(),
                        "Spotted_At": spotted_at
                    })
                else:
                    result = db.session.execute(text("""
                        SELECT FlightID FROM flights
                        WHERE AircraftID = :AircraftID
                        ORDER BY Timestamp DESC
                        LIMIT 1
                    """), {"AircraftID": aircraft_id}).fetchone()

                    if result:
                        db.session.execute(text("""
                            UPDATE flights
                            SET FlightNumber = :FlightNumber,
                                Departure = :Departure,
                                Arrival = :Arrival,
                                Spotted_At = :Spotted_At
                            WHERE FlightID = :FlightID
                        """), {
                            "FlightNumber": flight_number,
                            "Departure": departure,
                            "Arrival": arrival,
                            "Spotted_At": spotted_at,
                            "FlightID": result._mapping["FlightID"]
                        })

                db.session.commit()
                flash("Aircraft updated successfully!", "success")
                return redirect(url_for("aircraft.aircraft_table"))

            except Exception as e:
                db.session.rollback()
                flash(f"Failed to update aircraft: {str(e)}", "danger")

        result = db.session.execute(text("SELECT * FROM aircraft WHERE AircraftID = :AircraftID"), {"AircraftID": aircraft_id})
        aircraft = result.fetchone()
        if not aircraft:
            flash("Aircraft not found.", "danger")
            return redirect(url_for("aircraft.aircraft_table"))

        return render_template("edit_aircraft.html", aircraft=dict(aircraft._mapping), airlines=airlines)

    except Exception as e:
        flash("Unexpected error loading edit form.", "danger")
        return redirect(url_for("aircraft.aircraft_table"))
