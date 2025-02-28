from flask import Flask, request, jsonify
from flask_cors import CORS
from API_routes import api


# -------- Initialise Flask --------
app = Flask(__name__)
CORS(app)

# -------- Register Flask API routes --------
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
