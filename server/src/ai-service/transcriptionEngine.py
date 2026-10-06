import os
import subprocess
import tempfile
import shutil
import imageio_ffmpeg
from faster_whisper import WhisperModel

# Global model singleton to avoid reloading model on every request
_whisper_model = None

def get_ffmpeg_path():
    """Get the path to the FFmpeg executable."""
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        # Fallback to system ffmpeg if available
        return "ffmpeg"


def get_whisper_model(model_size="base", device="cpu", compute_type="int8"):
    """Get or initialize the faster-whisper model singleton."""
    global _whisper_model
    if _whisper_model is None:
        print(f"[TranscriptionEngine] Loading Faster-Whisper model ({model_size}, {device}, {compute_type})...")
        _whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[TranscriptionEngine] Faster-Whisper model ready!")
    return _whisper_model


def extract_audio(input_file_path, output_audio_path=None):
    """
    Extract 16kHz mono audio from video (e.g. .mp4) using FFmpeg.
    Returns the path to the extracted WAV audio file.
    """
    ffmpeg_exe = get_ffmpeg_path()
    
    if output_audio_path is None:
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_audio_path = temp_audio.name
        temp_audio.close()

    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite output without asking
        "-i", input_file_path,
        "-vn",              # Disable video
        "-acodec", "pcm_s16le", # 16-bit PCM WAV
        "-ar", "16000",     # 16kHz sampling rate
        "-ac", "1",         # Mono channel
        output_audio_path
    ]

    print(f"[TranscriptionEngine] Extracting audio using FFmpeg: {input_file_path} -> {output_audio_path}")
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode != 0:
        error_msg = process.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg audio extraction failed: {error_msg}")

    return output_audio_path


def transcribe_file(file_path, model_size="base"):
    """
    Transcribe a video (.mp4, .mkv, etc.) or audio file using FFmpeg and Faster-Whisper.
    Returns a dictionary with transcript, language, duration, and segments.
    """
    extracted_audio = None
    try:
        # Extract audio as 16kHz mono WAV using FFmpeg for reliable decoding
        extracted_audio = extract_audio(file_path)

        model = get_whisper_model(model_size=model_size)

        print("[TranscriptionEngine] Starting transcription...")
        segments_gen, info = model.transcribe(
            extracted_audio,
            beam_size=5,
            vad_filter=True, # Voice activity detection to filter silence
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments = []
        full_text_list = []

        for segment in segments_gen:
            text = segment.text.strip()
            if text:
                segments.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text
                })
                full_text_list.append(text)

        full_transcript = " ".join(full_text_list).strip()

        print(f"[TranscriptionEngine] Transcription complete. Language: {info.language} ({info.language_probability:.2f}), Duration: {info.duration:.1f}s")
        print(f"[TranscriptionEngine] Transcript length: {len(full_transcript)} characters")

        return {
            "transcript": full_transcript,
            "language": info.language,
            "languageProbability": round(info.language_probability, 2),
            "duration": round(info.duration, 2),
            "segments": segments
        }

    finally:
        # Clean up temporary extracted audio file
        if extracted_audio and os.path.exists(extracted_audio):
            try:
                os.remove(extracted_audio)
            except Exception as e:
                print(f"[TranscriptionEngine] Warning: Failed to clean up temp audio {extracted_audio}: {e}")
