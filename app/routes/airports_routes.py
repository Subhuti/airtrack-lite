from flask import Blueprint, request, jsonify, render_template
from sqlalchemy import text
from extensions import db
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)
airports_bp = Blueprint('airports', __name__, url_prefix='/airports')

@airports_bp.route('/logged')
def logged_airports():
    result = db.session.execute(text("""
        SELECT DISTINCT ICAO
        FROM (
            SELECT Departure AS ICAO FROM aircraft
            UNION
            SELECT Arrival AS ICAO FROM aircraft
        ) AS all_icaos
        WHERE ICAO IS NOT NULL
        ORDER BY ICAO
    """)).fetchall()

    icaos = [row[0] for row in result]

    airports = []
    for icao in icaos:
        row = db.session.execute(text("""
            SELECT ICAO, AirportName 
            FROM airports 
            WHERE ICAO = :icao
        """), {"icao": icao}).fetchone()
        if row:
            airports.append(dict(row._mapping))

    return render_template("logged_airports.html", airports=airports)

@airports_bp.route('/search')
def search_airports():
    query = request.args.get('q', '').strip().upper()
    if not query:
        return jsonify([])

    try:
        results = db.session.execute(text("""
            SELECT ICAO, IATA, AirportName, municipality, iso_country, iso_region, type
            FROM airports 
            WHERE (ICAO LIKE :query_pattern 
                   OR IATA LIKE :query_pattern 
                   OR AirportName LIKE :query_pattern
                   OR municipality LIKE :query_pattern)
            AND ICAO IS NOT NULL
            ORDER BY 
                CASE WHEN ICAO = :exact THEN 1
                     WHEN ICAO LIKE :query_pattern THEN 2 
                     WHEN IATA LIKE :query_pattern THEN 3
                     ELSE 4 END,
                AirportName
            LIMIT 10
        """), {
            "exact": query,
            "query_pattern": f"{query}%"
        }).fetchall()

        airports = []
        for row in results:
            airport = dict(row._mapping)
            city = airport['municipality'] or "Unknown City"
            if "(" in city and ")" in city:
                city = city.split("(")[1].split(")")[0]

            state = ""
            if airport['iso_region'] and '-' in airport['iso_region']:
                state = airport['iso_region'].split('-')[1]

            airport['display_name'] = f"{airport['AirportName']}, {city}, {state}, {airport['iso_country']}"
            airport['code_display'] = f"{airport['ICAO']}" + (f" ({airport['IATA']})" if airport['IATA'] else "")
            airports.append(airport)

        return jsonify(airports)

    except Exception as e:
        logger.error(f"Airport search error: {str(e)}")
        return jsonify([]), 500

@airports_bp.route('/search_icao_only')
def search_icao_only():
    query = request.args.get('q', '').strip().upper()
    if not query:
        return jsonify([])

    try:
        results = db.session.execute(text("""
            SELECT ICAO, CONCAT(AirportName, ' (', ICAO, ')') AS display_name
            FROM airports
            WHERE ICAO LIKE :query
            ORDER BY ICAO
            LIMIT 10
        """), {"query": f"{query}%"})

        return jsonify([{
            "ICAO": row.ICAO,
            "display_name": row.display_name
        } for row in results])

    except Exception as e:
        logger.error(f"ICAO-only airport search error: {str(e)}")
        return jsonify([]), 500

@airports_bp.route('/info/<icao>', endpoint='airport_info')
def airport_info(icao):
    try:
        airport = db.session.execute(
            text("SELECT * FROM airports WHERE ICAO = :icao"),
            {"icao": icao}
        ).fetchone()
        
        if not airport:
            return f"Airport {icao} not found in database.", 404

        aircraft_count = db.session.execute(
            text("SELECT COUNT(*) FROM aircraft WHERE Departure = :icao OR Arrival = :icao"),
            {"icao": icao}
        ).scalar()

        return render_template('airport_info.html', 
            airport=dict(airport._mapping),
            aircraft_count=aircraft_count)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"⚠️ Exception: {str(e)}", 500

@lru_cache(maxsize=100)
def format_airport_display(icao_code):
    if not icao_code:
        return "Unknown Airport"

    try:
        row = db.session.execute(text("""
            SELECT AirportName, municipality, iso_country, iso_region
            FROM airports WHERE ICAO = :icao
        """), {"icao": icao_code}).fetchone()

        if row:
            airport = dict(row._mapping)
            name = airport.get("AirportName", "Unnamed Airport")
            city = airport.get("municipality") or "Unknown City"
            if "(" in city and ")" in city:
                city = city.split("(")[1].split(")")[0]

            country = airport.get("iso_country") or "Unknown Country"
            state = ""
            if airport.get("iso_region") and '-' in airport["iso_region"]:
                state = airport["iso_region"].split('-')[1]

            return f"{name}, {city}, {state}, {country}"
        else:
            return f"{icao_code} Airport"

    except Exception as e:
        return f"{icao_code} (Unavailable)"

def register_filters(app):
    app.jinja_env.filters['airport_display'] = format_airport_display

def setup_logging():
    import os
    from logging.handlers import RotatingFileHandler
    if not os.path.exists('logs'):
        os.mkdir('logs')
    handler = RotatingFileHandler('logs/airport_lookups.log', maxBytes=10240, backupCount=10)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.INFO)
    airport_logger = logging.getLogger(__name__)
    airport_logger.setLevel(logging.INFO)
    airport_logger.addHandler(handler)
    return airport_logger

logger = setup_logging()
