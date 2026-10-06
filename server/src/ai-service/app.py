import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from summaryEngine import summarize_text
from transcriptionEngine import transcribe_file

# Create Flask application
app = Flask(__name__)

# Allow requests from the Node/React application
CORS(app)

# Ensure temporary upload directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "temp_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "AI Service is running",
        "features": ["text-summarization", "video-transcription", "video-summarization"]
    })


# Text Summary endpoint
@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        text = data.get("text")

        if not text:
            return jsonify({
                "success": False,
                "message": "Text is required"
            }), 400

        print("\n===== TEXT SUMMARY REQUEST RECEIVED =====")
        print(f"Input text length: {len(text)} chars")

        summary_data = summarize_text(text)

        print("\n===== PARSED SUMMARY =====")
        print(summary_data)

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


# Video/Audio Transcribe endpoint
@app.route("/transcribe", methods=["POST"])
def transcribe_video_endpoint():
    temp_path = None
    try:
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "No file provided. Please upload a file with field name 'file'."
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        filename = secure_filename(file.filename) or "uploaded_video.mp4"
        suffix = os.path.splitext(filename)[1] or ".mp4"

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=app.config["UPLOAD_FOLDER"])
        temp_path = temp_file.name
        file.save(temp_path)
        temp_file.close()

        print(f"\n===== VIDEO TRANSCRIPTION REQUEST RECEIVED =====")
        print(f"Filename: {filename}, Saved to temp: {temp_path}")

        # Transcribe with FFmpeg + Faster-Whisper
        transcription_result = transcribe_file(temp_path)

        return jsonify({
            "success": True,
            "data": transcription_result
        })

    except Exception as error:
        print("\n===== TRANSCRIPTION ERROR =====")
        print(error)

        return jsonify({
            "success": False,
            "message": "Failed to transcribe video",
            "error": str(error)
        }), 500

    finally:
        # Clean up temporary uploaded video file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Failed to delete temp file {temp_path}: {e}")


# Video Upload -> Transcribe -> Summarize combined endpoint
@app.route("/summarize-video", methods=["POST"])
def summarize_video_endpoint():
    temp_path = None
    try:
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "No file provided. Please upload a file with field name 'file'."
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        filename = secure_filename(file.filename) or "uploaded_video.mp4"
        suffix = os.path.splitext(filename)[1] or ".mp4"

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=app.config["UPLOAD_FOLDER"])
        temp_path = temp_file.name
        file.save(temp_path)
        temp_file.close()

        print(f"\n===== VIDEO SUMMARIZATION REQUEST RECEIVED =====")
        print(f"Filename: {filename}, Saved to temp: {temp_path}")

        # Step 1: Transcribe video using local FFmpeg and Faster-Whisper
        transcription_result = transcribe_file(temp_path)
        transcript = transcription_result.get("transcript", "").strip()

        if not transcript:
            return jsonify({
                "success": False,
                "message": "No speech detected in the uploaded video.",
                "data": {
                    "transcript": "",
                    "summary": None
                }
            }), 400

        print(f"\n===== TRANSCRIPT READY FOR SUMMARY ENGINE =====")
        print(f"Transcript ({len(transcript)} chars): {transcript[:200]}...")

        # Step 2: Send transcribed text to Summary Engine
        summary_data = summarize_text(transcript)

        print("\n===== VIDEO SUMMARY GENERATED SUCCESSFULLY =====")

        return jsonify({
            "success": True,
            "data": {
                "transcript": transcript,
                "language": transcription_result.get("language"),
                "duration": transcription_result.get("duration"),
                "segments": transcription_result.get("segments"),
                "summary": summary_data
            }
        })

    except Exception as error:
        print("\n===== VIDEO SUMMARIZATION ERROR =====")
        print(error)

        return jsonify({
            "success": False,
            "message": "Failed to process and summarize video",
            "error": str(error)
        }), 500

    finally:
        # Clean up temporary uploaded video file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Failed to delete temp file {temp_path}: {e}")


# Start Flask server
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
