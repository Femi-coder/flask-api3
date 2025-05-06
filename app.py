from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymongo
import os

#  Initialize Flask App
app = Flask(__name__)
CORS(app)

#  MongoDB Connection
MONGO_URI = os.getenv("MONGODB_ATLAS_URI", "mongodb+srv://Femi:password_123@ecowheelsdublin.zpsyu.mongodb.net")
client = pymongo.MongoClient(MONGO_URI)
db = client["carrental"]
transactions_collection = db["transactions"]
vehicles_collection = db["vehicles"]

# Define Route for Returning Cars
@app.route("/api/return-car", methods=["POST"])
def return_car():
    try:
        data = request.get_json()
        transaction_id = data.get("transaction_id")

        if not transaction_id:
            return jsonify({"error": "Missing transaction_id"}), 400

        # Find the transaction
        transaction = transactions_collection.find_one({"transaction_id": transaction_id})
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        if transaction.get("status") == "returned":
            return jsonify({"error": "Car already returned"}), 400

        # Convert string date to datetime
        due_date = datetime.strptime(transaction.get("end"), "%Y-%m-%d")
        return_time = datetime.utcnow()
        late_fee = 0

        if return_time > due_date:
            late_days = (return_time - due_date).days
            late_fee = late_days * 20  # Charge €20 per late day

        # Update transaction status in DB
        transactions_collection.update_one(
            {"transaction_id": transaction_id},
            {
                "$set": {
                    "status": "returned",
                    "return_time": return_time,
                    "late_fee": late_fee
                }
            }
        )

        #Makes vehicle available again
        vehicle_id = int(transaction["vehicle_id"])  # Convert vehicle_id to int
        vehicles_collection.update_one(
            {"carId": vehicle_id},
            {"$set": {"available": True}}  # Sets vehicle as available
        )

        return jsonify({
            "status": "success",
            "message": "Car returned successfully",
            "late_fee": late_fee
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#  Run the Flask App
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
