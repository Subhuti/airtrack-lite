import os
import sys
import time
import json
import math
import pwd
import grp
import pytz
import traceback
import logging
from datetime import datetime, date
from math import ceil
from zoneinfo import ZoneInfo
from urllib.parse import unquote_plus
from flask import Flask, render_template, redirect, url_for, send_from_directory, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from models.aircraft import Aircraft
from utils.country_flags import get_country_flag

load_dotenv()

# Import the central db instance from extensions
from extensions import db

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Configuration (loaded from environment or Docker Compose)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mariadb+mariadbconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'fallback-hardcoded-key')  # ✅ Replace in .env

# Bind SQLAlchemy
from extensions import db
db.init_app(app)

def get_app_timezone():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT timezone FROM app_settings LIMIT 1")).scalar()
            return pytz.timezone(result) if result else pytz.utc
    except Exception as e:
        print(f"⚠️ Failed to fetch timezone from DB: {e}")
        return pytz.utc

class DBTimezoneFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.tz = get_app_timezone()

    def converter(self, timestamp):
        utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.utc)
        return utc_dt.astimezone(self.tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

# Set up formatter and attach to root logger
formatter = DBTimezoneFormatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S %Z")

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)

for handler in logging.root.handlers:
    handler.setFormatter(formatter)

# Create engine after app is bound
with app.app_context():
    engine = db.engine

# Template cache-busting
@app.context_processor
def inject_time():
    return {'time': time.time}

from utils.timezone_utils import convert_to_local

# Import all blueprints
from routes.aircraft_routes import aircraft_bp
from routes.airlines_routes import airlines_bp
from routes.reports_routes import reports_bp
from routes.airports_routes import airports_bp
from routes.aircraft_info_route import aircraft_info_bp
from routes.add_aircraft_routes import add_aircraft_bp
from routes.edit_aircraft_routes import edit_aircraft_bp
from routes.flight_history_routes import flight_history_bp
from routes.search_routes import search_bp


