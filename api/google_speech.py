from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from utils.config import GEMINIAI_API_KEY
from io import BytesIO
import tempfile
import os
import re
import subprocess
from google.cloud import speech, texttospeech
import google.generativeai as genai

router = APIRouter()
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()
genai.configure(api_key=GEMINIAI_API_KEY)
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg"}


@router.post('/_speech')
async def create(file: UploadFile = File(...), session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        send_error_response(
            "Invalid file format. Allowed formats: MP3, WAV, OGG.")
    temp_audio_path = None

    try:
        # process audio
        file_ext = ".wav" if file.content_type == "audio/wav" else ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio_path = temp_audio.name

        if file_ext == ".mp3":
            temp_wav_path = temp_audio_path.replace(".mp3", ".wav")
            try:
                subprocess.run(
                    [
                        "ffmpeg", "-i", temp_audio_path, "-ar", "16000", "-ac", "1", "-f", "wav", temp_wav_path
                    ],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                raise Exception(f"FFmpeg conversion failed: {str(e)}")
            os.remove(temp_audio_path)
            temp_audio_path = temp_wav_path

        # Speech to Text
        with open(temp_audio_path, "rb") as audio_file:
            audio_content = audio_file.read()

        response_results = speech_client.recognize(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="id-ID",
            ),
            audio=speech.RecognitionAudio(content=audio_content)
        ).results

        if not response_results:
            send_error_response("Speech recognition failed.")
        text_result = response_results[0].alternatives[0].transcript
        print(f"Recognized text: {text_result}")

        # Gemini AI
        ai_response = genai.GenerativeModel(
            "gemini-1.5-flash").generate_content(text_result)
        response_text = getattr(ai_response, "text",
                                "Maaf, saya tidak dapat memahami.").strip()
        print(f"GeminiAI Response: {response_text}")

        # Text to Speech
        tts_response_audio_content = tts_client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=re.sub(r"[^\w\s]", "", response_text)
            ),
            voice=texttospeech.VoiceSelectionParams(
                language_code='id-ID',
                name='id-ID-Wavenet-D'
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000
            )
        ).audio_content

        return StreamingResponse(
            BytesIO(tts_response_audio_content),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=response.wav"}
        )
    except Exception as error:
        send_error_response(str(error), "Internal server error")
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
