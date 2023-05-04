import logging

from peewee import fn
from pytz import timezone

from generated import countday_pb2, countday_pb2_grpc
from scraper.models import Events, Lessons, Trackings

tz = timezone("Europe/Zurich")

# Gets the latest tracking time for a lesson
LATEST_TRACKING = Trackings.select(
    Trackings.lesson, fn.MAX(Trackings.track_date).alias("max_date")
).group_by(Trackings.lesson)


class WeeklyServicer(countday_pb2_grpc.WeeklyServicer):
    def Weekly(self, request, context):
        logging.info("Request for Weekly")

        # Gets the min places_free per lesson
        subquery = (
            Lessons.select(
                Lessons.id.alias("lesson_id"),
                fn.MIN(Trackings.places_free).alias("min_places"),
            )
            .join(Trackings)
            .group_by(Lessons)
        )

        # Gets the average (min) free spaces per hour
        query = (
            Events.select(
                Lessons,
                fn.AVG(subquery.c.min_places).alias("avg_free"),
                fn.AVG(Lessons.places_max).alias("avg_max"),
            )
            .join(Lessons)
            .join(subquery, on=(subquery.c.lesson_id == Lessons.id))
            .where(
                Events.id == request.eventId,
                Lessons.from_date >= request.dateFrom,
                Lessons.from_date <= request.dateTo,
            )
            .group_by(
                Lessons.id,
                fn.to_char(Lessons.from_date, "Day"),
                fn.to_char(Lessons.from_date, "HH24:MI")
            )
        )

        data = {}
        details = {}  # more details when its clicked on
        weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for wd in weekdays:
            data[wd] = {}
            details[wd] = []
            for rt in range(24):
                data[wd][rt] = []

        for x in query:
            h = x.lessons.from_date.astimezone(tz).hour
            wd = weekdays[x.lessons.from_date.weekday()]
            data[wd][h].append(
                countday_pb2.WeeklyDetails(
                    timeFrom=x.lessons.from_date.astimezone(
                        tz).strftime("%H:%M"),
                    timeTo=x.lessons.to_date.astimezone(tz).strftime("%H:%M"),
                    avgFree=x.avg_free,
                    avgMax=x.avg_max,
                )
            )

        # an hour can have multiple details
        # if there's nothing in an hour, simply give out an list
        weekdays = {}
        for day, _ in data.items():
            weekdays[day] = [
                countday_pb2.WeeklyHour(hour=h, details=data[day][h]) for h in range(24)
            ]

        return countday_pb2.WeeklyReply(
            monday=weekdays["monday"],
            tuesday=weekdays["tuesday"],
            wednesday=weekdays["wednesday"],
            thursday=weekdays["thursday"],
            friday=weekdays["friday"],
            saturday=weekdays["saturday"],
            sunday=weekdays["sunday"],
        )
