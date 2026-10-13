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
from models.database.event import Event, EventMedia, EventBookmark, VdoEventImage
from models.database.contractor import Agency, Contractor
from models.database.scheme import Scheme, SchemeMedia, SchemeBookmark
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
from models.database.notice import Notice, NoticeMedia, NoticeType, NoticeReply
from models.database.survey_master import (
    FundHead,
    CollectionFrequency,
    CleaningFrequency,
    WorkFrequency,
    AnnualSurvey,
    DoorToDoorCollectionDetails,
    RoadSweepingDetails,
    DrainCleaningDetails,
    CSCDetails,
    ODFSustainability,
    SWMAssetsCategory,
    LWMAssets,
    PWMUDetails,
    FSMDetails,
    GobardhanProject,
    D2DActivities,
    BartanBank,
    VehicleAssets,
    FundSanctioned,
    WorkOrderDetails,
)
from models.database.gps import GPSTracking, Vehicle, GPSRecord
from models.database.feedback import Feedback
from models.database.volunteer import VolunteerRegistration
from models.database.circular import Circular

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
    "EventBookmark",
    "VdoEventImage",
    # Contractor models
    "Agency",
    "Contractor",
    # FCM device models
    "UserDeviceToken",
    "PublicUserDeviceToken",
    # Scheme models
    "Scheme",
    "SchemeMedia",
    "SchemeBookmark",
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
    "NoticeType",
    "NoticeReply",
    # Survey Master models
    "FundHead",
    "CollectionFrequency",
    "CleaningFrequency",
    "WorkFrequency",
    "AnnualSurvey",
    "DoorToDoorCollectionDetails",
    "RoadSweepingDetails",
    "DrainCleaningDetails",
    "CSCDetails",
    "ODFSustainability",
    "SWMAssetsCategory",
    "LWMAssets",
    "PWMUDetails",
    "FSMDetails",
    "GobardhanProject",
    "D2DActivities",
    "BartanBank",
    "VehicleAssets",
    "FundSanctioned",
    "WorkOrderDetails",
    # GPS Tracking model
    "GPSTracking",
    "GPSRecord",
    "Vehicle",
    # Feedback model
    "Feedback",
    # Volunteer model
    "VolunteerRegistration",
    # Circular model
    "Circular",
]

