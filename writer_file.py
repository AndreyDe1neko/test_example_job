import csv
from datetime import datetime
from db import Sessionlocal
from models import *

db = Sessionlocal()


# def write_credits():
# db.query(Credits).delete()
with open('csv_data/credits.csv', encoding='utf-8') as credits_csv:
    db.query(Credits).delete()
    csv_read = csv.reader(credits_csv, delimiter='\t')
    next(csv_read)
    for row in csv_read:
        issuance_date = None
        return_date = None
        actual_return_date = None
        if row[2]:
            issuance_date = datetime.strptime(row[2], "%d.%m.%Y").date()
        if row[3]:
            return_date = datetime.strptime(row[3], "%d.%m.%Y").date()
        if row[4]:
            actual_return_date = datetime.strptime(row[4], "%d.%m.%Y").date()
        new_credit = Credits(
            id=int(row[0]),
            user_id=int(row[1]),
            issuance_date=issuance_date,
            return_date=return_date,
            actual_return_date=actual_return_date,
            body=int(row[5]),
            percent=float(row[6])
        )
        db.add(new_credit)
    db.commit()
    db.close()


# def write_dictionary():
# db.query(Dictionary).delete()
with open('csv_data/dictionary.csv', encoding='utf-8') as dictionary_csv:
    db.query(Dictionary).delete()
    csv_read = csv.reader(dictionary_csv, delimiter='\t')
    next(csv_read)
    for row in csv_read:
        new_dict_elem = Dictionary(
            id=int(row[0]),
            name=row[1]
        )
        db.add(new_dict_elem)
    db.commit()
    db.close()


# def write_payments():
# db.query(Payments).delete()
with open('csv_data/payments.csv', encoding='utf-8') as payments_csv:
    csv_read = csv.reader(payments_csv, delimiter='\t')
    next(csv_read)
    for row in csv_read:
        payment_date = None
        if row[2]:
            payment_date = datetime.strptime(row[2], "%d.%m.%Y").date()
        new_payment_elem = Payments(
            id=int(row[0]),
            credit_id=int(row[1]),
            payment_date=payment_date,
            type_id=row[3],
            sum=row[4]
        )
        db.add(new_payment_elem)
    db.commit()
    db.close()


# def write_users():
# db.query(Users).delete()
with open('csv_data/users.csv', encoding='utf-8') as users_csv:
    csv_read = csv.reader(users_csv, delimiter='\t')
    next(csv_read)
    for row in csv_read:
        print(row)
        registration_date = None
        if row[2]:
            registration_date = datetime.strptime(row[2], "%d.%m.%Y").date()
        new_payment_elem = Users(
            id=int(row[0]),
            login=str(row[1]),
            registration_date=registration_date
        )
        db.add(new_payment_elem)
    db.commit()
    db.close()