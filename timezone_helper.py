from datetime import datetime
import pytz

# Timezone configuration
IST = pytz.timezone('Asia/Kolkata')

def to_timezone_aware(dt, tzinfo):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt.astimezone(tzinfo)