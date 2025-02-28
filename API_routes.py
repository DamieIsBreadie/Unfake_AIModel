from flask import Blueprint, request, jsonify
from AImodel import load_model, model_predict
import firebase_admin
from firebase_admin import credentials, firestore
from checked_algorithm import classify_news

#from adlina's scraping file
from scrapfly_scraper import scrape_single_tweet



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


# -------- GET Post --------
@api.route("/fetch_post", methods=["POST"])
def fetch_post():
    data = request.get_json()
    post_id = data.get("post_id")

    if not post_id:
        return jsonify({"error": "No Post ID provided"})

    # check post exists in database
    post_reference = db.collection("posts").document(post_id)
    post = post_reference.get()

    if post.exists:
        return jsonify({"post": post.to_dict(), "source": "database"})
    else:
        # implement scraping if not exist in database
        scraped_post = scrape_single_tweet(f"https://x.com/status/{post_id}")

        if scraped_post:
            post_reference.set({
                "post_id": post_id, "tweet_text": scraped_post["tweet_text"],
                "tweet_link": scraped_post["tweet_link"]
            })

            return jsonify({"post": scraped_post, "source": "scraper"})
        else:
            return jsonify({"error": "Failed to fetch post"}), 500


# -------- GET Prediction (run model) --------
@api.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text")
        post_id = data.get("post_id")  # new field for the tweet/post id

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # If a post_id is provided, check if a prediction already exists
        if post_id:
            doc_ref = db.collection("ai_result").document(post_id)
            doc = doc_ref.get()
            if doc.exists:
                # Return the existing AI result
                return jsonify(doc.to_dict()), 200

        # Compute prediction as none exists
        label, confidence = model_predict(text, model)
        result_data = {
            "post_id": post_id,
            "results": {
                "prediction": label,
                "confidence": confidence
            },
            "text": text
        }

        # Save the result in Firestore if post_id is provided
        if post_id:
            db.collection("ai_result").document(post_id).set(result_data)

        return jsonify(result_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------- Store user votes and update to database --------
@api.route("/vote", methods=["POST"])
def store_user_vote():
    data = request.get_json()
    post_id = data.get("post_id")
    user_id = data.get("user_id")
    user_votes = data.get("user_votes")

    if not all([post_id, user_id, user_votes]):
        return jsonify({"error": "Missing required fields"}), 400

    save_user_vote(post_id, user_id, user_votes)

    return jsonify({"message": "Vote saved successfully"})


# --------- Fetch Final (Checked Algorithm) Results --------
@api.route("/result", methods=["GET"])
def get_final_results():
    post_id = request.args.get("post_id")

    if not post_id:
        return jsonify({"error": "No Post ID detected"}), 400

    final_results = classify_news(post_id)

    if "error" in final_results:
        return jsonify(final_results), 404

    return jsonify(final_results)
