from flask import Blueprint, render_template, request, url_for
from sqlalchemy import text
from extensions import db
from utils.country_flags import get_country_flag
from utils.timezone_utils import get_current_timezone
from utils.airport_utils import format_airport_display as airport_display
import pytz
from datetime import datetime, date

search_bp = Blueprint('search', __name__)

@search_bp.route("/search_unified")
def search_unified():
    search_type = request.args.get("type")
    search_query = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtered_data = []
    total_pages = 1
    like_query = f"%{search_query.lower()}%"

    if search_type == "aircraft":
        count_result = db.session.execute(text("""
            SELECT COUNT(*) FROM aircraft a
            LEFT JOIN airlines al ON a.AirlineID = al.AirlineID
            WHERE LOWER(a.Registration) LIKE :q OR LOWER(a.FlightNumber) LIKE :q
               OR LOWER(a.Aircraft_Type) LIKE :q OR LOWER(a.Departure) LIKE :q
               OR LOWER(a.Arrival) LIKE :q OR LOWER(a.Country_of_Reg) LIKE :q
               OR LOWER(al.AirlineName) LIKE :q
        """), {"q": like_query}).scalar()
        total_pages = max(1, (count_result + per_page - 1) // per_page)

        result = db.session.execute(text("""
            SELECT a.AircraftID, a.Registration, a.FlightNumber, a.Aircraft_Type, 
                   a.Departure, a.Arrival, a.Country_of_Reg,
                   a.First_Sighted, a.Aircraft_Updated AS Timestamp,
                   al.AirlineName
            FROM aircraft a
            LEFT JOIN airlines al ON a.AirlineID = al.AirlineID
            WHERE LOWER(a.Registration) LIKE :q OR LOWER(a.FlightNumber) LIKE :q
               OR LOWER(a.Aircraft_Type) LIKE :q OR LOWER(a.Departure) LIKE :q
               OR LOWER(a.Arrival) LIKE :q OR LOWER(a.Country_of_Reg) LIKE :q
               OR LOWER(al.AirlineName) LIKE :q
            ORDER BY a.Aircraft_Updated DESC
            LIMIT :limit OFFSET :offset
        """), {"q": like_query, "limit": per_page, "offset": offset})

        timezone = get_current_timezone()

        for row in result:
            aircraft = dict(row._mapping)

            # Format timestamps
            dt = aircraft.get("First_Sighted")
            if dt:
                if isinstance(dt, date) and not isinstance(dt, datetime):
                    dt = datetime.combine(dt, datetime.min.time())
                dt = dt.replace(tzinfo=pytz.utc).astimezone(timezone)
                aircraft["First_Sighted_Display"] = dt.strftime('%d-%m-%Y %H:%M:%S')
            else:
                aircraft["First_Sighted_Display"] = "Unknown"

            dt = aircraft.get("Timestamp")
            if dt:
                if isinstance(dt, date) and not isinstance(dt, datetime):
                    dt = datetime.combine(dt, datetime.min.time())
                dt = dt.replace(tzinfo=pytz.utc).astimezone(timezone)
                aircraft["Last_Sighted_Display"] = dt.strftime('%d-%m-%Y %H:%M:%S')
            else:
                aircraft["Last_Sighted_Display"] = "Unknown"

            aircraft["Departure_Display"] = airport_display(aircraft.get("Departure"))
            aircraft["Arrival_Display"] = airport_display(aircraft.get("Arrival"))
            aircraft["Country_Flag"] = get_country_flag(aircraft.get("Country_of_Reg"))

            filtered_data.append(aircraft)

        return render_template("partials/_aircraft_table_rows.html",
                               filtered_aircraft=filtered_data,
                               total_pages=total_pages,
                               current_page=page,
                               search_query=search_query)

    elif search_type == "airline":
        count_result = db.session.execute(text("""
            SELECT COUNT(*) FROM airlines
            WHERE LOWER(AirlineName) LIKE :q
        """), {"q": like_query}).scalar()
        total_pages = max(1, (count_result + per_page - 1) // per_page)

        result = db.session.execute(text("""
            SELECT al.AirlineID, al.AirlineName,
                   COUNT(a.AircraftID) AS TotalAircraft
            FROM airlines al
            LEFT JOIN aircraft a ON al.AirlineID = a.AirlineID
            WHERE LOWER(al.AirlineName) LIKE :q
            GROUP BY al.AirlineID, al.AirlineName
            ORDER BY al.AirlineName ASC
            LIMIT :limit OFFSET :offset
        """), {"q": like_query, "limit": per_page, "offset": offset})

        for row in result:
            airline = dict(row._mapping)
            filtered_data.append(airline)

        return render_template("partials/filtered_airlines.html",
                               filtered_airlines=filtered_data,
                               total_pages=total_pages,
                               current_page=page,
                               search_query=search_query)

    return "Search type not supported", 400
