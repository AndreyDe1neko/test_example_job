from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


class Users(Base):
    __tablename__='Users'


    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False, unique=True)
    registration_date = Column(Date, nullable=False)

    # def __str__(self):
    #     return self.login

    credits = relationship("Credits", back_populates="user")


class Credits(Base):
    __tablename__ = 'Credits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    issuance_date = Column(Date)
    return_date = Column(Date)
    actual_return_date = Column(Date)
    body = Column(Integer)
    percent = Column(Integer)

    user = relationship("Users", back_populates="credits")

    # def __str__(self):
    #     return self.body


class Dictionary(Base):
    __tablename__ = 'Dictionary'
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Plans(Base):
    __tablename__ = 'Plans'

    id = Column(Integer, primary_key=True)
    period = Column(Date)
    sum = Column(Integer)
    category_id = Column(Integer, ForeignKey("Dictionary.id"))


class Payments(Base):
    __tablename__ = 'Payments'

    id = Column(Integer, primary_key=True)
    sum = Column(Integer)
    payment_date = Column(Date)
    credit_id = Column(Integer, ForeignKey("Credits.id"))
    type_id = Column(Integer, ForeignKey("Dictionary.id"))


