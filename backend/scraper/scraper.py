import json
import requests
from datetime import datetime
import dateutil.parser
from pytz import timezone
import time
from models import Events, Lessons, Trackings, create_all_tables
import os


tz = timezone("Europe/Zurich")


def fetch(limit, offset=0):
    return json.loads(requests.get(f"https://asvz.ch/asvz_api/event_search?_format=json&limit={limit}&offset={offset}").text)


def scrape(FETCH, hours_to_scrape=24):
    """
    Fetches the next few hours with all activities
    Args:
        FETCH: If the script should fetch. Else it will simply take the local entries.json file.
        hours_to_scrape (int): Amount of hours into the future to scrape.
    """
    if FETCH:
        entries = []
        dt = datetime.now().astimezone(tz)
        all_scraped = 0
        i = 0
        while not all_scraped:
            js: dict = fetch(360, i * 360)
            for e in js["results"]:
                if e["cancelled"]:
                    continue
                from_date = dateutil.parser.isoparse(
                    e['from_date']).astimezone(tz)
                if (from_date - dt).total_seconds() / 3600 >= hours_to_scrape:
                    all_scraped = True
                    break
                try:
                    t = {
                        "nid": e["nid"],
                        "sport": e["sport_name"],
                        "title": e["title"],
                        "location": e["location"],
                        "places_free": e.get("places_free", 0),
                        "places_max": e.get("places_max", 0),
                        "places_taken": e.get("places_taken", e.get("places_max", 0)),
                        "from_date": e['from_date'],
                        "to_date": e['to_date'],
                        "niveau_name": e["niveau_name"],
                        "cancelled": e["cancelled"],
                        "livestream": e["livestream"],
                    }
                except KeyError:
                    print(f"Wasn't able to parse {e}")
                entries.append(t)
            i += 1
            print(f"Fetching iteration: {i}")

        print(f"Entries: {len(entries)}")

        with open("data/entries.json", "w") as f:
            json.dump(entries, f, indent=4)

        # updates the sports.json file with all the current sport types
        sports = {}
        for fa in js["facets"]:
            if fa["id"] != "sport":
                continue
            for s in fa["terms"]:
                sports[s["tid"]] = s["label"]
        with open("sports.json", "w") as f:
            json.dump(sports, f, indent=4)
    else:
        with open("data/entries.json", "r") as f:
            entries: list = json.load(f)

    # converts datetime to datetime objects for ease of use
    for e in entries:
        e["from_date"] = dateutil.parser.isoparse(
            e['from_date']).astimezone(tz)
        e["to_date"] = dateutil.parser.isoparse(
            e['to_date']).astimezone(tz)

    return entries


def add_to_db(entries: list):
    current_time = int(time.time())
    add_events = []
    add_lessons = []
    update_lessons = []
    add_trackings = []
    ids = []
    for e in entries:
        # create new activity
        event, created_event = Events.get_or_create(
            sport=e["sport"],
            title=e["title"],
            location=e["location"],
            niveau = e["niveau_name"],
        )
        if created_event:
            add_events.append(event)
        
        # Case 1: Same event ID, but from/toDate/places_max might've been modified
        lesson = Lessons.get_or_none(nid=e["nid"])

        # Case 2: event ID not stored yet. Either ID was changed or new lesson, but event & time overlap (so same event)
        if not lesson:
            lesson, created_lesson = Lessons.get_or_create(
                event=event,
                from_date=int(e["from_date"].timestamp()),
                to_date=int(e["to_date"].timestamp()),
                defaults={"nid": e["nid"], "places_max":0, "cancelled": False, "livestream": False, "from_date": 0, "to_date": 0},
            )
            if created_lesson:
                add_lessons.append(lesson)
        else:
            lesson.from_date = int(e["from_date"].timestamp())
            lesson.to_date = int(e["to_date"].timestamp())
        
        # always update lessons to make sure values are up to date (they might change)
        lesson.places_max = e["places_max"]
        lesson.cancelled = e["cancelled"]
        lesson.livestream = e["livestream"]
        update_lessons.append(lesson)
        
        # check free/taken spots
        tracking = Trackings.create(lesson=lesson, track_date=current_time, places_free=e["places_free"], places_taken=e["places_taken"])
        add_trackings.append(tracking)
    
    # save the values
    Events.bulk_create(add_events)
    Lessons.bulk_create(add_lessons)
    Lessons.bulk_update(update_lessons, fields=[Lessons.from_date, Lessons.to_date, Lessons.places_max, Lessons.cancelled, Lessons.livestream])
    Trackings.bulk_create(add_trackings)
    
    print(
        f"Successfully inserted/updated {len(entries)} entries into the db")
    

if __name__ == "__main__":
    if not os.path.exists("data/entries.db"):
        create_all_tables()
    entries = scrape(True, 24)  # scrape x hours in advance
    add_to_db(entries)
