from flask import Blueprint, request, jsonify
from AImodel import load_model, model_predict
import firebase_admin
from firebase_admin import credentials, firestore

# -------- FLASK BLUEPRINT ---------
api = Blueprint("api", __name__)

# -------- Load Model --------
model = load_model()

# Initialize Firebase if it hasn't been already
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Get Firestore client (make sure Firebase has already been initialized in your main app)
db = firestore.client()

# -------- Flask Route Initialisation --------
@api.route("/")
def home():
    return "Unfake API is running!"

# -------- Fetch Prediction --------
@api.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text")
        post_id = data.get("post_id")  # new field for the tweet/post id

        if not text:
            return jsonify({"error": "No Link Provided"}), 400

        label, confidence = model_predict(text,model)

        # If post_id is provided, save the result to Firestore
        if post_id:
            result_data = {
                "post_id": post_id,
                "results": {
                    "prediction": label,
                    "confidence": confidence
                },
                "text": text
            }
            db.collection("ai_result").document(post_id).set(result_data)


        return jsonify({"prediction": label, "confidence": confidence})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------- Get Votes from users and update to database --------
""" @api.route("/vote", methods=["POST"])
def vote():
    return 
"""

#Parameters
# - text (containing the post content)
# - post_id (post's id)
# - results (a dictionary containing prediction and confidence)
#      - prediction
#      - confidence

# Table name: ai_result
