from extensions import db
from sqlalchemy import text
import pytz

def get_current_timezone():
    try:
        result = db.session.execute(
            text("SELECT SettingValue FROM app_settings WHERE SettingKey = 'Timezone' LIMIT 1")
        ).scalar()
        if result and result in pytz.all_timezones:
            return pytz.timezone(result)
    except Exception as e:
        print(f"⚠️ Failed to fetch timezone from DB: {e}")

    return pytz.timezone("UTC")  # Final fallback

def convert_to_local(dt):
    tz = get_current_timezone()
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.utc).astimezone(tz)
    return dt.astimezone(tz)