# Register all blueprints
app.register_blueprint(aircraft_bp)
app.register_blueprint(airlines_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(airports_bp)
app.register_blueprint(aircraft_info_bp)
app.register_blueprint(add_aircraft_bp)
app.register_blueprint(edit_aircraft_bp)
app.register_blueprint(flight_history_bp)
app.register_blueprint(search_bp)

from utils.country_flags import get_country_flag
app.jinja_env.globals['get_country_flag'] = get_country_flag

@app.context_processor
def inject_get_country_flag():
    return dict(get_country_flag=get_country_flag)

# Register template filters (minimal addition)
from routes.airports_routes import register_filters
register_filters(app)

# Configuration (using environment variables from Docker Compose)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mariadb+mariadbconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config['DEBUG'] = True
app.config['TESTING'] = False
app.secret_key = os.getenv('SECRET_KEY', "fallback-hardcoded-key")  # Replace with actual key for production

# Create the engine inside an application context
with app.app_context():
    engine = db.engine  # This will now be properly initialized within an app context

# ----------- AIRCRAFT AND AIRLINE FUNCTIONS -----------

# Get airlines with aircraft count
def get_airlines_with_aircraft_count():
    conn = get_db_connection()
    if conn is None:
        logging.error("❌ Failed to connect to the database.")
        return []

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT al.AirlineID, al.AirlineName,
                   COUNT(ac.AircraftID) AS AircraftCount
            FROM airlines al
            LEFT JOIN aircraft ac ON al.AirlineID = ac.AirlineID
            GROUP BY al.AirlineID, al.AirlineName
            ORDER BY al.AirlineName
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return result
    except Exception as e:
        logging.error(f"❌ Error getting airlines with aircraft count: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        conn.close()

# ----------- STATS FUNCTIONS -----------

def get_airtrack_stats():
    try:
        with engine.connect() as conn:
            total_aircraft = conn.execute(text("SELECT COUNT(*) FROM aircraft")).scalar()
            total_flights = conn.execute(text("SELECT COUNT(*) FROM flights")).scalar()
            total_airlines = conn.execute(text("SELECT COUNT(*) FROM airlines")).scalar()
            models_seen = conn.execute(text("SELECT COUNT(DISTINCT Aircraft_Type) FROM aircraft WHERE Aircraft_Type IS NOT NULL AND Aircraft_Type != ''")).scalar()
            photos_logged = conn.execute(text("SELECT COUNT(*) FROM aircraft WHERE Aircraft_Image IS NOT NULL AND Aircraft_Image != ''")).scalar()
            total_countries = conn.execute(text("SELECT COUNT(DISTINCT Country_of_Reg) FROM aircraft WHERE Country_of_Reg IS NOT NULL AND Country_of_Reg != ''")).scalar()
            
            # Add orphaned aircraft count
            orphaned_aircraft = conn.execute(text("SELECT COUNT(*) FROM aircraft WHERE AirlineID IS NULL OR AirlineID = ''")).scalar()
            
            # Add airports count
            departures = conn.execute(text("SELECT DISTINCT Departure FROM aircraft WHERE Departure IS NOT NULL AND Departure != ''")).fetchall()
            arrivals = conn.execute(text("SELECT DISTINCT Arrival FROM aircraft WHERE Arrival IS NOT NULL AND Arrival != ''")).fetchall()
            
            all_airports = set()
            for d in departures:
                if d[0]:
                    all_airports.add(d[0])
            for a in arrivals:
                if a[0]:
                    all_airports.add(a[0])
            
            airports_logged = len(all_airports)

            return {
                "total_aircraft": total_aircraft,
                "total_flights": total_flights,
                "total_airlines": total_airlines,
                "models_seen": models_seen,
                "photos_logged": photos_logged,
                "total_countries": total_countries,
                "orphaned_aircraft": orphaned_aircraft,
                "airports_logged": airports_logged
            }
    except Exception as e:
        app.logger.error(f"Error fetching admin stats: {e}")
        return {
            "total_aircraft": 0,
            "total_flights": 0,
            "total_airlines": 0,
            "models_seen": 0,
            "photos_logged": 0,
            "total_countries": 0,
            "orphaned_aircraft": 0,
            "airports_logged": 0
        }

# ----------- DATABASE FUNCTIONS -----------

def execute_query(query, params=None):
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logging.error(f"❌ SQLAlchemy error: {e}")
        return None

from sqlalchemy import text

# Get a database connection using SQLAlchemy
def get_db_connection():
    try:
        return db.engine.connect()
    except Exception as e:
        logging.error(f"❌ SQLAlchemy connection error: {e}")
        return None

# ----------- UPDATE FUNCTIONS -----------

from sqlalchemy import text

# Update First_Sighted where null using SQLAlchemy
def update_first_sighted():
    try:
        with db.engine.begin() as conn:
            update_query = """
                UPDATE aircraft
                SET First_Sighted = Aircraft_Updated
                WHERE First_Sighted IS NULL AND Aircraft_Updated IS NOT NULL;
            """
            result = conn.execute(text(update_query))
            print(f"First_Sighted dates updated successfully. Rows affected: {result.rowcount}")
    except Exception as e:
        print(f"Error updating First_Sighted dates: {e}")

@app.route("/reports")
def reports():
    try:
        with engine.connect() as conn:
            query = text("SELECT show_disclaimer FROM settings WHERE id = 1")
            result = conn.execute(query).fetchone()
            show_disclaimer = result[0] if result else True

        from utils.timezone_utils import convert_to_local
        current_year = convert_to_local(datetime.utcnow()).year

        return render_template("reports.html", show_disclaimer=show_disclaimer, current_year=current_year)

    except Exception as e:
        logging.error(f"❌ Error checking disclaimer preference: {e}")
        return "Internal Server Error", 500

@app.route("/")
def root_redirect():
    return redirect(url_for("splash"))

@app.route("/splash", methods=["GET"])
def splash():
    current_time = datetime.now().timestamp()  # Get the current timestamp
    return render_template('splash.html', current_time=current_time)

@app.context_processor
def inject_globals():
    return dict(max=max, min=min)

@app.route("/index", methods=["GET", "POST"])
def index():
    current_year = convert_to_local(datetime.utcnow()).year

    try:
        airlines_list = []
        filtered_aircraft = []
        selected_airline_name = ""
        total_airlines = 0
        total_aircraft = 0
        filtered_total_aircraft = 0
        no_aircraft_message = ""
        total_pages = 1
        page = request.args.get("page", 1, type=int)
        per_page = 10

        with db.engine.connect() as conn:
            total_airlines = conn.execute(text("SELECT COUNT(*) FROM airlines")).scalar() or 0
            total_aircraft = conn.execute(text("SELECT COUNT(*) FROM aircraft")).scalar() or 0

            airlines_query = text("SELECT AirlineID, AirlineName FROM airlines ORDER BY AirlineName")
            airlines = conn.execute(airlines_query).fetchall()

            airlines_list = [{"AirlineID": row[0], "AirlineName": row[1]} for row in airlines]

            if not airlines_list:
                logging.warning("⚠️ No airlines found in the database!")

        return render_template(
            "index.html",
            total_airlines=total_airlines,
            total_aircraft=total_aircraft,
            airlines=airlines_list,
            filtered_aircraft=filtered_aircraft,
            selected_airline_name=selected_airline_name,
            filtered_total_aircraft=filtered_total_aircraft,
            no_aircraft_message=no_aircraft_message,
            current_page=page,
            total_pages=total_pages,
            current_year=current_year
        )

    except Exception as e:
        logging.exception(f"❌ Error in index route: {e}")
        flash("An error occurred. Please try again later.", "danger")
        return render_template(
            "index.html",
            airlines=[],
            total_pages=1,
            current_page=1,
            current_year=current_year
        )

@app.route("/upload_aircraft_image", methods=["GET", "POST"])
def upload_aircraft_image():
    if request.method == "POST":
        registration = request.form.get("registration")
        image = request.files.get("image")

        if not registration or not image:
            flash("Registration and image are required.", "danger")
            return redirect(url_for("upload_aircraft_image"))

        filename = f"{registration}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        image.save(os.path.join("static/aircraft_images", filename))

        try:
            with db.engine.begin() as conn:
                update_sql = text("""
                    UPDATE aircraft
                    SET Aircraft_Image = :filename
                    WHERE Registration = :registration
                """)
                conn.execute(update_sql, {
                    "filename": filename,
                    "registration": registration
                })
            flash("Image uploaded successfully!", "success")
        except Exception as e:
            flash("Failed to update image in database.", "danger")
            print(f"❌ DB Error: {e}")

        return redirect(url_for("aircraft.aircraft_table"))

    return render_template("upload_aircraft_image.html")

from flask import current_app
from utils.country_flags import get_country_list

@app.route('/delete_image/<int:aircraft_id>', methods=['POST'])
def delete_image(aircraft_id):
    aircraft = Aircraft.query.get(aircraft_id)

    if aircraft and aircraft.Aircraft_Image:
        image_path = os.path.join(current_app.root_path, 'static', 'aircraft_images', aircraft.Aircraft_Image)
        if os.path.exists(image_path):
            os.remove(image_path)

        aircraft.Aircraft_Image = None
        db.session.commit()
        flash('Aircraft image deleted successfully.', 'success')
    else:
        flash('No image found for this aircraft.', 'danger')

    return redirect(url_for('aircraft.aircraft_table'))


@app.route('/get_registrations/<int:airline_id>')
def get_registrations(airline_id):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT Registration FROM aircraft
                WHERE AirlineID = :airline_id
                ORDER BY Registration ASC
            """), {"airline_id": airline_id})
            registrations = [{"Registration": row.Registration} for row in result.fetchall()]
            return jsonify(registrations)
    except Exception as e:
        app.logger.error(f"❌ Error fetching registrations: {e}")
        return jsonify([]), 500

@app.route("/airlines")
def airlines():
    per_page = 10
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("search", "").strip()
    airline_filter = request.args.get("airline", "").strip()
    offset = (page - 1) * per_page
    airlines_list = []
    total_count = 0
    total_pages = 1

    try:
        with engine.connect() as conn:
            count_query = text("""
                SELECT COUNT(*) 
                FROM airlines
                WHERE AirlineName LIKE :search OR :airline_filter = ''
            """)
            total_count = conn.execute(count_query, {
                "search": f"%{search_query}%",
                "airline_filter": airline_filter
            }).scalar()

            total_pages = max(1, (total_count + per_page - 1) // per_page)

            airlines_query = text("""
                SELECT a.AirlineID, a.AirlineName, COUNT(f.AircraftID) AS TotalAircraft
                FROM airlines a
                LEFT JOIN aircraft f ON a.AirlineID = f.AirlineID
                WHERE a.AirlineName LIKE :search OR :airline_filter = ''
                GROUP BY a.AirlineID, a.AirlineName
                ORDER BY a.AirlineName ASC
                LIMIT :limit OFFSET :offset
            """)
            airlines = conn.execute(airlines_query, {
                "search": f"%{search_query}%",
                "airline_filter": airline_filter,
                "limit": per_page,
                "offset": offset
            }).fetchall()

            airlines_list = [dict(row._mapping) for row in airlines]

        current_year = datetime.now().year

    except Exception as e:
        logging.error(f"❌ Error retrieving airlines: {e}")
        flash("An error occurred while fetching airlines.", "danger")
        current_year = datetime.now().year

    return render_template(
        "airlines_table.html",
        airlines=airlines_list,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        search_query=search_query,
        airline_filter=airline_filter,
        start_page=max(1, page - 2),
        end_page=min(total_pages, page + 2),
        current_year=current_year
    )

@app.route("/delete_flight/<int:flight_id>", methods=["POST"])
def delete_flight(flight_id):
    try:
        with db.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM flights WHERE FlightID = :id"),
                {"id": flight_id}
            )
        flash("Flight deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting flight: {e}", "danger")

    return redirect(url_for("aircraft_info", aircraft_id=flight_id))

@app.route("/delete_aircraft/<int:aircraft_id>", methods=["POST"])
def delete_aircraft(aircraft_id):
    try:
        with db.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM aircraft WHERE AircraftID = :id"),
                {"id": aircraft_id}
            )
        flash("Aircraft deleted successfully!", "success")
    except Exception as e:
        logging.error(f"❌ Error deleting aircraft: {e}")
        flash("An error occurred while deleting the aircraft.", "danger")

    return redirect(url_for("aircraft.aircraft_table"))

@app.route("/orphaned_aircraft")
def orphaned_aircraft():
    try:
        with db.engine.connect() as conn:
            # Count orphaned aircraft
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM aircraft WHERE AirlineID IS NULL")
            ).scalar()

            # Fetch orphaned aircraft details
            results = conn.execute(text("""
                SELECT a.*, al.AirlineName
                FROM aircraft a
                LEFT JOIN airlines al ON a.AirlineID = al.AirlineID
                WHERE a.Orphaned = 1
                ORDER BY a.Aircraft_Updated DESC
            """))

            orphaned_list = [dict(row._mapping) for row in results]

    except Exception as e:
        logging.error(f"❌ Error loading orphaned aircraft: {e}")
        flash("Failed to load orphaned aircraft.", "danger")
        return redirect(url_for("index"))

    return render_template(
        "orphaned_aircraft.html",
        orphaned_aircraft=orphaned_list,
        orphaned_aircraft_count=count_result
    )

def get_all_airlines():
    conn = get_db_connection()
    if conn is None:
        logging.error("❌ Failed to get DB connection in get_all_airlines.")
        return []

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT AirlineID, AirlineName FROM airlines ORDER BY AirlineName")
        rows = cursor.fetchall()
        return [{"AirlineID": row[0], "AirlineName": row[1]} for row in rows]
    except Exception as e:
        logging.error(f"❌ Error in get_all_airlines: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/airline_info/<int:airline_id>")
def airline_info(airline_id):
    """Display details for a specific airline."""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT AirlineID, AirlineName, Last_Updated
                FROM airlines
                WHERE AirlineID = :airline_id
            """), {"airline_id": airline_id}).fetchone()

            if result:
                airline_data = dict(result._mapping)
            else:
                return "Airline Not Found", 404

    except Exception as e:
        logging.error(f"❌ Error retrieving airline info: {e}")
        return "Internal Server Error", 500

    return render_template("airline_info.html", airline=airline_data)


