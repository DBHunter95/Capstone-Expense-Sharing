# Expense Sharing App

### Introduction


This app is for the capstone project of the Udacity full stack developer course. It is designed to show the use of RESTful APIs built in a Python Flask Application. It serves the frontend found in this repository: https://github.com/DBHunter95/Expense-sharing-frontend.

The app is currently live on Heroku and can be viewed here: https://expense-sharing-demo.herokuapp.com/

The purpose of the app is to help groups of people share expenses. If someone in a group, for example a household, is buying something for everyone they can enter the transaction into the app and the app will determine how much the buyer is owed from each person (be it for a group or just 1 other individual). It will then maintain records of the total each user is owed/owes from each other user and in total across all transactions.


### Hosting locally

The app is currently live on heroku, however if you want to run the app locally you can do so by downloading all requiremnts from the requirements.txt folder and then from the command line exporting FLASK_APP=app.py and then flask run.

Note: There was a unusual error where in order for the code to run effectively locally the import addresses in the app.py file had to be ".models" and ".auth" rather than "models" and "auth". If you are experiencing errors running the app locally please adjust this.


### Roles

!!! Currently the Role Based Authorisation has been disabled in order to make the app more easily viewable !!!

The app is equipped with two roles through Auth0: administrators and users. The administrators have total permissions over all the endpoints whilst the users can use all endpoints except those that edit existing transactions. All endpoints require a Json token.

## API Reference

The app is currently deployed to Herkou where it can be sent curl requests using the URL: https://expense-sharing-app.herokuapp.com

### Error Handling

Errors are returned as JSON objects in the following format:

```
{"error":404,"message":"resource not found","success":false}
```

The API will return 3 error types when requests fail:

- 404 Recourse not found
- 422 Unprocessable
- 401 Not Authorized


### Endpoints

POST /users

- Adds a user to a database. Requires a jSON object describing the users name. Returns a JSON success message and the new user information. 

- Sample:

```
curl --request POST --header "Content-Type: application/json" --data '{"name":"Pail"}' --header '<JSON-Token>' https://expense-sharing-app.herokuapp.com/users
```

```
{"new_user":{"id":3,"name":"Pail","outstanding":{},"total_owed":0.0},"success":true}
```

POST /groups

- Adds a groups to the database. Requires a Json object with the group name and a dictionary with the primary keys of the groups members. Returns a JSON success message and the new group information.

- Sample:

```
curl --request POST --header "Content-Type: application/json" --data '{"name":"House", "users":[1,2,3]}' --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/groups
```

```
{"new_group":{"id":1,"members":[{"id":1,"name":"raul"},{"id":2,"name":"Linda"},{"id":3,"name":"Pail"}],"name":"House"},"success":true}
```

GET /users

- Queries the database for all users and returns a JSON list of users along with the total amount of money they are owed and an array representing how much each individual user owes the other named "outsanding". 

- Sample:

``` 
curl --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/users
 ```

```
{"success":true,"users":[{"id":2,"name":"raul","outstanding":{"1":-1.0},"total_owed":-1.0},{"id":3,"name":"Jedediah","outstanding":{"1":-1.0},"total_owed":-1.0},{"id":1,"name":"david","outstanding":{"1":-1.0,"2":1.0,"3":1.0},"total_owed":2.0}]}
```

GET /groups

- Queries the database and returns a JSON list of the groups as well as a dictionary with their members.

- Sample:

``` 
curl --header '<JSON Token> https://expense-sharing-app.herokuapp.com/groups
 ```

```
{"groups":[{"id":1,"members":[{"id":1,"name":"david"},{"id":2,"name":"raul"},{"id":3,"name":"Jedediah"}],"name":"House"}],"success":true}
```

POST /transactions

- adds a transaction to the database, also passes the information through to other functions in order to update the expense records of the user's involved in the transaction. Requires a Json object containing the item name, price, the primary key of the buyer, and the group primary key or the primary key of the 'borrower'.

``` 
curl --request POST --header "Content-Type: application/json" --data '{"item":"milk","price":3,"buyer_id":1,"group_id":1}' --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/transactions
```

```
{"success":true,"transaction":{"borrower id":null,"borrower_name":"","buyer_id":1,"buyer_name":"raul","date":null,"group_id":1,"group_name":"house","id":2,"price":3.0}}
```

GET /transactions

- Queries the database and returns a JSON list of transactions.

- Sample:

```
 curl --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/transactions 
```

```
{"success":true,"transactions":[{"borrower id":null,"borrower_name":"","buyer_id":1,"buyer_name":"david","date":null,"group_id":1,"group_name":"House","id":3,"price":3.0}]}
```

DELETE /transactions/<id>

- Deletes a transaction from the database and updates user records accordingly. Returns a success message and the ID of the deleted transaction.

- Sample:

```
curl --request DELETE --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/transactions/1
```

PATCH /transactions/<id>

- Edits the price of an existing transaction and updates the records of the users accordingly. Requires a JSON object with the the new price. Returns a JSON success message.

- Sample:

```
curl --request PATCH --header "Content-Type: application/json" --data '{"price":6}' --header '<JSON Token>' https://expense-sharing-app.herokuapp.com/transactions/3
```  

### Testing

A unittest can be run using the test_app.py file. This test can be performed locally, to run the tests adjust the database URL in "models.py" to an empty local database and uncomment the "db_drop_and_create_all()" line in the setup_db function. Then you can run the test using "python test_app.py" in the command line. 









