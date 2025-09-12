# modules/voice_handler.py
import logging
import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def process_voice(self, voice_file) -> Optional[str]:
        """پردازش فایل صوتی و تبدیل به متن"""
        try:
            # ایجاد فایل موقت
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_ogg:
                # دانلود فایل صوتی
                await voice_file.download_to_drive(tmp_ogg.name)

                # تبدیل به WAV
                wav_path = self._convert_to_wav(tmp_ogg.name)

                # تبدیل صوت به متن
                text = self._speech_to_text(wav_path)

                # حذف فایل‌های موقت
                os.unlink(tmp_ogg.name)
                os.unlink(wav_path)

                return text

        except Exception as e:
            logger.error(f"خطا در پردازش پیام صوتی: {e}")
            return None

    def _convert_to_wav(self, ogg_path: str) -> str:
        """تبدیل فایل OGG به WAV"""
        try:
            # بارگذاری فایل صوتی
            audio = AudioSegment.from_ogg(ogg_path)

            # ایجاد مسیر فایل WAV
            wav_path = ogg_path.replace(".ogg", ".wav")

            # ذخیره به فرمت WAV
            audio.export(wav_path, format="wav")

            return wav_path

        except Exception as e:
            logger.error(f"خطا در تبدیل فایل صوتی: {e}")
            raise

    def _speech_to_text(self, wav_path: str) -> Optional[str]:
        """تبدیل فایل WAV به متن"""
        try:
            with sr.AudioFile(wav_path) as source:
                # خواندن فایل صوتی
                audio = self.recognizer.record(source)

                # تلاش برای تشخیص به فارسی با Google
                try:
                    text = self.recognizer.recognize_google(audio, language="fa-IR")
                    logger.info(f"متن تشخیص داده شده: {text}")
                    return text

                except sr.UnknownValueError:
                    logger.warning("نتوانستم صدا را تشخیص دهم")
                    return None

                except sr.RequestError as e:
                    logger.error(f"خطا در درخواست به Google: {e}")
                    return None

        except Exception as e:
            logger.error(f"خطا در تبدیل صوت به متن: {e}")
            return None

    def process_voice_text(self, text: str) -> str:
        """پردازش و بهبود متن تشخیص داده شده"""
        if not text:
            return ""

        # اصلاحات رایج در تشخیص گفتار فارسی
        corrections = {
            "توموم": "تومان",
            "تومون": "تومان",
            "تومن": "تومان",
            "هزارتومن": "هزار تومان",
            "میلیون تومن": "میلیون تومان",
            "حساب بانک": "حساب",
            "واریزی": "واریز",
            "برداشتی": "برداشت",
        }

        # اعمال اصلاحات
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)

        return text.strip()
