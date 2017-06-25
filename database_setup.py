# import os
# import sys
from sqlalchemy import (Column, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    password = Column(String(30), nullable=False)
    picture = Column(String(250), nullable=False)

    @property
    def serialize(self):
        # return object data in easily serializeable format
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'picture': self.picture
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    UniqueConstraint(name)

    @property
    def serialize(self):
        # return object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
        }


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    price = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey('user.id'))
    owner = relationship(User)
    UniqueConstraint(name)

    @property
    def serialize(self):
        # return object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_name': self.category.name,
            'owner_name': self.owner.username
        }


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
