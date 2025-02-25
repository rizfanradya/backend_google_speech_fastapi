from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from utils.config import GEMINIAI_API_KEY
from models.speech_result import SpeechResult
from io import BytesIO
import tempfile
import os
import regex
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
        file_content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_audio:
            temp_audio.write(file_content)
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

        # Gemini AI
        ai_response = genai.GenerativeModel(
            "gemini-1.5-flash").generate_content(text_result)
        response_text = getattr(
            ai_response,
            "text",
            "Maaf, saya tidak dapat memahami."
        ).strip()

        # Text to Speech
        tts_response_audio_content = tts_client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=regex.sub(r"[^\p{L}\s.,!?;:]", "", response_text)
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

        # add database
        add_db = SpeechResult()
        add_db.user_id = token['id']
        add_db.ai_generated = response_text
        add_db.speech_to_text = text_result
        session.add(add_db)
        await session.commit()
        await session.refresh(add_db)

        abs_path = os.path.abspath(__file__)
        base_dir = os.path.dirname(os.path.dirname(abs_path))

        upload_dir = os.path.join(
            base_dir, 'data', 'uploads', 'input_file_audio')
        os.makedirs(upload_dir, exist_ok=True)
        file_extension_upload = file.filename.split('.')[-1]
        filename_upload = f'{add_db.id}.{file_extension_upload}'
        file_path_upload = os.path.join(upload_dir, filename_upload)
        add_db.input_file_audio = filename_upload
        with open(file_path_upload, 'wb') as f:
            f.write(file_content)

        download_dir = os.path.join(
            base_dir, 'data', 'downloads', 'output_file_audio')
        os.makedirs(download_dir, exist_ok=True)
        filename_download = f'{add_db.id}.wav'
        file_path_download = os.path.join(download_dir, filename_download)
        contents_download = BytesIO(tts_response_audio_content)
        add_db.output_file_audio = filename_download
        with open(file_path_download, 'wb') as f:
            f.write(contents_download.getvalue())

        await session.commit()
        return StreamingResponse(
            contents_download,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={filename_download}"
            })
    except Exception as error:
        send_error_response(str(error), "Internal server error")
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
