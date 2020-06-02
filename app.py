import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json

from models import setup_db, Transaction, User, Group, members
from auth import AuthError, requires_auth

# This is a function for updating user records when a group transaction is made.

def update_group_transaction(buyer_id, group_id, price):

  group = Group.query.filter_by(id = group_id).one()
  buyer = User.query.filter_by(id = buyer_id).one()
  buyer_records = json.loads(buyer.outstanding)
  amount = price/len(group.people)
  buyer.total_owed += price
  buyer.update()

  for user in group.people:

    borrower_records = json.loads(user.outstanding)
    buyer_key = "%d" % buyer.id

    if buyer_key in borrower_records:
      borrower_key = "%d" % user.id
      buyer_records[borrower_key] += amount
      borrower_records[buyer_key] -= amount
      buyer_records[buyer_key] = 0 

      buyer.outstanding = json.dumps(buyer_records)
      user.outstanding = json.dumps(borrower_records)
      user.total_owed -= amount
      buyer.update()
      user.update()
    
    else:
      borrower_key = "%d" % user.id
      buyer_records[borrower_key] = amount
      borrower_records[buyer_id] = -amount
      buyer_records[buyer_key] = 0

      buyer.outstanding = json.dumps(buyer_records)
      user.outstanding = json.dumps(borrower_records)
      user.total_owed -= amount
      buyer.update()
      user.update()

# This is a function for updating user records when a transaction is made between two individuals.

def update_individual_transaction(buyer_id, borrower_id, price):

  buyer = User.query.filter_by(id=buyer_id).one()
  borrower = User.query.filter_by(id=borrower_id).one()

  buyer_records = json.loads(buyer.outstanding)
  borrower_records = json.loads(borrower.outstanding)
  buyer_key = "%d" % buyer_id
  borrower_key = "%d" % borrower_id

  if borrower_key in buyer_records:
    buyer_records[borrower_key] += price
    borrower_records[buyer_key] -= price

  else:
    buyer_records[borrower_id] = price
    borrower_records[buyer_id] = -price

  buyer.outstanding = json.dumps(buyer_records)
  borrower.outstanding = json.dumps(borrower_records)
  borrower.total_owed -= price
  buyer.total_owed += price
  buyer.update()
  borrower.update()


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)


  @app.route('/users')
  @requires_auth('get:users')
  def get_users(payload):
    selection = User.query.all()
    users = [user.format() for user in selection]

    return jsonify({
      'success': True,
      'users': users
    })


  @app.route('/groups')
  @requires_auth('get:groups')
  def get_groups(payload):
    selection = Group.query.all()
    groups = [group.format() for group in selection]

    return jsonify({
      'success': True,
      'groups': groups
    })


  @app.route('/transactions')
  @requires_auth('get:transactions')
  def get_transactions(payload):
    selection = Transaction.query.all()
    transactions = [transaction.format() for transaction in selection]

    return jsonify({
      'success': True,
      'transactions': transactions
    })


  @app.route('/users', methods=['POST'])
  @requires_auth('post:users')
  def add_user(payload):
    body = request.get_json()
    name = body.get('name', None)
    
    try:
      new_user = User(name=name, outstanding=json.dumps({}))
      new_user.insert()
 
    except:
      abort(422)

    return jsonify({
        'success': True
    })


  @app.route('/groups', methods=['POST'])
  @requires_auth('post:groups')
  def add_group(payload):
    body = request.get_json()
    name = body.get('name', None)
    users = body.get('users', None)

    try:
      new_group = Group(name=name)
      new_group.insert()

    except:
      abort(422)

    for instance in users:
      user = User.query.filter_by(id=instance).one()
      new_group.people.append(user)
      new_group.update()

    return jsonify({
        'success': True
    })


  @app.route('/transactions/<id>', methods=['DELETE'])
  @requires_auth('delete:transaction')
  def delete_transaction(payload, id):

    transaction = Transaction.query.filter_by(id = id).one_or_none()

    if transaction is None:
        abort(404)

    buyer = User.query.filter_by(id = transaction.buyer_id).one()
    price = -transaction.price
    buyer_id = transaction.buyer_id
    group_id = transaction.group_id
    
    if transaction.borrower_id is None:
      group_id = transaction.group_id
      update_group_transaction(buyer_id, group_id, price)

    else:
      borrower_id = transaction.borrower_id
      price = (price/2)
      update_individual_transaction(buyer_id, borrower_id, price)

    transaction.delete()

    return jsonify({
        'success': True,
        'delete': id
    })
        

  @app.route('/transactions/<id>', methods=['PATCH'])
  @requires_auth('patch:transactions')
  def update_transaction(payload, id):
    transaction = Transaction.query.filter_by(id = id).one_or_none()
    body = request.get_json()
    new_price = body.get('price', None)

    if transaction is None:
        abort(404)

    buyer = User.query.filter_by(id = transaction.buyer_id).one()
    buyer_id = transaction.buyer_id
    price = new_price - transaction.price
    
    if transaction.borrower_id is None:
      group_id = transaction.group_id
      update_group_transaction(buyer_id, group_id, price)

    else:
      borrower_id = transaction.borrower_id
      price = (price/2)
      update_individual_transaction(buyer_id, borrower_id, price)

    transaction.price = new_price
    transaction.update()

    return jsonify({
        'success': True,
    })


  @app.route('/transactions', methods=['POST'])
  @requires_auth('post:transactions')
  def add_transaction(payload):
    body = request.get_json()
    item = body.get('item', None)
    price = body.get('price', None)
    buyer_id = body.get('buyer_id', None)
    borrower_id = body.get('borrower_id', None)
    group_id = body.get('group_id', None)

    try:
      new_transaction = Transaction(item=item, price=price, buyer_id=buyer_id,
                              borrower_id=borrower_id, group_id=group_id
                              )
      new_transaction.insert()
 
    except:
        abort(422)

    buyer = User.query.filter_by(id=buyer_id).one()

    if not group_id:
      price = (price/2)
      update_individual_transaction(buyer_id, borrower_id, price)

    else:
      update_group_transaction(buyer_id, group_id, price)

    return jsonify({
        'success': True
    })


  @app.errorhandler(422)
  def unprocessable(error):
     return jsonify({
                     "success": False, 
                     "error": 422,
                     "message": "unprocessable"
                     }), 422


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404


  @app.errorhandler(AuthError)
  def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


  return app


APP = create_app()

if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=8080, debug=True)