@app.route("/flight_history/<int:aircraft_id>")
def flight_history(aircraft_id):
    try:
        with db.engine.connect() as conn:
            # Get flight history
            result = conn.execute(text("""
                SELECT * FROM flights
                WHERE AircraftID = :aircraft_id
                ORDER BY Timestamp DESC
            """), {"aircraft_id": aircraft_id})
            columns = result.keys()
            history = [dict(zip(columns, row)) for row in result.fetchall()]

            # Get registration
            reg_result = conn.execute(text("""
                SELECT Registration FROM aircraft WHERE AircraftID = :aircraft_id
            """), {"aircraft_id": aircraft_id}).fetchone()
            aircraft = {"Registration": reg_result[0]} if reg_result else {}

            for flight in history:
                flight["Spotted_At"] = flight.get("Spotted_At") or "Unknown"
                ts = flight.get("Timestamp") or flight.get("timestamp")
                if isinstance(ts, datetime):
                    flight["local_timestamp"] = ts.strftime("%d-%m-%Y %H:%M:%S")
                else:
                    flight["local_timestamp"] = "N/A"

        return render_template("flight_history.html", history=history, aircraft=aircraft)

    except Exception as e:
        logging.error(f"❌ Error loading flight history for aircraft {aircraft_id}: {e}")
        flash("Failed to load flight history.", "danger")
        return redirect(url_for("index"))

