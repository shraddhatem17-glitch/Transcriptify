import enum
import os
import shutil
import subprocess
import threading
import time
import uuid
from functools import wraps
import base64
import requests
import settings
from logger_util import get_logger
from src import bcrypt
import zipfile

lock = threading.Lock()

log = get_logger(__name__)


class VmProUserDeleteType(enum.Enum):
    SoftDelete = "softDelete"
    UndoSoftDelete = "undoSoftDelete"
    HardDelete = 'hardDelete'


class BackGroundThread(threading.Thread):

    def __init__(self, thread_function):
        threading.Thread.__init__(self)
        self.runnable = thread_function
        self.daemon = True

    def run(self):
        self.runnable()


def get_media_to_thumbnail_file_name(media_file_name: str):
    return media_file_name.replace('.', '_') + ".png"


def get_password(length: int = 20, include_spacial_char: bool = True):
    import secrets
    import string
    """password with at least one lowercase character, at least one uppercase character,
     and at least three digits"""

    alphabet = string.ascii_letters + string.digits
    if include_spacial_char:
        alphabet += "!#$%&*+-/<=>?@[]^_{|}~"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password


def execute_in_lock(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        result = None
        lock.acquire()
        try:
            result = func(*args, **kwargs)
        except Exception as ex:
            log.exception(ex)
        lock.release()
        return result

    return decorated_function


def div(p, q):
    return p / q if q else 0


def floor_div(p, q):
    return p // q if q else 0


def get_uid():
    return str(uuid.uuid4()).replace('-', '')


def convert_to_hh_mm_ss(seconds: int, hh_included: bool = True) -> str:
    def get_formatted_value(v: int):
        return f'{v}' if v > 9 else f'0{v}'

    reminder: int
    reminder = seconds
    result: str = ""
    if hh_included:
        result = f'{get_formatted_value(int(reminder / 3600))}:'
        reminder = reminder % 3600

    result += f'{get_formatted_value(int(reminder / 60))}:'
    result += f'{get_formatted_value(reminder % 60)}'
    return result


def convert_hh_mm_ss_to_sec(hh_mm_ss: str):
    split_t = hh_mm_ss.split(":")
    hr = int(split_t[0])
    my_min = int(split_t[1])
    sec = int(split_t[2])
    my_time = hr * 3600 + my_min * 60 + sec
    return my_time


def convert_seconds_to_hours_and_minutes(seconds):
    if seconds == 0:
        return "0 secs"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    if hours > 0:
        return f"{hours} hrs {minutes} mins."
    elif minutes > 0:
        return f"{minutes} mins."
    else:
        return f"{remaining_seconds} secs."


def convert_elapsed_time_to_hh_mm_ss_ms(elapsed_time):
    try:
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        result = "{:02}:{:02}:{:02}.{:03}".format(int(hours), int(minutes), int(seconds), milliseconds)
        return result
    except Exception as e:
        log.info(e)
        return elapsed_time


def formate_running_ts(start_ts: float):
    return convert_to_hh_mm_ss(round(time.time() - start_ts))


def get_video_duration(video_file_path: str) -> (int, bool):
    try:
        log.info(f'trying to get duration of {video_file_path}')
        result: subprocess.CompletedProcess = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                                              "format=duration", "-of",
                                                              "default=noprint_wrappers=1:nokey=1", video_file_path],
                                                             stdout=subprocess.PIPE,
                                                             stderr=subprocess.STDOUT)

        if result.returncode != 0 or result.stdout.decode('utf-8').strip() == "N/A":
            log.error(f'Could not get video duration for file: {video_file_path}. ex: \n{result.stderr}')
            return 0, False
        # output is in seconds
        return round(float(result.stdout)), True
    except Exception as ex:
        log.exception(ex)
        return 0, False


def get_hashed_password(password: str) -> str:
    from main import app
    p = bcrypt.generate_password_hash(password, app.config.get('BCRYPT_LOG_ROUNDS')).decode()
    if isinstance(p, str):
        return p
    return p.decode('utf-8')


def is_valid_media(ext: str):
    return ext.lower() in settings.SUPPORTED_MEDIA_TYPE


def extract_thumbnail(vid_file_path, img_dir_path, thumbnail_quality=1, logger=log, req_id: str = ""):
    try:
        st = time.time()
        logger.info(f'going to extract thumbnail of video {vid_file_path} {req_id}')
        os.makedirs(img_dir_path, exist_ok=True)
        frame_gap_sec = 1
        frame_rate = 1000 / (frame_gap_sec * 1000)
        cmd = [
            "ffmpeg", "-y", "-i", vid_file_path,
            "-r", str(frame_rate),
            "-vf", f"scale=320:200",
            "-q:v", str(thumbnail_quality),
            f"{img_dir_path}/%d.jpg"
        ]
        time_out_sec = 30 * 60

        response: subprocess.CompletedProcess = subprocess.run(cmd, capture_output=True, timeout=time_out_sec)
        if response.returncode != 0:
            logger.error(f'Could not extract thumbnail in {formate_running_ts(st)} of video {vid_file_path} '
                         f'\n{response.stderr} \n{response.stdout} {req_id}')
            return False
        logger.info(f'Extract thumbnail in {formate_running_ts(st)} of video {vid_file_path} {req_id}')
        return True
    except Exception as ex:
        logger.exception(f'{ex} {req_id}')
        return False


def get_video_bit_rate(video_path, in_kbps=True):
    try:
        cmd: str = f"ffprobe -v quiet -select_streams v:0 -show_entries " \
                   f"stream=bit_rate -of default=noprint_wrappers=1:nokey=1 {video_path}"
        result = subprocess.check_output(cmd.split()).decode('utf-8').strip()
        result = eval(result)
        if in_kbps:
            result = round(result / 1000)
        log.info(f'bit rate: {result} for {video_path}')
        return result
    except Exception as ex:
        log.exception(ex)
        return None


