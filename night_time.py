import sys
import json
import datetime
import copy
from skyfield import api
from skyfield import almanac
import nvector


ui_fmt = "%Y-%m-%d %H:%M"


def main():
    # arg format
    # XXXXTTTTYYYYTTTT[YYYYMMDD]
    input_string = sys.argv[1]
    departure_str = input_string[:4]
    departure_time = input_string[4:8]
    arrival_str = input_string[8:12]
    arrival_time = input_string[12:16]

    if(len(input_string) > 16):
        flight_date = datetime.datetime.strptime(
            input_string[16:], '%Y%m%d').replace(tzinfo=datetime.timezone.utc)
    else:
        flight_date = datetime.datetime.utcnow().date()

    airports = json.load(open('airports.json'))
    departure = copy.copy(airports[departure_str])
    arrival = copy.copy(airports[arrival_str])

    # calculate distance
    L = calculate_distance(
        departure["lat"],
        departure["lon"],
        arrival["lat"],
        arrival["lon"]
    )

    # calculate flight time
    departure["time"] = datetime.datetime.strptime(
        f"{flight_date.strftime('%Y%m%d')}{departure_time}",
        '%Y%m%d%H%M').replace(tzinfo=datetime.timezone.utc)

    arrival["time"] = datetime.datetime.strptime(
        f"{flight_date.strftime('%Y%m%d')}{arrival_time}",
        '%Y%m%d%H%M').replace(tzinfo=datetime.timezone.utc)

    flight_time = arrival["time"] - departure["time"]
    if flight_time.days < 0:
        flight_time += datetime.timedelta(days=1)
        arrival["time"] += datetime.timedelta(days=1)

    print(f"Departure: {departure_str} Time: {departure['time'].strftime(ui_fmt)} IATA: {departure['iata']} City: {departure['city']}")
    print(f"Arrival:   {arrival_str} Time: {arrival['time'].strftime(ui_fmt)} IATA: {arrival['iata']} City: {arrival['city']}")
    print(f"Distance:  {int(L)}nm Flight time: {flight_time}")

    # average airplane speed based on block time, kt
    Vplane = L / (flight_time.seconds / 3600)

    # get some sun parameters
    (departure["sunrise"], departure["sunset"]) = get_sun_data(departure["lat"], departure["lon"], departure["time"])
    (arrival["sunrise"], arrival["sunset"]) = get_sun_data(arrival["lat"], arrival["lon"], arrival["time"])

    print(f"Departure Sunrise: {departure['sunrise'].strftime(ui_fmt)} Sunset: {departure['sunset'].strftime(ui_fmt)}")
    print(f"Arrival   Sunrise: {arrival['sunrise'].strftime(ui_fmt)} Sunset: {arrival['sunset'].strftime(ui_fmt)}")

    if (departure["sunrise"] <= departure["time"] <= departure["sunset"]) and (arrival["sunrise"] <= arrival["time"] <= arrival["sunset"]):
        print("Full day flight")
        exit()
    elif (departure["sunrise"] <= departure["time"] <= departure["sunset"]):
        print("Flight from day to night, night landing")

        x_point = meet_with_sun(departure, arrival, Vplane, "sunset")
        nt = (arrival["time"] - x_point["time"]).seconds / 3600

    elif (arrival["sunrise"] <= arrival["time"] <= arrival["sunset"]):
        print("Flight from night to day, day landing")

        x_point = meet_with_sun(departure, arrival, Vplane, "sunrise")
        nt = (x_point["time"] - departure["time"]).seconds / 3600

    else:
        print("Full night time")
        nt = flight_time.seconds / 3600

    print(f"Night time: {convert_time(nt)}")


def meet_with_sun(departure, arrival, Vplane, target):
    max_iterations = 50
    max_diff_minutes = 0.5
    i = 0
    found_x = False

    start_point = copy.copy(departure)
    end_point = copy.copy(arrival)

    print(f"Departure lat/lon: {start_point['lat']:.2f} {start_point['lon']:.2f} | Arrival lat/lon: {end_point['lat']:.2f} {end_point['lon']:.2f}")
    print(f"lat\tlon\tdist\ttime on route\t\t{target}\t\t\tdiff (minutes)")
    while((i < max_iterations) and not found_x):
        i += 1

        x_point = {}
        x_point["lat"], x_point["lon"] = get_midpoint(start_point["lat"], start_point["lon"], end_point["lat"], end_point["lon"])

        (x_point["sunrise"], x_point["sunset"]) = get_sun_data(x_point["lat"], x_point["lon"], departure["time"])
        D = calculate_distance(departure["lat"], departure["lon"], x_point["lat"], x_point["lon"])
        x_point["time"] = departure["time"] + datetime.timedelta(hours=(D / Vplane))

        diff = (x_point["time"] - x_point[target])
        if diff.days < 0:
            diff += datetime.timedelta(days=1)
            diff_m = - 24 * 60 + diff.seconds / 60
        else:
            diff_m = diff.seconds / 60

        print(f"{x_point['lat']:.2f}\t{x_point['lon']:.2f}\t{D:.2f}\t{x_point['time'].strftime(ui_fmt)}\t{x_point[target].strftime(ui_fmt)}\t{diff_m:.2f}")

        if abs(diff_m) >= max_diff_minutes:
            if diff_m > 0:
                start_point = copy.copy(start_point)
                end_point = copy.copy(x_point)
            else:
                start_point = copy.copy(x_point)
                end_point = copy.copy(end_point)
        else:
            found_x = True

    return x_point


def get_midpoint(lat1, lon1, lat2, lon2):

    points = nvector.GeoPoint(latitude=[lat1, lat2], longitude=[lon1, lon2], degrees=True)
    nvectors = points.to_nvector()
    n_EM_E = nvectors.mean()
    g_EM_E = n_EM_E.to_geo_point()
    lat, lon = g_EM_E.latitude_deg, g_EM_E.longitude_deg

    return lat[0], lon[0]


def get_sun_data(lat, lon, flight_date):
    sky_fmt = "%Y-%m-%dT%H:%M:%SZ"

    ts = api.load.timescale()
    e = api.load('de421.bsp')

    sunrise = None
    sunset = None

    bluffton = api.Topos(lat, lon)
    # first get sunrise and sunset times
    t, y = almanac.find_discrete(ts.utc(flight_date.date()), ts.utc(flight_date.date() + datetime.timedelta(days=1)), almanac.sunrise_sunset(e, bluffton))
    for ti, yi in zip(t, y):
        if yi:
            sunrise = ti.utc_iso()
        else:
            sunset = ti.utc_iso()

    return (datetime.datetime.strptime(sunrise, sky_fmt).replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(minutes=30),
            datetime.datetime.strptime(sunset, sky_fmt).replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(minutes=30))


def calculate_distance(lat1, lon1, lat2, lon2):
    wgs84 = nvector.FrameE(name='WGS84')
    point1 = wgs84.GeoPoint(latitude=lat1, longitude=lon1, degrees=True)
    point2 = wgs84.GeoPoint(latitude=lat2, longitude=lon2, degrees=True)
    s_12, _azi1, _azi2 = point1.distance_and_azimuth(point2)

    return s_12 / 1000 / 1.852  # nm


def convert_time(nt):
    decimal_part = nt % 1
    minutes = int(decimal_part * 60)
    hours = int(nt)

    return f"{hours}h {minutes}m"


if __name__ == "__main__":
    main()
