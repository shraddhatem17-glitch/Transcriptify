import enum
import json
from logger_util import get_logger

log = get_logger(__name__)


class ResultCode(enum.Enum):
    Ok = 1
    SystemInternalError = 2
    InvalidDataOrArgument = 3
    AuthenticationError = 4
    InvalidRequestFormat = 5
    AuthorizationError = 6
    StudyAlreadyPublished = 7
    UserAlreadyPresent = 8
    UserNotFound = 9
    TesterNotFound = 10
    InvalidAuthToken = 11
    AccountDeactivated = 12
    URLNotAccessible = 13
    FileExists = 14
    BusinessMailRequired = 15
    DuplicateOtp = 16
    OtpExpired = 17
    StimuliNotFound = 18
    MediaTypeNotSupported = 19
    EmailCouldNotSent = 20
    ProjectNotFound = 21
    InvalidQuestionType = 22
    QuestionNotFound = 23
    ProjectCouldNotPublished = 24
    SurveyLinkedToVideo = 25
    InvalidStimuliType = 26
    StudyIdMismatch = 27
    ProjectAlreadyCompleted = 28
    ValidationFailed = 29
    ParticipantEmotionNotFound = 30
    FileNotFound = 31
    ExceedingFileSizeLimit = 32
    TesterResponseAlreadyExists = 33
    ProjectIsNotPublished = 34
    ProjectIsCompleted = 35
    IncorrectOptionRecruitmentFail = 36
    RecordNotFound = 37
    PartOfNextQueLogic = 38
    TestingStatusNotFound = 39
    InvalidTesterStatusForAction = 40
    InvalidSurveyID = 41
    RecordAlreadyExists = 42
    CurrentlyUnableToProcess = 43
    MediaFileUseInStudy = 44
    CouldNotTestSimulatedEyeTrackingStudy = 45
    ExcelFileNotFound = 46
    InvalidFileType = 47
    MeetingNotFound = 48
    MeetingCompletedOrRunning = 49
    MeetingRunning = 50
    MaxLimitExceeded = 51
    InvalidMeetingParticipantToken = 52
    MeetingParticipantNotFound = 53
    ParticipantNotFound = 54
    MeetingIsOver = 55
    MeetingIsScheduledForFutureTime = 56
    SessionEnded = 56
    MeetingNotCompleted = 57
    ProjectQuestionsBeingUpdating = 58
    StimuliRunning = 59
    QuestionProcessing = 60
    DuplicateAnnotation = 61
    TopicDeletionFailed = 62
    MeetingElapsed = 63
    OperationNotAllowed = 64
    SubscriptionExpired = 65
    SubscriptionExpireThresholdBreach = 66
    TermAndConditionNotAccepted = 67


class ActionResult(object):
    def __init__(self, code: ResultCode = ResultCode.Ok, message: str = '', data=None, req_id: str = "",
                 http_res_status=None, obj=None):
        self.code: ResultCode = code
        self.message: str = message
        self.data: dict = data
        self._obj = obj
        self.req_id: str = req_id
        self.http_res_status = http_res_status

    def to_dic(self) -> dict:
        return {'code': str(self.code.name), 'message': self.message, "data": ""}

    def to_json(self) -> str:
        return json.dumps(self.to_dic())

    @staticmethod
    def get_internal_err_res():
        return ActionResult(ResultCode.SystemInternalError, 'System internal Error. Please try again.',
                            http_res_status=500)

    @staticmethod
    def get_ok_dic():
        return {'code': str(ResultCode.Ok.name), 'message': "", "data": ""}

    @property
    def obj(self):
        return self._obj
