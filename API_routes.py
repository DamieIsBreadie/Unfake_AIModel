from flask import Blueprint, request, jsonify
from AImodel import load_model, model_predict
import firebase_admin
from firebase_admin import credentials, firestore
from checked_algorithm import classify_news
import math
import re

#from adlina's scraping file
# from scrapfly_scraper import scrape_single_tweet



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
        post_id = data.get("post_id")

        if not text or not post_id:
            return jsonify({"error": "Missing text or post_id"}), 400

        # 🔹 Convert post_id to Firestore-safe format
        safe_post_id = re.sub(r'[:/.]', '-', post_id)

        # 🔹 Step 1: Check if AI result exists
        doc_ref = db.collection("ai_result").document(safe_post_id)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200  # Return existing result

        # 🔹 Step 2: Compute AI prediction
        label, confidence = model_predict(text, model)
        result_data = {
            "post_id": safe_post_id,  # Store safe ID
            "results": {
                "prediction": label,
                "confidence": confidence
            },
            "text": text
        }

        # 🔹 Step 3: Save AI result in Firestore
        db.collection("ai_result").document(safe_post_id).set(result_data)

        print(f"[DEBUG] AI prediction stored for post_id: {safe_post_id}")

        return jsonify(result_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route("/get-ai-result", methods=["GET"])
def get_ai_result():
    tweet_url = request.args.get("tweetUrl")
    if not tweet_url:
        return jsonify({"error": "Missing tweet URL"}), 400

    tweet_id = tweet_url.split("/")[-1]  # Extract tweet ID from URL
    doc_ref = db.collection("ai_result").document(tweet_id)
    doc = doc_ref.get()

    if not doc.exists:
        # Return an empty object or default values if no AI result exists
        return jsonify({}), 200

    ai_data = doc.to_dict()
    return jsonify(ai_data), 200

@api.route("/get-checked-result", methods=["GET"])
def get_checked_result():
    tweet_url = request.args.get("tweetUrl")
    if not tweet_url:
        return jsonify({"error": "Missing tweet URL"}), 400

    # 🔹 Extract tweet ID from the URL (same as get-vote-count)
    tweet_id = tweet_url.split("/")[-1]  # Extract only the tweet ID
    safe_post_id = re.sub(r'[:/.]', '-', tweet_id)  # 🔹 Sanitize tweet ID

    print(f"[DEBUG] Checking for results for post_id: {safe_post_id}")

    # 🔹 Step 1: Check for Checked Algorithm results first
    checked_doc = db.collection("checkedAlgo_result").document(safe_post_id).get()
    if checked_doc.exists:
        print(f"[DEBUG] Returning Checked Algorithm result for {safe_post_id}")
        return jsonify(checked_doc.to_dict()), 200

    # 🔹 Step 2: If no Checked Algorithm result, return AI result
    ai_doc = db.collection("ai_result").document(safe_post_id).get()
    if ai_doc.exists:
        print(f"[DEBUG] Returning AI result for {safe_post_id}")
        return jsonify(ai_doc.to_dict()), 200

    # 🔹 Step 3: If neither exists, return an empty response
    print(f"[DEBUG] No AI or Checked Algorithm result found for {safe_post_id}")
    return jsonify({"error": "No AI or Checked Algorithm results found"}), 404

# --------- Fetch Final (Checked Algorithm) Results --------
@api.route("/result", methods=["GET"])
def get_final_results():
    post_id = request.args.get("post_id")

    # # 🔹 Convert post_id to match the format stored in Firestore
    # safe_post_id = re.sub(r'[:/.]', '-', post_id)

    if not post_id:
        return jsonify({"error": "No Post ID detected"}), 400
    
    # 🔹 Convert post_id to match the format stored in Firestore
    safe_post_id = re.sub(r'[:/.]', '-', post_id)

    print(f"[DEBUG] Retrieving result for post_id: {post_id}")

    # 🔹 Step 1: Retrieve AI result from Firestore
    ai_doc = db.collection("ai_result").document(safe_post_id).get()
    if not ai_doc.exists:  # ✅ FIXED: Removed ()
        return jsonify({"error": "AI result not found"}), 404

    ai_data = ai_doc.to_dict()
    probability_real = ai_data["results"]["confidence"][1]

    # Compute entropy for AI confidence
    conf = ai_data["results"]["confidence"]
    model_entropy = - (conf[0] * math.log(conf[0] + 1e-10) + conf[1] * math.log(conf[1] + 1e-10))

    # 🔹 Step 2: Check for votes in `x_posts`
    post_doc = db.collection("x_posts").document(post_id).get()
    user_votes = []

    if post_doc.exists:
        post_data = post_doc.to_dict()
        votes_count = post_data.get("votes_count", {})
        total_votes = post_data.get("total_votes", 0)

        print(f"[DEBUG] Total votes: {total_votes}")
        print(f"[DEBUG] Vote breakdown: {votes_count}")

        # 🔹 If no votes exist, return AI results only
        if total_votes == 0:
            return jsonify({
                "post_id": post_id,
                "results": ai_data["results"],
                "message": "No user votes yet, returning AI result only."
            }), 200

        # Process user votes
        credibility_per_vote = 1.0 / total_votes if total_votes > 0 else 0.5

        for category, count in votes_count.items():
            vote_value = 1 if category == "Real" else 0  
            for _ in range(count):
                user_votes.append({"vote_value": vote_value, "credibility": credibility_per_vote})

        print(f"[DEBUG] Processed user votes: {user_votes}")

    # 🔹 If no votes exist, return AI results only
    if not user_votes:
        return jsonify({
            "post_id": post_id,
            "results": ai_data["results"],
            "message": "No user votes yet, returning AI result only."
        }), 200

    # 🔹 Step 3: Run Checked Algorithm if votes exist
    final_score, classification = classify_news(probability_real, model_entropy, user_votes)

    print(f"[DEBUG] Final Score: {final_score}, Classification: {classification}\n")

    # 🔹 Step 4: Save Checked Algorithm result
    checked_algo_result = {
        "post_id": post_id,
        "result": {
            "final_score": final_score,
            "classification": classification
        }
    }

    db.collection("checkedAlgo_result").document(post_id).set(checked_algo_result)
    print(f"[DEBUG] Successfully saved result for {post_id} in checkedAlgo_result")

    return jsonify({"final_score": final_score, "classification": classification}), 200
