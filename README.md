## Night time calculator

Flight night time calculator for pilots. It's a simplified way to calculate where/what time an airplane and sun can meet. It doesn't compensate sunset/sunrise times for airplane altitude.

This is a beta version, tested just on few flights.

The logic is simple. It finds a midpoint on the route, check the time when airplane will be there and compares it with sunset/sunrise at this point. If the difference is too big it takes front/rear part of the route and check the midpoint again and again...

## Known issues

It will not calculate the night time if your departured before sunset and arrived after sunrise - damn who ever fly these routes


## How to use

```bash
$ python ./night_time.py LKPR1720LKMT181020200401
Departure: LKPR Time: 2020-04-01 17:20 IATA: PRG City: Prague
Arrival:   LKMT Time: 2020-04-01 18:10 IATA: OSR City: Ostrava
Distance:  151nm Flight time: 0:50:00
Departure Sunrise: 2020-04-01 04:08 Sunset: 2020-04-01 18:05
Arrival   Sunrise: 2020-04-01 03:53 Sunset: 2020-04-01 17:49
Flight from day to night, night landing
Departure lat/lon: 50.10 14.26 | Arrival lat/lon: 49.70 18.11
 lat    lon    dist   time on route     flt time  sunset             diff (min)
 49.91  16.19   75.67 2020-04-01 17:45  0h 25m    2020-04-01 17:57   -12.60
 49.81  17.15  113.51 2020-04-01 17:57  0h 37m    2020-04-01 17:53     3.85
 49.86  16.67   94.59 2020-04-01 17:51  0h 31m    2020-04-01 17:55    -4.38
 49.84  16.91  104.05 2020-04-01 17:54  0h 34m    2020-04-01 17:54    -0.27
Night time: 0h 15m
```

Input parameter format is AAAABBBBCCCCDDDD[YYYYMMDD] where
- AAAA - ICAO departure airport
- BBBB - departure time in UTC
- CCCC - ICAO arrival airport
- DDDD - arrival time in UTC
- YYYYMMDD - flight date, optional if you calculate the night time for today's flight


## Airports database

There is a json file with ICAO airfield identificators with some additional data (like Lat and Lng). I have no idea how old is it, so might be some data is not fresh or missing

## Python libraries

- [skyfield](https://rhodesmill.org/skyfield/)
- [nvector](https://pypi.org/project/nvector/)