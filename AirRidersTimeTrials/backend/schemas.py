import re
from marshmallow import Schema, fields, validates, ValidationError, EXCLUDE
from models import Country
from extensions import db

TIME_RE = re.compile(r"^\d+'\d{2}\"?\d{3}$")  # ex: 1'05"780 or 1'05"780 (quote optional)

def parse_time_to_ms(time_str: str) -> int:
    """
    Converts "M'SS\"mmm" -> total milliseconds.
    Example: 1'05"780 => 65780ms
    """
    # normalize: ensure contains a double quote for split convenience
    s = time_str.replace("”", "\"").replace("“", "\"").replace("'", "'")
    # extract minutes, seconds, millis
    # pattern: M'SS"mmm  OR  M'SSmmm (quote optional)
    m_part, rest = s.split("'")
    minutes = int(m_part)

    if '"' in rest:
        sec_part, ms_part = rest.split('"')
    else:
        sec_part, ms_part = rest[:2], rest[2:]

    seconds = int(sec_part)
    millis = int(ms_part)

    return (minutes * 60 * 1000) + (seconds * 1000) + millis

class RegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    country_code = fields.Str(required=False, allow_none=True)

#i think that **kwargs should help as any additional info from marshmellow, interups data flow
    @validates("username")
    def validate_username(self, value, **kwargs):
        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if len(value) > 50:
            raise ValidationError("Username too long.")

# did **kwargs to validate password
    @validates("password")
    def validate_password(self, value, **kwargs):
        if len(value) < 6:
            raise ValidationError("Password must be at least 6 characters.")


class UpdateUserSchema(Schema):
    class Meta:
        unknown = EXCLUDE #ignores any additional data
    
    #only validate the change in country
    country_code = fields.Str(required=False, allow_none=True)
    

#did **kwargs to def valid country code
    @validates("country_code")
    def validate_country_code(self, value, **kwargs):
        if value is None or value == "":
            return
        
        #checks for lowercase
        if db.session.get(Country, value.lower()):
            return
        
        #checks for uppercase
        if db.session.get(Country, value.upper()):
            return

        raise ValidationError("Invalid country code: {value}")

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    

class RecordCreateSchema(Schema):
    course_key = fields.Str(required=True)
    machine_name = fields.Str(required=True)
    character_name = fields.Str(required=True)
    time = fields.Str(required=True)
    lap1 = fields.Float(required=False, allow_none=True)
    lap2 = fields.Float(required=False, allow_none=True)
    lap3 = fields.Float(required=False, allow_none=True)

#did the same here with time, using **kwargs
    @validates("time")
    def validate_time(self, value, **kwargs):
        if not TIME_RE.match(value):
            raise ValidationError("Time must look like: 1'05\"780")
        # also ensure parse works
        try:
            _ = parse_time_to_ms(value)
        except Exception:
            raise ValidationError("Invalid time format.")
