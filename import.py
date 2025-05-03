import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"), encoding="utf8")
db = scoped_session(sessionmaker(bind=engine))


def main():

    f = open("room_details.csv")
    reader = csv.reader(f)

    for roomtype, guestcapacity, price in reader:
        db.execute("INSERT INTO room_details (roomtype, guestcapacity, price) VALUES (:roomtype, :guestcapacity, :price)", {"roomtype" : roomtype, "guestcapacity" : guestcapacity, "price" : price})
    db.commit()


main()