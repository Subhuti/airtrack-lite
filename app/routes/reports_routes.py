from flask import Blueprint, render_template, url_for, flash
from sqlalchemy import text
from extensions import db
import logging

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

def render_report(title, columns, data):
    return render_template('partials/_report_table.html', title=title, columns=columns, data=data)

def safe_query(sql, params=None, title="", columns=[]):
    try:
        result = db.session.execute(text(sql), params or {})
        rows = [dict(row._mapping) for row in result.fetchall()]
        return render_report(title, columns, rows)
    except Exception as e:
        logging.error(f"❌ Error in report '{title}': {e}")
        flash(f"Failed to load {title}.", "danger")
        return render_report(title, [], [])

@reports_bp.route("/logged_airports")
def report_logged_airports():
    try:
        conn = db.engine.connect()
        query = text("""
            SELECT DISTINCT a.ICAO, a.AirportName, a.Country
            FROM airports a
            JOIN (
                SELECT DISTINCT Departure AS ICAO FROM aircraft
                UNION
                SELECT DISTINCT Arrival AS ICAO FROM aircraft
            ) x ON a.ICAO = x.ICAO
            ORDER BY a.Country, a.AirportName
        """)
        result = conn.execute(query)
        columns = result.keys()

        airports = []
        for row in result:
            row_dict = dict(zip(columns, row))
            icao = row_dict["ICAO"]
            row_dict["ICAO"] = (
                f'<a href="{url_for("airports.airport_info", icao=icao)}" '
                f'class="icao-key">{icao}</a>'
            )
            airports.append(row_dict)

        conn.close()
        return render_template(
            "partials/_report_table.html",
            title="Logged Airports",
            data=airports,
            columns=["ICAO", "AirportName", "Country"]
        )

    except Exception as e:
        logging.error(f"❌ Error generating Logged Airports report: {e}")
        return render_report("Logged Airports", [], [])

@reports_bp.route('/top_airlines')
def top_airlines():
    return safe_query("""
        SELECT a.AirlineName, COUNT(*) AS Aircraft_Count
        FROM aircraft ac
        LEFT JOIN airlines a ON ac.AirlineID = a.AirlineID
        WHERE a.AirlineName IS NOT NULL
        GROUP BY a.AirlineName
        ORDER BY Aircraft_Count DESC
        LIMIT 20
    """, title="Top Airlines", columns=["AirlineName", "Aircraft_Count"])

@reports_bp.route('/top_countries')
def top_countries():
    return safe_query("""
        SELECT Country_of_Reg, COUNT(*) AS Count
        FROM aircraft
        WHERE Country_of_Reg IS NOT NULL AND Country_of_Reg != ''
        GROUP BY Country_of_Reg
        ORDER BY Count DESC
        LIMIT 20
    """, title="Top Countries of Registration", columns=["Country_of_Reg", "Count"])
