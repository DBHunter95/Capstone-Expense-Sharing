import os, sys
from flask import Flask
from sqlalchemy import Column, String, Integer, Float
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json

db = SQLAlchemy()

def setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://xcjngabiwfokhv:c87d6974f39d3b174c73ddafb29eff6535fa71179a4d805229e5546378b89c5a@ec2-34-202-88-122.compute-1.amazonaws.com:5432/dc9t6gpgtl9pc6"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    #db_drop_and_create_all()

def db_drop_and_create_all():
    db.drop_all()
    db.create_all()

members = db.Table('members',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('user_id', db.Integer,db.ForeignKey('users.id'), primary_key=True)
    )    

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    total_owed = db.Column(db.Float)
    # Outstanding is used as a python dictionary but stored as a JSON object
    outstanding = db.Column(db.String(500))
    transactions = db.relationship('Transaction', backref='user_transaction', lazy=True)
    # Relationship with Group class to show which groups the users are in
    faction = db.relationship('Group', secondary=members, lazy='subquery',
                              backref=db.backref('people', lazy=True))

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
            'total_owed': self.total_owed,
            'outstanding': json.loads(self.outstanding)
        }

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def insert(self):
        db.session.add(self)
        db.session.commit()

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    transactions = db.relationship('Transaction', backref='group_transaction', lazy=True)

    def format(self):
        members = []
        # Get's list of users in the group from the relationship with the User class
        for user in self.people:
            members.append({
                "id": user.id,
                "name":user.name
            })
        return {
            'id': self.id,
            'name': self.name,
            'members' : members
        }

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def insert(self):
        db.session.add(self)
        db.session.commit()

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120))
    date = db.Column(db.String, nullable=True)
    price = db.Column(db.Float)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrower_id = db.Column(db.Integer)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)

    def format(self):
        buyer = User.query.filter_by(id=self.buyer_id).one()
        borrower = User.query.filter_by(id=self.borrower_id).one_or_none()
        group = Group.query.filter_by(id=self.group_id).one_or_none()
        buyer_name = buyer.name
        group_name = ''
        borrower_name = ''

        #This updates the price displayed if it is a payment
        price = 0

        if self.item == "Payment":
            price = (self.price/2)
        else:
            price = self.price

        if borrower is None and group is None:
            group_name = 'deleted'
        
        elif borrower is None:
            group_name = group.name
        else:
            borrower_name = borrower.name
               
        return {
            'id': self.id,
            'date': self.date,
            'price': price,
            'buyer_id': self.buyer_id,
            'borrower id': self.borrower_id,
            'buyer_name': buyer_name,
            'borrower_name': borrower_name,
            'group_id': self.group_id,
            'group_name': group_name,
            'item': self.item
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    
