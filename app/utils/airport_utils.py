# utils/airport_utils.py

from extensions import db
from sqlalchemy import text
from functools import lru_cache
from utils.logger import logger  # make sure this exists in your project

@lru_cache(maxsize=100)
def format_airport_display(icao_code):
    if not icao_code:
        logger.debug("Empty ICAO code provided to airport display filter")
        return "Unknown Airport"
    
    try:
        with db.engine.connect() as conn:
            airport = conn.execute(text("""
                SELECT AirportName, municipality, iso_country, iso_region
                FROM airports 
                WHERE ICAO = :icao
            """), {"icao": icao_code}).fetchone()
            
            if airport:
                name = airport.AirportName or "Unnamed Airport"
                
                # Clean up municipality - extract just the part in parentheses
                city = airport.municipality or "Unknown City"
                if "(" in city and ")" in city:
                    city = city.split("(")[1].split(")")[0]
                
                country = airport.iso_country or "Unknown Country"
                
                # Extract state from iso_region (AU-NSW -> NSW)
                state = ""
                if airport.iso_region and '-' in airport.iso_region:
                    state = airport.iso_region.split('-')[1]
                
                result = f"{name}, {city}, {state}, {country}"
                logger.debug(f"Found airport data for {icao_code}: {result}")
                return result
            else:
                logger.warning(f"Airport not found in database: {icao_code}")
                return f"{icao_code} Airport"
    except Exception as e:
        logger.error(f"Database error looking up airport {icao_code}: {str(e)}")
        return f"{icao_code} (Unavailable)"
