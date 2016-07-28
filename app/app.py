from flask import Flask, request, render_template, make_response, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib

app = Flask(__name__)

client = MongoClient("mongodb://admin:admin@ds023624.mlab.com:23624/bcamarketplace")
db = client.get_default_database()

userCollection = db.users
itemCollection = db.catalog
wantedItems = db.wantedItems

def hashPassword(password):
	return hashlib.md5(password.encode()).hexdigest()

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	first_name = ""
	last_name = ""
	username = request.form["username"]
	print(username)
	password = request.form["password"]

	password = hashPassword(str(password))

	print(password)

	users = userCollection.find({"username" : username, "password" : password})

	if (users.count() == 1):
		first_name = users[0]["firstName"]
		last_name = users[0]["lastName"]
		resp = make_response(redirect("/profile"))
		resp.set_cookie('username', username)
		resp.set_cookie('first_name', first_name)
		resp.set_cookie('last_name', last_name)
		print(request.cookies.get("username"))
		return resp

	else:
		return render_template("index.html", message="Account with the given username and password does not exist")


@app.route("/newaccount")
def create_account():
	return render_template("newaccount.html")

@app.route("/accountcreated", methods=["GET", "POST"])
def account_created():
	first_name = request.form["firstname"]
	last_name = request.form["lastname"]
	email = request.form["email"]
	username = request.form["username"]
	password = request.form["password"]
	
	count = userCollection.find({"username" : username}).count()

	if (count == 0):
		userCollection.insert({
			"firstName" : first_name,
			"lastName" : last_name,
			"email" : email,
			"username" : username,
			"password" : hashPassword(str(password))
		});
		return render_template("index.html", message="Thank you for registering, " + first_name)

	else:
		return render_template("newaccount.html", message="Username already taken")

@app.route("/catalog")
def catalog():
	username = request.cookies.get("username")
	items = itemCollection.find()
	print(username)
	return render_template("catalog.html", items=items, username=username)

@app.route("/sellsomething")
def sellsomething():
	return render_template("sell.html")

@app.route("/sell", methods=["GET", "POST"])
def sell():
	title = request.form["title"]
	description = request.form["description"]
	price = request.form["price"]

	insertedItemId = itemCollection.insert({
		"id" : 0,
		"title" : title,
		"description" : description,
		"price" : price,
		"owner" : request.cookies.get("username")
	});

	itemCollection.update({'_id': ObjectId(insertedItemId)}, {"$set": {"id" : ObjectId(insertedItemId)}}, upsert=False)

	print(ObjectId(insertedItemId))
	items = itemCollection.find()

	return render_template("catalog.html", items=items)

@app.route("/profile")
def profile():
	first_name = request.cookies.get("first_name")
	last_name = request.cookies.get("last_name")
	username = request.cookies.get("username")
	user = userCollection.find({"username" : username})

	itemsPlaced = itemCollection.find({"owner" : username})
	itemsRequested = wantedItems.find({"owner" : username})

	resp = make_response(render_template("profile.html", name=first_name + " " + last_name, itemsPlaced=itemsPlaced, itemsRequested = itemsRequested))
	return resp

@app.route("/buy", methods=["GET", "POST"])
def buy():
	itemId = request.form["itemId"]
	print(itemId)
	item = itemCollection.find({"_id" : ObjectId(itemId)})
	return render_template("cart.html", item=item)

@app.route("/sold", methods=["GET", "POST"])
def sold():
	first_name = request.cookies.get("first_name")
	last_name = request.cookies.get("last_name")
	username = request.cookies.get("username")
	itemId = request.form["itemId"]
	user = userCollection.find({"username" : username})

	itemCollection.delete_many({"_id": ObjectId(itemId)})
	wantedItems.delete_many({"id": ObjectId(itemId)})

	itemsPlaced = itemCollection.find({"owner" : username})

	resp = make_response(render_template("profile.html", name=first_name + " " + last_name, itemsPlaced=itemsPlaced))
	return resp

@app.route("/confirmbuy", methods=["GET", "POST"])
def confirmbuy():
	itemId = request.form["itemId"]
	print(itemId)
	item = itemCollection.find({"_id" : ObjectId(itemId)})
	print(ObjectId(itemId))
	return render_template("buy.html", item=item[0])


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
	itemId = request.form["itemId"]
	username = request.cookies.get("username")
	user = userCollection.find({"username" : username})
	item = itemCollection.find({"_id" : ObjectId(itemId)})
	price = request.form["price"]
	comments = request.form["comments"]

	wantedItems.insert({
		"id" : ObjectId(itemId),
		"title" : item[0]["title"],
		"description" : item[0]["description"],
		"itemPrice" : item[0]["price"],
		"owner" : item[0]["owner"],
		"purchaser" : username,
		"priceOffered" : price
	});

	itemsPlaced = itemCollection.find({"owner" : username})


	resp = make_response(render_template("profile.html", name=user[0]["firstName"] + " " + user[0]["lastName"], itemsPlaced=itemsPlaced))
	return resp

@app.route("/acceptoffer", methods=["GET", "POST"])
def acceptoffer():
	first_name = request.cookies.get("first_name")
	last_name = request.cookies.get("last_name")
	username = request.cookies.get("username")
	itemId = request.form["itemId"]
	user = userCollection.find({"username" : username})

	itemCollection.delete_many({"id": ObjectId(itemId)})
	wantedItems.delete_many({"id": ObjectId(itemId)})

	itemsPlaced = itemCollection.find({"owner" : username})

	resp = make_response(render_template("profile.html", name=first_name + " " + last_name, itemsPlaced=itemsPlaced))
	return resp

if __name__ == "__main__":
	app.run()
