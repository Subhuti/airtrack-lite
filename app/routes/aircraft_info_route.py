# /app/routes/aircraft_info_route.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import text
from extensions import db
from utils.country_flags import get_country_flag
from utils.airport_utils import format_airport_display as airport_display
from datetime import datetime, date
from math import ceil
import pytz
import logging

aircraft_info_bp = Blueprint("aircraft_info", __name__, url_prefix="/aircraft")

@aircraft_info_bp.route("/aircraft_info/<int:aircraft_id>")
def aircraft_info(aircraft_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 10

        query_aircraft = text("""
            SELECT ac.*, al.AirlineName
            FROM aircraft ac
            LEFT JOIN airlines al ON ac.AirlineID = al.AirlineID
            WHERE ac.AircraftID = :AircraftID
        """)
        result = db.session.execute(query_aircraft, {"AircraftID": aircraft_id}).fetchone()
        aircraft = dict(result._mapping) if result else None

        if not aircraft:
            flash("Aircraft not found.", "danger")
            return redirect(url_for("aircraft.aircraft_table"))

        aircraft["Registration"] = aircraft["Registration"].strip().upper()
        aircraft["FlightNumber"] = (aircraft.get("FlightNumber") or "").upper()
        aircraft["AirlineName"] = aircraft.get("AirlineName") or "Unknown"

        country = aircraft.get("Country_of_Reg") or ""
        aircraft["Country_Flag"] = get_country_flag(country)

        # First sighted
        dt = aircraft.get("First_Sighted")
        if dt:
            if isinstance(dt, date) and not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time())
            dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Australia/Sydney"))
            aircraft["First_Sighted_Display"] = dt.strftime('%d-%m-%Y %H:%M:%S')
        else:
            aircraft["First_Sighted_Display"] = "Unknown"

        # Last seen
        dt = aircraft.get("Aircraft_Updated")
        if dt:
            if isinstance(dt, date) and not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time())
            dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Australia/Sydney"))
            aircraft["Last_Sighted_Display"] = dt.strftime('%d-%m-%Y %H:%M:%S')
        else:
            aircraft["Last_Sighted_Display"] = "Unknown"

        aircraft["Spotted_At_Display"] = aircraft.get("Spotted_At") or "Unknown"
        aircraft["Aircraft_Departure"] = aircraft.get("Departure")
        aircraft["Aircraft_Arrival"] = aircraft.get("Arrival")

        # Latest known flight
        latest_result = db.session.execute(text("""
            SELECT Departure, Arrival
            FROM flights
            WHERE AircraftID = :AircraftID
            ORDER BY Timestamp DESC
            LIMIT 1
        """), {"AircraftID": aircraft_id}).fetchone()

        aircraft["Latest_Departure"] = latest_result[0] if latest_result else None
        aircraft["Latest_Arrival"] = latest_result[1] if latest_result else None

        # Pagination and history
        total = db.session.execute(text("SELECT COUNT(*) FROM flights WHERE AircraftID = :AircraftID"),
                                   {"AircraftID": aircraft_id}).scalar()
        total_pages = max(ceil(total / per_page), 1)
        offset = (page - 1) * per_page

        history_results = db.session.execute(text("""
            SELECT FlightID, FlightNumber, Departure, Arrival, Timestamp, Spotted_At
            FROM flights
            WHERE AircraftID = :AircraftID
            ORDER BY Timestamp DESC
            LIMIT :limit OFFSET :offset
        """), {"AircraftID": aircraft_id, "limit": per_page, "offset": offset}).fetchall()

        flight_history = []
        for row in history_results:
            flight = dict(row._mapping)
            ts = flight.get("Timestamp")
            if ts:
                if isinstance(ts, date) and not isinstance(ts, datetime):
                    ts = datetime.combine(ts, datetime.min.time())
                ts = ts.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Australia/Sydney"))
                flight["Timestamp_Display"] = ts.strftime('%d-%m-%Y %H:%M:%S')
            else:
                flight["Timestamp_Display"] = "Unknown"
            flight["Spotted_At"] = flight.get("Spotted_At") or "Unknown"
            flight_history.append(flight)

        return render_template(
            "aircraft_info.html",
            aircraft=aircraft,
            flight_history=flight_history,
            current_page=page,
            total_pages=total_pages,
            current_year=datetime.now().year
        )

    except Exception as e:
        logging.exception("❌ Error fetching aircraft info")
        flash("Database error occurred.", "danger")
        return redirect(url_for("aircraft.aircraft_table"))
