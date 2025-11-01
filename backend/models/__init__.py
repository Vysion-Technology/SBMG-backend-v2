"""
Models package initialization.
Import all models here to ensure they are registered with SQLAlchemy.
"""

# Import all database models to register them with SQLAlchemy Base
from models.database.auth import (
    Role,
    User,
    PositionHolder,
    PublicUser,
    PublicUserToken,
    PublicUserOTP,
)
from models.database.attendance import DailyAttendance
from models.database.geography import District, Block, GramPanchayat
from models.database.complaint import (
    ComplaintType,
    ComplaintTypeGeographicalIneligibility,
    ComplaintStatus,
    Complaint,
    ComplaintAssignment,
    ComplaintMedia,
    ComplaintComment,
)
from models.database.fcm_device import UserDeviceToken, PublicUserDeviceToken
from models.database.event import Event, EventMedia
from models.database.contractor import Agency, Contractor
from models.database.scheme import Scheme, SchemeMedia
from models.database.survey import (
    Form,
    Question,
    AnswerType,
    QuestionOption,
    ResponseReviewStatus,
    Response,
    FormAssignment,
)
from models.database.inspection import (
    Inspection,
    InspectionImage,
    HouseHoldWasteCollectionAndDisposalInspectionItem,
    RoadAndDrainCleaningInspectionItem,
    CommunitySanitationInspectionItem,
    OtherInspectionItem,
)
from models.database.notice import Notice, NoticeMedia
from models.database.survey_master import (
    FundHead,
    CollectionFrequency,
    CleaningFrequency,
    AnnualSurvey,
    DoorToDoorCollectionDetails,
    RoadSweepingDetails,
    DrainCleaningDetails,
    CSCDetails,
    SWMAssets,
    FundSanctioned,
    WorkOrderDetails,
)
from models.database.gps import GPSTracking
from models.database.feedback import Feedback
__all__ = [
    # Auth models
    "DailyAttendance",
    "Role",
    "User",
    "PositionHolder",
    "PublicUser",
    "PublicUserToken",
    "PublicUserOTP",
    # Geography models
    "District",
    "Block",
    "GramPanchayat",
    # Complaint models
    "ComplaintType",
    "ComplaintTypeGeographicalIneligibility",
    "ComplaintStatus",
    "Complaint",
    "ComplaintAssignment",
    "ComplaintMedia",
    "ComplaintComment",
    # Event models
    "Event",
    "EventMedia",
    # Contractor models
    "Agency",
    "Contractor",
    # FCM device models
    "UserDeviceToken",
    "PublicUserDeviceToken",
    # Scheme models
    "Scheme",
    "SchemeMedia",
    # Survey models
    "Form",
    "Question",
    "AnswerType",
    "QuestionOption",
    "ResponseReviewStatus",
    "Response",
    "FormAssignment",
    # Inspection models
    "Inspection",
    "InspectionImage",
    "HouseHoldWasteCollectionAndDisposalInspectionItem",
    "RoadAndDrainCleaningInspectionItem",
    "CommunitySanitationInspectionItem",
    "OtherInspectionItem",
    # Notice models
    "Notice",
    "NoticeMedia",
    # Survey Master models
    "FundHead",
    "CollectionFrequency",
    "CleaningFrequency",
    "AnnualSurvey",
    "DoorToDoorCollectionDetails",
    "RoadSweepingDetails",
    "DrainCleaningDetails",
    "CSCDetails",
    "SWMAssets",
    "FundSanctioned",
    "WorkOrderDetails",
    # GPS Tracking model
    "GPSTracking",
    # Feedback model
    "Feedback",
]
