import datetime
import enum
from logger_util import get_logger
from src import db

log = get_logger(__name__)


class FountSize(enum.Enum):
    Small = "Small"
    Medium = "Medium"
    Large = "Large"


class JobStatus(enum.Enum):
    NotStarted = "NotStarted"
    Processing = "Processing"
    Completed = "Completed"
    ProcessingError = "ProcessingError"


class JobType(enum.Enum):
    Audio = "Audio"
    Video = "Video"


class Job(db.Model):
    """ Job Model for storing uploaded audio/video file jobs """
    __tablename__ = "jobs"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    job_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default=JobStatus.NotStarted.value)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    media_url = db.Column(db.String(555), nullable=True)

    def __init__(self, title, file_name, job_type, user_id=None, media_url=None, status=JobStatus.NotStarted.value):
        self.title = title
        self.file_name = file_name
        self.job_type = job_type
        self.user_id = user_id
        self.media_url = media_url
        self.status = status
        self.created_on = datetime.datetime.now()
        self.updated_on = datetime.datetime.now()

    @staticmethod
    def get_jobs_by_user_id(user_id: int):
        return Job.query.filter_by(user_id=user_id).order_by(Job.created_on.desc()).all()

    @staticmethod
    def get_oldest_pending():
        try:
            job: Job = Job.query.filter(Job.status == JobStatus.NotStarted.value).order_by(Job.created_on.asc()).first()
            if job:
                job.status = JobStatus.Processing.value
                db.session.commit()
            return job
        except Exception as ex:
            db.session.rollback()
            log.exception(f"Got exception whole getting job: {ex}")
            return None

    @staticmethod
    def get_job_by_id(job_id: int):
        return Job.query.filter_by(id=job_id).first()
