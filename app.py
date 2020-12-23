import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json

from .models import setup_db, Transaction, User, Group, members, db_drop_and_create_all
from .auth import AuthError, requires_auth

# This is a function for updating user records when a group transaction is made.
# It divides the price by the number of members of the group and then loops through every member of the group
# updating the debt lists and the total each user is owed
# Each user has a python dictionary called outstanding which stores their debts with other users
# The key's in these dictionaries are the other users ID'd and the value's are the debts

def update_group_transaction(buyer_id, group_id, price):

  group = Group.query.filter_by(id = group_id).one()
  buyer = User.query.filter_by(id = buyer_id).one()
  buyer_records = json.loads(buyer.outstanding)
  amount = price/len(group.people)

  try:
    for user in group.people:
      if buyer.id == user.id:
        continue

      borrower_records = json.loads(user.outstanding)
      buyer_key = "%d" % buyer.id # This format is necessary for updating the "outstanding" dictionary to avoid duplicate entries.
      borrower_key = "%d" % user.id

      if buyer_key in borrower_records:
        buyer_records[borrower_key] += amount
        borrower_records[buyer_key] -= amount 
      
      else:
        buyer_records[borrower_key] = amount
        borrower_records[buyer_id] = -amount
      
      buyer.outstanding = json.dumps(buyer_records)
      user.outstanding = json.dumps(borrower_records)
      user.total_owed -= amount
      buyer.total_owed += amount
      buyer.update()
      user.update()
  
  except:
    abort(422)

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
  def get_users():
    selection = User.query.all()
    users = [user.format() for user in selection]

    return jsonify({
      'success': True,
      'users': users
    })


  @app.route('/groups')
  def get_groups():
    selection = Group.query.all()
    groups = [group.format() for group in selection]

    return jsonify({
      'success': True,
      'groups': groups
    })


  @app.route('/transactions')
  def get_transactions():
    selection = Transaction.query.all()
    transactions = [transaction.format() for transaction in selection]

    return jsonify({
      'success': True,
      'transactions': transactions
    })


  @app.route('/users', methods=['POST'])
  def add_user():
    body = request.get_json()
    name = body.get('name', None)
    
    # try:
    new_user = User(name=name, outstanding=json.dumps({}), total_owed=0)
    new_user.insert()
 
    # except:
    #   abort(422)

    return jsonify({
        'success': True,
        'new_user': new_user.format()
    })


  @app.route('/groups', methods=['POST'])
  def add_group():
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
        'success': True,
        'new_group': new_group.format()
    })

  @app.route('/users/<id>', methods=['DELETE'])
  def delete_user(id):

    user = User.query.filter_by(id = id).one_or_none()

    if user is None:
      print(id)
      abort(404)
        

    user.delete()

    return jsonify({
        'success': True,
        'delete': id
    })

  
  @app.route('/groups/<id>', methods=['DELETE'])
  def delete_group(id):

    group = Group.query.filter_by(id = id).one_or_none()

    if group is None:
        abort(404)
        
    group.delete()

    return jsonify({
        'success': True,
        'delete': id
    })


  @app.route('/transactions/<id>', methods=['DELETE'])
  def delete_transaction(id):

    transaction = Transaction.query.filter_by(id = id).one_or_none()

    if transaction is None:
        abort(404)

    #If statement to confirm price is a number, if it is not a number it does not try to update the debt list
    if isinstance(transaction.price, int) or isinstance(transaction.price, float):
      #This updates the record of debts by passing the negative price to the appriate function (group or individual)
      buyer = User.query.filter_by(id = transaction.buyer_id).one()
      price = -transaction.price
      buyer_id = transaction.buyer_id
      group_id = transaction.group_id
    
      #Determines if the transaction was a group or individual transaction
      if transaction.borrower_id is None or transaction.borrower_id == 0:
        #If statement in case group has been deleted when someone tries to delete the transaction
        if group_id is None or group_id == 0:
          pass
        else:
          group_id = transaction.group_id
          update_group_transaction(buyer_id, group_id, price)

      else:
        borrower_id = transaction.borrower_id
        price = (price/2)
        update_individual_transaction(buyer_id, borrower_id, price) 
        
    #pass statement for if price is not a number or contains extra characters
    else:
      pass

    transaction.delete()

    return jsonify({
        'success': True,
        'delete': id
    })
        

  @app.route('/transactions/<id>', methods=['PATCH'])
  def update_transaction(id):
    transaction = Transaction.query.filter_by(id = id).one_or_none()
    body = request.get_json()
    new_price = body.get('price', None)

    if transaction is None:
        abort(404)

    # this section updates the debt records with the new price
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
        'transaction': transaction.format()
    })


  @app.route('/transactions', methods=['POST'])
  def add_transaction():
    body = request.get_json()
    item = body.get('item', None)
    price = body.get('price', None)
    buyer_id = body.get('buyer_id', None)
    borrower_id = body.get('borrower_id', None)
    group_id = body.get('group_id', None)

    # try:
    new_transaction = Transaction(item=item, price=price, buyer_id=buyer_id,
                            borrower_id=borrower_id, group_id=group_id
                            )
    new_transaction.insert()
 
    # except:
    #     abort(422)

    buyer = User.query.filter_by(id=buyer_id).one()

    #Updates the user debts
    if not group_id:
      price = (price/2)
      update_individual_transaction(buyer_id, borrower_id, price)

    else:
      update_group_transaction(buyer_id, group_id, price)

    return jsonify({
        'success': True,
        'transaction': new_transaction.format()
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


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)