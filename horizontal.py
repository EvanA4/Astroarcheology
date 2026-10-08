import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_body


def get_horizontal(name: str, t: Time, lat: float, long: float):
    '''
    ## get_horizontal
    Returns the horizontal coordinates of a celestial object as an
    array of [altitude, azimuth, and distance]. All angles should be
    in radians, and all distances should be in AU.

    ### Parameters:
    | Field | Description |
    | - | - |
    | `name` | The name of the celestial object (e.g., 'mars') |
    | `t` | The Time object for the observation |
    | `lat` | The latitude of the observer on Earth |
    | `long` | The longitude of the observer on Earth |
    '''

    site = EarthLocation(lat=lat * u.rad, lon=long * u.rad)
    planet = get_body(name, t, location=site)
    altaz = planet.transform_to(
        AltAz(obstime=t, location=site, pressure=0 * u.hPa)
    )
    return [
        float(altaz.alt.to_value(u.rad)),
        float(altaz.az.to_value(u.rad)),
        float(altaz.distance.to_value(u.au)),
    ]


if __name__ == "__main__":
    t = Time.now()
    horizontal = get_horizontal('Sun', t, 1.43, 3.2)
    print(horizontal)