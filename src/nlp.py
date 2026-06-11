from google.genai import types
import settings
from logger_util import get_logger
from google import genai


log = get_logger(__name__)


client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Define system prompt
system_prompt = (
    "Analyze transcript and provide a very detailed answer on data and restrict your "
    "response to the factual information provided in the transcripts only. Do not access or "
    "reference any external knowledge sources and Assume you have no knowledge beyond the "
    "content in the transcripts. Answer questions solely based on the information provided only."
)


def query_transcription(transcription: str, question="For the below transcription given, give a very detailed summary.",
                        req_id: str = ""):
    try:
        prompt = f"Question: \n\n{question}\n\nTranscription:\n\n{transcription}"
        # Call Gemini 1.5 Flash (free tier friendly)
        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt,
                                                  config=types.GenerateContentConfig(max_output_tokens=20000,
                                                                                     temperature=0.9,
                                                                                     system_instruction=system_prompt))
        return response.text
    except Exception as ex:
        log.exception(f"Exception occurred during getting summary for request id: {ex}, {req_id}.")
        return None

