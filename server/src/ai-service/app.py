
from flask import Flask, request, jsonify
from flask_cors import CORS

from summaryEngine import summarize_text


# Create Flask application
app = Flask(__name__)

# Allow requests from the Node/React application
CORS(app)


# Health check
@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "message": "AI Service is running"
    })


# Summary endpoint
@app.route("/summarize", methods=["POST"])
def summarize():

    try:

        # Get JSON body
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        # Get text from request
        text = data.get("text")

        if not text:
            return jsonify({
                "success": False,
                "message": "Text is required"
            }), 400

        print("\n===== REQUEST RECEIVED =====")
        print(text)

        # Send text to Summary Engine (returns a parsed dictionary)
        summary_data = summarize_text(text)

        print("\n===== PARSED SUMMARY =====")
        print(summary_data)

        # Send structured JSON back to Node
        return jsonify({
            "success": True,
            "data": summary_data
        })

    except Exception as error:

        print("\n===== AI SERVICE ERROR =====")
        print(error)

        return jsonify({
            "success": False,
            "message": "Failed to generate summary",
            "error": str(error)
        }), 500


# Start Flask server
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