def compress_video(vid_file_path, max_bit_rate=1300, logger=log, req_id: str = ''):
    try:
        if get_video_bit_rate(vid_file_path) < max_bit_rate:
            return True
        st = time.time()
        out_file: str = os.path.join('temp', f'{get_uid()}.{vid_file_path.split(".")[-1]}')
        cmd = f'ffmpeg -i {vid_file_path} -vcodec libx264 -crf 28  -maxrate {max_bit_rate}K -bufsize 2M {out_file}'
        vid_duration, _ = get_video_duration(vid_file_path)
        # time_out_sec = 30 * 60 # min * sec
        time_out_sec = vid_duration * 3
        logger.info(f'going to compress video {vid_file_path} video duration: {vid_duration} {req_id}\n {cmd}')
        response: subprocess.CompletedProcess = subprocess.run(cmd.split(), capture_output=True, timeout=time_out_sec)
        if response.returncode != 0:
            logger.error(f'Could not compress video in {formate_running_ts(st)} of cmd {cmd} '
                         f'\n{response.stderr} \n{response.stdout}')
            return False
        shutil.move(out_file, vid_file_path)
        logger.info(f'video compression complete in {formate_running_ts(st)} for '
                    f'video duration: {convert_to_hh_mm_ss(vid_duration)} of video {vid_file_path} {req_id}')
        return True
    except Exception as ex:
        logger.exception(ex)
        return False


def convert_bytes_to_mb(bytes_size: int, round_offset=0):
    mb = bytes_size / 1048576  # 1048576 = 1024 * 1024
    return round(mb, round_offset) if round_offset > 0 else mb


def allowed_video_extension(file_ext: str):
    return file_ext.lower() in settings.VIDEO_MEDIA_TYPE


def is_video_file(file_path: str):
    ext: str = file_path.split('.')[-1]
    return allowed_video_extension(ext)


def save_base64_jpg_image(img_name_path, base64str: str):
    try:
        # encode str into bytes
        base64str = base64str[23:]
        encode_img = str.encode(base64str)
        imgdata = base64.b64decode(encode_img)
        with open(img_name_path, 'wb') as f:
            f.write(imgdata)
        return True
    except Exception as ex:
        log.exception(ex)
        return False


def convert_inch_to_meter(inch) -> float:
    return inch * 0.0254


def download_file(url: str, output_file: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        with open(output_file, "wb") as handle:
            for data in response.iter_content():
                handle.write(data)
        return True
    except Exception as ex:
        log.exception(f"couldn't download url: {url}\n {ex}")
        return False


class MediaFileType(enum.Enum):
    Stimuli = "sti"
    LogoImg = "logo"
    Transcription = "trans"


def get_media_file_name(org_id: int, user_id: int, file_type: MediaFileType, file_ext: str):
    return f"org_{org_id}_usr_{user_id}_{file_type.value}_{get_uid()}.{file_ext}"


def unzip_file(zip_filename, extract_to, req_id: str = '', logger=log):
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info(f"File '{zip_filename}' successfully unzipped to '{extract_to}' {req_id}")
        return True
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return False


def get_size(path, logger=log):
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            return sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(path)
                for filename in filenames)
        else:
            return 0
    except Exception as e:
        logger.exception(f"An error occurred while getting file size: {e}")
        return 0


def safe_remove_directory(directory, log_obj=log, retry=5):
    try:
        if retry == 0:
            return False
        shutil.rmtree(directory)
        log_obj.info(f"Directory '{directory}' removed successfully.")
        return True
    except OSError as e:
        if e.errno == 39:
            log_obj.info(f"Directory '{directory}' not empty. Cleaning up.")
            time.sleep(3)
            return safe_remove_directory(directory, log_obj, retry - 1)
        else:
            log_obj.info(f"Error removing directory '{directory}': {e}")
        return False
    except Exception as ex:
        log_obj.info(f"Error removing directory '{directory}': {ex}")
        return False


def zip_folders_or_files(folder_paths, zip_filename, req_id: str = '', logger=log, retry=5):
    try:
        st = time.time()
        logger.info(f'Going to zip {len(folder_paths)} items. {req_id}')
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in folder_paths:
                if not os.path.exists(path):
                    continue
                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, os.path.dirname(path))
                            zipf.write(file_path, rel_path)
                            logger.info(f"Added file {file_path} as {rel_path} to the zip file.")
                else:
                    a_name = os.path.basename(path)
                    zipf.write(path, a_name)
                    logger.info(f"Added file {path} as {a_name} to the zip file.")
        is_valid_zip = validate_zip_file(zip_filename)
        if not is_valid_zip:
            os.remove(zip_filename)
            if retry > 0:
                logger.info(f"Retrying to create zip: {zip_filename} retry left: {retry - 1}")
                return zip_folders_or_files(folder_paths, zip_filename, req_id, logger, retry - 1)
            else:
                return False
        logger.info(f"Items zipped successfully as '{zip_filename}' in {formate_running_ts(st)} {req_id}")
        return True
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return False


def validate_zip_file(file_path: str, logger=log) -> bool:
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.testzip()
        return True
    except Exception as e:
        logger.error(f"Error validating the ZIP file at {file_path}: {e}")
        return False


def mask_email(email):
    local_part, domain = email.split('@', 1)
    if len(local_part) > 5:
        masked_local = local_part[:3] + '*' * (len(local_part) - 5) + local_part[-2:]
    else:
        masked_local = local_part[0] + '*' * (len(local_part) - 1)
    return f"{masked_local}@{domain}"


def get_job_file_name(user_id: int, ext: str):
    return f"{user_id}_{get_uid()}.{ext}"


