import enum
import time
import requests
import settings
from logger_util import get_logger
from src.common_utils import formate_running_ts

log = get_logger(__name__)


class TranscriptLanguage(enum.Enum):
    English = 'en'
    Hindi = 'hi'


class DeepgramAPI(object):
    def __init__(self, lang_code=TranscriptLanguage.English.value,
                 auth_token: str = settings.DEEPGRAM_TOKEN):
        self.auth_token = auth_token
        self.lang_code = lang_code
        self.headers = {'Authorization': f'Token {self.auth_token}', 'Content-Type': 'audio/mp3'}
        self.url = f"https://api.deepgram.com/v1/listen?language={self.lang_code}&model=nova-2&smart_format=" \
                   f"true&punctuate=true&paragraphs=true&utterances=true&diarize=true&summarize=false&detect_topics=" \
                   f"false&filler_words=false"

    def audio_transcription(self, audio_file_path, retry=5, binary_data=None, req_id="", logger=log, fail_count=0,
                            error_str=""):
        try:
            if not binary_data:
                with open(audio_file_path, 'rb') as file:
                    binary_data = file.read()
            st = time.time()
            response = requests.post(self.url, headers=self.headers, data=binary_data)
            if response.status_code == 200:
                transcript_json = response.json()
                logger.info(f"Got transcription for {audio_file_path}, {req_id} in {formate_running_ts(st)}, in retry"
                            f" left {retry}")
                return transcript_json
            elif (response.status_code == 408 or response.status_code == 504) and retry > 0:  # 408 for slow upload
                # and 504 for gateway time out error
                error = f"Could not get transcription from deep gram due to status code: {response.status_code} " \
                        f"and reason: {response.text}, going to retry retry left = {retry - 1}, {req_id}, " \
                        f"in {formate_running_ts(st)}"
                logger.info(error)
                error_str += f"{error}\n\n"
                time.sleep(30)
                return self.audio_transcription(audio_file_path, retry=retry - 1, binary_data=binary_data,
                                                fail_count=fail_count+1, req_id=req_id, error_str=error_str)
            else:
                logger.error(f"Failed to transcribe audio. Status code: {response.status_code}. Response:"
                             f" {response.text}, {req_id}, in {formate_running_ts(st)}, all previous errors: "
                             f"{error_str}")
                return None
        except Exception as ex:
            logger.exception(f"Exception occurred during transcription: {ex}, {req_id}")
            return None
