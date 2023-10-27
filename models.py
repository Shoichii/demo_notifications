from peewee import *

db = SqliteDatabase('demo.db')

class Person(Model):
    name = CharField(null=True)
    telegram_id = BigIntegerField()
    birthday = CharField(null=True)
    phone = CharField(null=True)
    role = CharField()
    accept = BooleanField(null=True)

    class Meta:
        database = db

Person.create_table()