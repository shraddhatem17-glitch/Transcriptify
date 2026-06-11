import os.path
import queue
import threading
import time
from typing import Optional

from logger_util import get_logger
from src import Job, JobStatus, app, with_app_context, db
from src.audio_extractor.deepgram import DeepgramAPI
from src.common_utils import convert_to_hh_mm_ss

work_q = queue.Queue()
processed_count = 0
last_min_processed_count = 0
# from_ts = 0
# to_ts = 0

log = get_logger(__name__, "processor.log")


class BackGroundThread(threading.Thread):

    def __init__(self, thread_function):
        threading.Thread.__init__(self)
        self.runnable = thread_function
        self.daemon = True

    def run(self):
        self.runnable()


def construct_text_transcript(raw_transcription):
    transcription = ''
    for channel in raw_transcription['results']['channels']:
        for alternative in channel['alternatives']:
            for para in alternative['paragraphs']['paragraphs']:
                if not int(para['start']) == -1:
                    sent_time = convert_to_hh_mm_ss(int(para['start']))
                else:
                    sent_time = int(para['start'])
                speaker = f"Speaker {para['speaker'] + 1}"
                transcript_line = ' '.join(sent['text'].strip() if sent['text'] else "" for sent in para['sentences'])
                transcription += f"{speaker}    {sent_time}    {transcript_line}\n"
    return transcription


@with_app_context
def check_n_process_job():
    try:
        job: Optional[Job] = None
        try:
            job: Job = Job.get_oldest_pending()
        except Exception as ex:
            log.exception(ex)
        if not job:
            return False
        log.info(f"Job Found for processing with job id: {job.id} and status changed to {JobStatus.Processing.value}.")
        if not os.path.exists(job.media_url):
            job.status = JobStatus.ProcessingError.value
            db.session.commit()
            log.error(f"Media file not found for job id: {job.id}.")
            return False
        log.info(f"Going to get transcription from deepgram for job id: {job.id}.")
        raw_transcript = DeepgramAPI().audio_transcription(job.media_url)
        if not raw_transcript:
            job.status = JobStatus.ProcessingError.value
            db.session.commit()
            log.error(f"Could not get transcription from deepgram for job id: {job.id}.")
            return False
        log.info(f"Got transcription from deepgram for job id: {job.id}.")
        text_transcript = construct_text_transcript(raw_transcript)
        transcript_save_path = job.media_url.split(".")[0] + ".txt"
        with open(transcript_save_path, "w", encoding="utf-8") as f:
            f.write(text_transcript)
        log.info(f"Transcription successfully generated and save for job id: {job.id}, on path: {transcript_save_path}")
        job.status = JobStatus.Completed.value
        db.session.commit()
        return True
    except Exception as ex:
        log.exception(f"Got Exception in check_n_process_job - ex: {ex}")
        return False


def process_job_loop():
    while True:
        try:
            if check_n_process_job():
                continue
            time.sleep(10)
        except Exception as ex:
            log.exception(ex)


if __name__ == '__main__':
    log.info("Starting processor as main!!!")
    workers = []

    for i in range(2):
        vid_bg = BackGroundThread(process_job_loop)
        vid_bg.start()
        workers.append(vid_bg)

    for worker in workers:
        worker.join()
