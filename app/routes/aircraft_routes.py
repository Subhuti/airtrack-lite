# /app/routes/aircraft_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from sqlalchemy import text
from datetime import datetime, date
from math import ceil
import logging
import pytz

from extensions import db
from utils.country_flags import get_country_flag
from utils.timezone_utils import get_current_timezone
from utils.airport_utils import format_airport_display as airport_display

aircraft_bp = Blueprint("aircraft", __name__, url_prefix="")

@aircraft_bp.route("/aircraft_table")
def aircraft_table():
    try:
        timezone = get_current_timezone()
        logging.info(f"Current timezone: {timezone}")

        filter_type = request.args.get("filter_type")
        airline_id = request.args.get("airlineID")
        registration = request.args.get("registration")

        PER_PAGE = 10
        current_page = request.args.get("page", 1, type=int)
        offset = (current_page - 1) * PER_PAGE

        # Count query
        count_query = "SELECT COUNT(*) FROM aircraft a"
        count_conditions = []
        count_params = {}

        if filter_type == "airline" and airline_id:
            count_conditions.append("a.AirlineID = :airline_id")
            count_params["airline_id"] = airline_id
        elif filter_type == "registration" and registration:
            count_conditions.append("a.Registration LIKE :registration")
            count_params["registration"] = f"%{registration}%"

        if count_conditions:
            count_query += " WHERE " + " AND ".join(count_conditions)

        total_aircraft = db.session.execute(
            text(count_query), count_params
        ).scalar() or 0
        total_pages = max(ceil(total_aircraft / PER_PAGE), 1)

        # Data query
        data_query = """
            SELECT a.*, al.AirlineName,
                   a.First_Sighted, a.Aircraft_Updated AS Timestamp
            FROM aircraft a
            LEFT JOIN airlines al ON a.AirlineID = al.AirlineID
        """
        where_clauses = []
        query_params = {"limit": PER_PAGE, "offset": offset}

        if filter_type == "airline" and airline_id:
            where_clauses.append("a.AirlineID = :airline_id")
            query_params["airline_id"] = airline_id
        elif filter_type == "registration" and registration:
            where_clauses.append("a.Registration LIKE :registration")
            query_params["registration"] = f"%{registration}%"

        if where_clauses:
            data_query += " WHERE " + " AND ".join(where_clauses)

        data_query += " ORDER BY a.Aircraft_Updated DESC LIMIT :limit OFFSET :offset"

        result = db.session.execute(text(data_query), query_params)
        rows = result.fetchall()
        columns = result.keys()

        aircraft_records = []
        for row in rows:
            record = dict(zip(columns, row))

            # Format timestamps
            for field, key in [("First_Sighted", "First_Sighted_Display"), ("Timestamp", "Aircraft_Updated_Display")]:
                dt = record.get(field)
                if dt:
                    if isinstance(dt, date) and not isinstance(dt, datetime):
                        dt = datetime.combine(dt, datetime.min.time())
                    dt = dt.replace(tzinfo=pytz.utc).astimezone(timezone)
                    record[key] = dt.strftime('%d-%m-%Y %H:%M:%S')
                else:
                    record[key] = "Unknown"

            # Airport formatting
            record["Departure_Display"] = airport_display(record.get("Departure"))
            record["Arrival_Display"] = airport_display(record.get("Arrival"))

            # Normalize for display
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, date):
                    record[key] = value.strftime("%Y-%m-%d")
                elif value is None:
                    record[key] = "Unknown"

            # Country flag
            record["Country_Flag"] = get_country_flag(record.get("Country_of_Reg"))

            aircraft_records.append(record)

        # Pagination block
        BLOCK_SIZE = 10
        current_block = (current_page - 1) // BLOCK_SIZE
        start_page = current_block * BLOCK_SIZE + 1
        end_page = min(start_page + BLOCK_SIZE - 1, total_pages)
        next_block_page = min(end_page + 1, total_pages)
        prev_block_page = max(start_page - BLOCK_SIZE, 1)

        return render_template(
            "aircraft_table.html",
            filtered_aircraft=aircraft_records,
            current_page=current_page,
            total_pages=total_pages,
            current_year=datetime.now().year,
            start_page=start_page,
            end_page=end_page,
            prev_block_page=prev_block_page,
            next_block_page=next_block_page
        )

    except Exception as e:
        logging.error("❌ Error loading aircraft_table:")
        import traceback
        logging.error(traceback.format_exc())
        flash("Error loading aircraft table.", "danger")
        return redirect(url_for("aircraft.aircraft_table"))
