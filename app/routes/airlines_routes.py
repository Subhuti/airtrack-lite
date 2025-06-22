from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import text
from extensions import db

airlines_bp = Blueprint('airlines', __name__, url_prefix='/airlines')

@airlines_bp.route('/')
def airlines_table():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = 25
        offset = (page - 1) * per_page

        # Count total records
        total_result = db.session.execute(text("SELECT COUNT(*) FROM airlines")).fetchone()
        total_records = total_result[0] if total_result else 0
        total_pages = (total_records + per_page - 1) // per_page

        # Fetch airlines
        result = db.session.execute(
            text("SELECT * FROM airlines ORDER BY AirlineName ASC LIMIT :limit OFFSET :offset"),
            {"limit": per_page, "offset": offset}
        )
        airlines = [dict(row._mapping) for row in result.fetchall()]

        return render_template(
            'airlines_table.html',
            airlines=airlines,
            current_page=page,
            total_pages=total_pages,
            filter_type=None,
            selected_airline_id=None,
            selected_registration=""
        )

    except Exception as e:
        print(f"❌ Error fetching airlines: {e}")
        flash("An error occurred loading airlines.")
        return render_template(
            'airlines_table.html',
            airlines=[],
            current_page=1,
            total_pages=1,
            filter_type=None,
            selected_airline_id=None,
            selected_registration=""
        )

@airlines_bp.route('/add', methods=['GET', 'POST'], endpoint='add_airline')
def add_airline():
    if request.method == 'POST':
        airline_name = request.form.get('AirlineName', '').strip()

        if not airline_name:
            flash("Airline name is required.", "danger")
            return redirect(url_for('airlines.add_airline'))

        try:
            db.session.execute(
                text("INSERT INTO airlines (AirlineName) VALUES (:name)"),
                {"name": airline_name}
            )
            db.session.commit()
            flash("Airline added successfully!", "success")
            return redirect(url_for('airlines.airlines_table'))

        except Exception as e:
            print(f"❌ Error adding airline: {e}")
            flash("Failed to add airline.", "danger")
            return redirect(url_for('airlines.add_airline'))

    return render_template('add_airline.html')
