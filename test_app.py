import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from app import create_app
from models import setup_db, User, Group, Transaction, db_drop_and_create_all, members
from config import administrator_token, user_token


class Lending_Test(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "lending_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app)

        self.new_user1 = {
            'name': 'Jedediah'
        }

        self.new_user2 = {
            'name': 'Barbara'
        }

        self.new_group = {
            'name': 'house',
            'users': [1,2]
        }

        self.new_transaction = {
            'item':'milk',
            'price': 3,
            'buyer_id': 1,
            'group_id': 1
        }

        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    '''Tests for adding a new user'''

    def test_add_user(self):
        res = self.client().post('/users', json = self.new_user1, headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_add_user_without_authorization(self):
        res = self.client().post('/users', json = self.new_user1)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)

    '''Tests for adding a new group'''

    def test_add_group(self):
        res = self.client().post('/groups', json = self.new_group, headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_add_group_without_authorization(self):
        res = self.client().post('/groups', json = self.new_group)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)

    '''Tests for adding a new transaction'''
    
    def test_add_transaction(self):
        res = self.client().post('/transactions', json = self.new_transaction, headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_add_transaction_without_authorization(self):
        res = self.client().post('/transactions', json = self.new_transaction)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)

    '''Tests for the 'GET' endpoints'''

    def test_get_users(self):
        res = self.client().get('/users', headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_get_users_without_authorization(self):
        res = self.client().get('/users')

        self.assertEqual(res.status_code, 401)

    def test_get_groups(self):
        res = self.client().get('/groups', headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_get_groups_without_authorization(self):
        res = self.client().get('/groups')

        self.assertEqual(res.status_code, 401)

    def test_get_transactions(self):
        res = self.client().get('/transactions', headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_get_transactions_without_authorization(self):
        res = self.client().get('/transactions')

        self.assertEqual(res.status_code, 401)

    '''Tests for Delete Transaction'''
   
    def test_delete_transactions(self):
        res = self.client().delete('/transactions/32', headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_delete_transactions_without_permission(self):
        res = self.client().delete('/transactions/33', headers = user_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)

    def test_update_transactions(self):
        update = {"price":6}
        res = self.client().patch('/transactions/34', json = update, headers = administrator_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_update_transactions_without_permissions(self):
        update = {"price":6}
        res = self.client().patch('/transactions/34', json = update, headers = user_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
