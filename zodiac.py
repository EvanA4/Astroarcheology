from datetime import datetime, timezone
from astropy.coordinates import get_constellation, get_sun
from astropy.time import Time


def sun_constellation(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    sun = get_sun(Time(dt))
    return get_constellation(sun)


if __name__ == "__main__":
    dt = datetime.now()
    zodiac = sun_constellation(dt)
    print(zodiac)