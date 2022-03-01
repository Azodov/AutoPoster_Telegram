from peewee import *
from datetime import datetime
from pytz import timezone


def datetime_now():
    """Return normalized datetime with Moscow timezone"""

    date = datetime.now(timezone("Europe/Moscow"))
    return date.replace(tzinfo=None)


db = SqliteDatabase("base.db")


class Post(Model):
    id = PrimaryKeyField(unique=True)
    created = DateTimeField(default=datetime_now)

    chat_id = IntegerField(unique=True)
    text = TextField()
    last_timer = DateTimeField(default=datetime_now)  # from 0
    timer = IntegerField(default=3600)
    image = CharField(null=True)
    video = CharField(null=True)

    class Meta:
        database = db
        order_by = "id"
        db_table = "posts"


db.create_tables([Post])
