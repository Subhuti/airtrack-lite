# /app/models/aircraft.py

from extensions import db

class Aircraft(db.Model):
    __tablename__ = 'aircraft'

    AircraftID = db.Column(db.Integer, primary_key=True)
    Registration = db.Column(db.String(20), nullable=False, unique=True)
    AirlineID = db.Column(db.Integer, db.ForeignKey('airlines.AirlineID'), nullable=True)
    Aircraft_Type = db.Column(db.String(100), nullable=True)
    Country_of_Reg = db.Column(db.String(100), nullable=True)
    Departure = db.Column(db.String(10), nullable=True)
    Arrival = db.Column(db.String(10), nullable=True)
    Spotted_At = db.Column(db.String(100), nullable=True)
    Aircraft_Updated = db.Column(db.DateTime, nullable=True)
    First_Sighted = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Aircraft {self.Registration}>"