@app.route("/aircraft_info/<int:aircraft_id>")
def aircraft_info(aircraft_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 10

        with engine.connect() as conn:
            query_aircraft = text("""
                SELECT ac.*, ac.ICAO_Address, al.AirlineName, 
                       au.aircraftmanufacturer, au.aircraftmodel, au.msn AS serial, au.maxtakeoffweight,
                       au.enginecount, au.enginemanufacturer, au.enginetype, au.enginemodel, au.fueltype, 
                       au.registrationtype, au.registeredowner, au.registeredownercountry, 
                       au.operatorname, au.operatorcountry, au.firstregistrationdate,
                       au.airframe, au.propmanu, au.propmodel, au.typecert, au.countrymanu, 
                       au.yearmanu,
                       ur.mfr_mdl_code AS us_model_code, ur.serial_number AS us_serial,
                       ur.eng_mfr_mdl AS us_engine, ur.year_mfr AS us_year,
                       ur.certification AS us_cert, ur.status_code AS us_status,
                       ur.mode_s_hex AS us_hex, ur.air_worth_date AS us_airworthy,
                       ac.Aircraft_Updated
                FROM aircraft ac
                LEFT JOIN airlines al ON ac.AirlineID = al.AirlineID
                LEFT JOIN australia au ON ac.Registration = au.Registration
                LEFT JOIN united_states ur ON ac.Registration = CONCAT('N', ur.n_number)
                WHERE ac.AircraftID = :AircraftID
            """)
            result = conn.execute(query_aircraft, {"AircraftID": aircraft_id}).fetchone()
            aircraft = dict(result._mapping) if result else None

            if not aircraft:
                flash("Aircraft not found.", "danger")
                return redirect(url_for("aircraft_table"))

            aircraft["Registration"] = aircraft["Registration"].strip().rstrip("-").rstrip()
            aircraft["AirlineName"] = aircraft.get("AirlineName", "Unknown")

            msn = aircraft.get("MSN")

            first_sighted = aircraft.get("First_Sighted")
            if first_sighted and first_sighted != "Unknown":
                if isinstance(first_sighted, date) and not isinstance(first_sighted, datetime):
                    first_sighted = datetime.combine(first_sighted, datetime.min.time())
                aircraft["First_Seen_Display"] = first_sighted.strftime('%d-%m-%Y %H:%M:%S')
            else:
                aircraft["First_Seen_Display"] = "Unknown"

            updated = aircraft.get("Aircraft_Updated")
            if updated and updated != "Unknown":
                if isinstance(updated, date) and not isinstance(updated, datetime):
                    updated = datetime.combine(updated, datetime.min.time())
                aircraft["Last_Sighted_Display"] = updated.strftime('%d-%m-%Y %H:%M:%S')
            else:
                aircraft["Last_Sighted_Display"] = "Unknown"

            spotted_at = aircraft.get("Spotted_At")
            aircraft["Spotted_At_Display"] = spotted_at if spotted_at else "Unknown"

            icao_address = aircraft.get("ICAO_Address")
            aircraft["ICAO_Address_Display"] = icao_address if icao_address else "Unknown"

            latest_query = text("""
                SELECT Departure, Arrival
                FROM flights
                WHERE MSN = :MSN OR Registration = :Registration
                ORDER BY Timestamp DESC
                LIMIT 1
            """)
            result = conn.execute(latest_query, {"MSN": msn, "Registration": aircraft["Registration"]}).fetchone()

            if result:
                latest = dict(result._mapping)
                aircraft["Departure"] = latest.get("Departure")
                aircraft["Arrival"] = latest.get("Arrival")

            history_query = text("""
                SELECT FlightID, FlightNumber, Departure, Arrival, Timestamp, Spotted_At
                FROM flights
                WHERE MSN = :MSN OR Registration = :Registration
                ORDER BY Timestamp DESC
            """)

            history_results = conn.execute(history_query, {"MSN": msn, "Registration": aircraft["Registration"]}).fetchall()

            full_history = []
            for row in history_results:
                flight = dict(row._mapping)
                ts = flight.get("Timestamp")
                if ts:
                    if isinstance(ts, date) and not isinstance(ts, datetime):
                        ts = datetime.combine(ts, datetime.min.time())
                    flight["Timestamp"] = ts.strftime('%d-%m-%Y %H:%M:%S')

                spotted = flight.get("Spotted_At")
                flight["Spotted_At"] = spotted if spotted else "Unknown"

                full_history.append(flight)

            total_flights = len(full_history)
            total_pages = ceil(total_flights / per_page)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_flights = full_history[start:end]

            return render_template(
                "aircraft_info.html",
                aircraft=aircraft,
                flight_history=paginated_flights,
                current_page=page,
                total_pages=total_pages,
                current_year=datetime.now().year
            )

    except Exception as e:
        logging.error(f"❌ Error fetching aircraft info: {e}")
        flash("Database error occurred.", "danger")
        return redirect(url_for("aircraft_table"))

@app.route("/aircraft_info_help/<int:aircraft_id>")
def aircraft_info_help(aircraft_id):
    return render_template("aircraft_info_help.html", aircraft_id=aircraft_id)

@app.route("/edit_airline/<int:airline_id>", methods=["GET", "POST"])
def edit_airline(airline_id):
    try:
        with engine.begin() as conn:
            # Fetch airline details
            airline_query = text("SELECT * FROM airlines WHERE AirlineID = :airline_id")
            airline = conn.execute(airline_query, {"airline_id": airline_id}).mappings().fetchone()

            print(f"🚀 Airline Data Retrieved: {airline}")  # Debugging statement

            if not airline:
                flash("Airline not found.", "danger")
                return redirect(url_for('airlines'))

            if request.method == "POST":
                # Debugging statement to track form submission
                print(f"📥 Form Submitted: {request.form}")

                # Get the form data
                airline_name = request.form.get("airlineName", "").strip()
                print(f"✍️ Attempting to update airline with name: {airline_name}")

                if not airline_name:
                    flash("Airline name cannot be empty.", "danger")
                    return redirect(url_for('edit_airline', airline_id=airline_id))

                # Update query to modify the airline name
                update_query = text("""
                    UPDATE airlines
                    SET AirlineName = :AirlineName
                    WHERE AirlineID = :AirlineID
                """)
                conn.execute(update_query, {"AirlineName": airline_name, "AirlineID": airline_id})

                print(f"✈️ Airline {airline_id} updated to {airline_name}")

                flash("Airline updated successfully!", "success")
                return redirect(url_for('airlines'))

            # If GET request, send the data to the template
            return render_template("edit_airline.html", airline=airline)

    except Exception as e:
        print(f"❌ Error editing airline: {e}")
        flash("An error occurred while editing the airline.", "danger")
        return redirect(url_for('airlines'))

@app.route('/update_airline', methods=['POST'])
def update_airline():
    """Update airline name in the database."""
    try:
        airline_id = request.form.get('airline_id')
        airline_name = request.form.get('airline_name', '').strip()

        if not airline_id or not airline_name:
            flash("Error: Missing airline details.", "danger")
            return redirect(url_for('airlines'))

        with db.engine.begin() as conn:
            conn.execute(text("""
                UPDATE airlines 
                SET AirlineName = :airline_name 
                WHERE AirlineID = :airline_id
            """), {"airline_name": airline_name, "airline_id": airline_id})

        flash("Airline updated successfully!", "success")
        return redirect(url_for('airlines'))

    except Exception as e:
        logging.error(f"❌ Error updating airline: {e}")
        flash(f"Error updating airline: {e}", "danger")
        return redirect(url_for('airlines'))

@app.route("/delete_airline/<int:airline_id>", methods=["POST"])
def delete_airline(airline_id):
    """Delete an airline by its ID."""
    try:
        # Get the delete_option from the form submission
        delete_option = request.form.get('delete_option')
        print(f"🔧 Deletion option selected: {delete_option}")  # For debugging

        with db.engine.begin() as conn:
            existing = conn.execute(text("SELECT * FROM airlines WHERE AirlineID = :airline_id"), {"airline_id": airline_id}).fetchone()
            if not existing:
                flash("Airline not found.", "warning")
                return redirect(url_for("airlines"))

            if delete_option == 'full':  # Delete airline and aircraft
                # Delete the airline and all associated aircraft
                delete_query = text("DELETE FROM airlines WHERE AirlineID = :airline_id")
                conn.execute(delete_query, {"airline_id": airline_id})
                result = conn.execute(delete_query, {"airline_id": airline_id})
                print(f"🔧 Airline rows deleted: {result.rowcount}")
                delete_aircraft_query = text("DELETE FROM aircraft WHERE AirlineID = :airline_id")
                conn.execute(delete_aircraft_query, {"airline_id": airline_id})
                result = conn.execute(delete_query, {"airline_id": airline_id})
                print(f"🔧 Airline rows deleted: {result.rowcount}")
                flash("Airline and associated aircraft deleted successfully!", "success")
            elif delete_option == 'orphan':  # Delete airline but keep aircraft
                # Set all associated aircraft's AirlineID to NULL (orphaned)
                orphan_aircraft_query = text("""
                    UPDATE aircraft
                    SET AirlineID = NULL
                    WHERE AirlineID = :airline_id
                """)
                conn.execute(orphan_aircraft_query, {"airline_id": airline_id})
                result = conn.execute(delete_query, {"airline_id": airline_id})
                print(f"🔧 Airline rows deleted: {result.rowcount}")
                # Now delete the airline
                delete_query = text("DELETE FROM airlines WHERE AirlineID = :airline_id")
                conn.execute(delete_query, {"airline_id": airline_id})
                result = conn.execute(delete_query, {"airline_id": airline_id})
                print(f"🔧 Airline rows deleted: {result.rowcount}")
                flash("Airline deleted, aircraft orphaned.", "success")
            else:
                flash("Invalid delete option.", "danger")

            conn.commit()  # Ensure changes are saved to the database

    except Exception as e:
        logging.error(f"❌ Error deleting airline {airline_id}: {e}")
        flash("Error deleting airline.", "danger")

    return redirect(url_for("airlines"))

@app.template_filter("format_datetime")
def format_datetime(value):
    """Format datetime values consistently with Sydney timezone."""
    if value is None:
        return "N/A"
    if isinstance(value, datetime):
        sydney = pytz.timezone("Australia/Sydney")
        value = value.astimezone(sydney)
        return value.strftime("%d %B %Y - %H:%M:%S")
    return value

@app.route("/get_disclaimer_status")
def get_disclaimer_status():
    """Return whether the disclaimer should be shown."""
    try:
        with engine.connect() as conn:
            query = text("SELECT show_disclaimer FROM settings WHERE id = 1")
            result = conn.execute(query).fetchone()

            show_disclaimer = bool(result[0]) if result else True
            return jsonify({"show_disclaimer": show_disclaimer})

    except Exception as e:
        logging.error(f"❌ Error fetching disclaimer status: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/hide_disclaimer", methods=["POST"])
def hide_disclaimer():
    """Update the setting to hide the disclaimer."""
    try:
        with engine.connect() as conn:
            query = text("UPDATE settings SET show_disclaimer = FALSE WHERE id = 1")
            conn.execute(query)
            conn.commit()

        return jsonify({"message": "Disclaimer hidden successfully"}), 200

    except Exception as e:
        logging.error(f"❌ Error updating disclaimer preference: {e}")
        return jsonify({"error": "Database error"}), 500

# Start of Admin Functions #

@app.route("/admin/backup", methods=["POST"])
def backup_database():
    try:
        APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
        backup_dir = os.path.join(APP_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"airtrack_backup_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)

        dump_command = (
            f"mysqldump -h {os.getenv('DB_HOST')} -u {os.getenv('DB_USER')} "
            f"-p{os.getenv('DB_PASSWORD')} {os.getenv('DB_NAME')} > {filepath}"
        )

        result = os.system(dump_command)

        if result == 0:
            # Fix file ownership
            os.chown(filepath, os.getuid(), os.getgid())
            logging.info(f"✅ Database backup saved to: {filepath}")
            flash(f"Database backed up as {filename}", "success")
        else:
            raise RuntimeError("mysqldump failed.")

    except Exception as e:
        logging.error(f"❌ Backup error: {e}")
        flash("Failed to backup database.", "danger")

    return redirect(url_for("admin_panel"))

@app.route("/admin/restore", methods=["POST"])
def restore_database():
    try:
        import subprocess
        from glob import glob

        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        backup_files = sorted(
            glob(os.path.join(backup_dir, "*.sql")),
            key=os.path.getmtime,
            reverse=True
        )

        if not backup_files:
            flash("No backup files found to restore.", "danger")
            return redirect(url_for("admin_panel"))

        latest_backup = backup_files[0]
        logging.info(f"♻️ Restoring database from: {latest_backup}")

        restore_command = [
            "mysql",
            f"-h{os.getenv('DB_HOST')}",
            f"-u{os.getenv('DB_USER')}",
            f"-p{os.getenv('DB_PASSWORD')}",
            os.getenv('DB_NAME')
        ]

        with open(latest_backup, "rb") as backup_file:
            result = subprocess.run(restore_command, stdin=backup_file)

        if result.returncode == 0:
            flash(f"Database restored successfully from {os.path.basename(latest_backup)}", "success")
        else:
            raise RuntimeError("mysql restore failed.")

    except Exception as e:
        logging.error(f"❌ Restore error: {e}")
        flash("Failed to restore database.", "danger")

    return redirect(url_for("admin_panel"))

@app.route("/admin/flush_backups", methods=["POST"])
def flush_backups():
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        files = [f for f in os.listdir(backup_dir) if f.endswith(".sql")]

        if not files:
            flash("No backups to delete.", "info")
            return redirect(url_for("admin_panel"))

        for f in files:
            os.remove(os.path.join(backup_dir, f))

        flash("All backup files deleted.", "warning")
    except Exception as e:
        logging.error(f"❌ Error flushing backups: {e}")
        flash("Failed to flush backups.", "danger")
    return redirect(url_for("admin_panel"))

@app.route("/admin/flush_logs", methods=["POST"])
def flush_logs():
    try:
        # Replace this with your real log-flushing logic
        open("logs/airtrack.log", "w").close()  # example if you're using a flat log file
        logging.info("🧹 Logs flushed by admin.")
        flash("Logs flushed successfully!", "success")
    except Exception as e:
        logging.error(f"❌ Log flush error: {e}")
        flash("Failed to flush logs.", "danger")
    return redirect(url_for("admin_panel"))

@app.route("/admin/flush", methods=["POST"])
def flush_database():
    try:
        confirmation = request.form.get("confirm_flush")
        if confirmation != "CONFIRM":
            flash("Flush aborted. Confirmation missing or incorrect.", "danger")
            return redirect(url_for("admin_panel"))

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM flights"))
            conn.execute(text("DELETE FROM aircraft"))
            conn.execute(text("DELETE FROM airlines"))
        flash("Database flushed successfully.", "success")
        logging.info("✅ Database flushed (all user data deleted).")

    except Exception as e:
        logging.error(f"❌ Flush error: {e}")
        flash("Failed to flush database.", "danger")

    return redirect(url_for("admin_panel"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    try:
        stats = get_airtrack_stats()
    except Exception as e:
        logging.error(f"❌ Error loading admin stats: {e}")
        stats = {}

    # 👇 Add backup file list
    from datetime import datetime
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    try:
        files = [
            {
                "name": f,
                "modified": datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, f))).strftime("%Y-%m-%d %H:%M:%S")
            }
            for f in os.listdir(backup_dir) if f.endswith(".sql")
        ]
        backup_files = sorted(files, key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        logging.error(f"❌ Error listing backup files: {e}")
        backup_files = []

    return render_template("admin.html", stats=stats, backup_files=backup_files)

# End of Admin Functions #

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", time=time.time()), 404

# Flask Configurations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevents aggressive caching

@app.route('/test_direct')
def test_direct():
    return "✅ Direct route from app.py is working"

if __name__ == "__main__":
    # Flask Configurations
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevents aggressive caching

    # ✅ Print route map after app is fully initialized
    with app.app_context():
        print("\n--- Flask URL Map ---")
        print(app.url_map)
        print("----------------------\n")

    # ✅ Start Flask app
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=False)