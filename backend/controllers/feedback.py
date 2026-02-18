"""Controller for feedback operations."""

from typing import Optional
import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Header,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth import AuthService
from services.feedback import FeedbackService

from models.database.auth import User, PublicUser
from models.requests.feedback import FeedbackCreateRequest, FeedbackUpdateRequest
from models.response.feedback import FeedbackResponse, FeedbackStatsResponse
from models.internal import FeedbackFromEnum
from controllers.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_user_type(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> tuple[Optional[User], Optional[PublicUser]]:
    """
    Determine user type based on provided authentication.

    Returns:
        Tuple of (auth_user, public_user) where one will be None
    """
    print("Authorization header:", authorization)
    print("Token header:", token)
    auth_service = AuthService(db)

    # Check for authority user (Bearer token in Authorization header)
    if authorization and authorization.startswith("Bearer "):
        try:
            bearer_token = authorization.replace("Bearer ", "")
            auth_user = await auth_service.get_current_user_from_token(bearer_token)
            if auth_user and auth_user.is_active:
                print("Authenticated authority user:", auth_user)
                return (auth_user, None)
        except Exception:  # pylint: disable=broad-except
            logger.debug("Failed to authenticate authority user")

    # Check for public user (token header)
    if token:
        try:
            public_user = await auth_service.get_public_user_by_token(token)
            if public_user:
                return (None, public_user)
        except Exception:  # pylint: disable=broad-except
            logger.debug("Failed to authenticate public user")

    return (None, None)


@router.get("/my", response_model=FeedbackResponse)
async def get_my_feedback(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
) -> FeedbackResponse:
    """
    Get the authenticated user's own feedback.

    This endpoint works for both:
    - Authority users: Provide Authorization header with Bearer token
    - Public users: Provide token header with public user token
    """
    auth_user, public_user = await get_user_type(authorization, token, db)

    if not auth_user and not public_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Authorization header (for authority users) or token header (for public users)",
        )

    feedback_service = FeedbackService(db)

    try:
        feedback = await feedback_service.get_user_own_feedback(
            auth_user_id=auth_user.id if auth_user else None,
            public_user_id=public_user.id if public_user else None,
        )

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback found for this user",
            )

        return FeedbackResponse(
            id=feedback.id,
            auth_user_id=feedback.auth_user_id,
            public_user_id=feedback.public_user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching user feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback",
        ) from e


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_request: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
) -> FeedbackResponse:
    """
    Create new feedback.

    This endpoint works for both:
    - Authority users: Provide Authorization header with Bearer token
    - Public users: Provide token header with public user token
    """
    auth_user, public_user = await get_user_type(authorization, token, db)

    if not auth_user and not public_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Authorization header (for authority users) or token header (for public users)",
        )

    feedback_service = FeedbackService(db)

    try:
        feedback = await feedback_service.save_feedback(
            auth_user_id=auth_user.id if auth_user else None,
            public_user_id=public_user.id if public_user else None,
            rating=feedback_request.rating,
            comment=feedback_request.comment,
        )

        return FeedbackResponse(
            id=feedback.id,
            auth_user_id=feedback.auth_user_id,
            public_user_id=feedback.public_user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/", response_model=list[FeedbackResponse])
async def get_all_feedback(
    feedback_source: Optional[FeedbackFromEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[FeedbackResponse]:
    """
    Get all feedback (authority users only).

    Parameters:
    - feedback_source: Filter by feedback source (AUTH_USER or PUBLIC_USER)
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (max 1000)
    """
    assert current_user.is_active, "Inactive user cannot access feedback"
    feedback_service = FeedbackService(db)

    try:
        feedback_list = await feedback_service.get_all_feedback(
            feedback_source=feedback_source,
            skip=skip,
            limit=limit,
        )

        return [
            FeedbackResponse(
                id=fb.id,
                auth_user_id=fb.auth_user_id,
                public_user_id=fb.public_user_id,
                rating=fb.rating,
                comment=fb.comment,
            )
            for fb in feedback_list
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback",
        ) from e


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback_by_id(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FeedbackResponse:
    """
    Get feedback by ID (authority users only).
    """
    assert current_user.is_active, "Inactive user cannot access feedback"
    feedback_service = FeedbackService(db)

    feedback = await feedback_service.get_feedback_by_id(feedback_id)

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    return FeedbackResponse(
        id=feedback.id,
        auth_user_id=feedback.auth_user_id,
        public_user_id=feedback.public_user_id,
        rating=feedback.rating,
        comment=feedback.comment,
    )


@router.get("/stats/summary", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FeedbackStatsResponse:
    """
    Get feedback statistics (authority users only).

    Returns total feedback count and average ratings by user type.
    """
    assert current_user.is_active, "Inactive user cannot access feedback"
    feedback_service = FeedbackService(db)

    try:
        stats = await feedback_service.count_stats()
        return stats
    except Exception as e:
        logger.error("Error fetching feedback stats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback statistics",
        ) from e


@router.put("/my", response_model=FeedbackResponse)
async def update_my_feedback(
    feedback_request: FeedbackUpdateRequest,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
) -> FeedbackResponse:
    """
    Update the authenticated user's own feedback.

    This endpoint works for both:
    - Authority users: Provide Authorization header with Bearer token
    - Public users: Provide token header with public user token
    """
    auth_user, public_user = await get_user_type(authorization, token, db)

    if not auth_user and not public_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Authorization header (for authority users) or token header (for public users)",
        )

    feedback_service = FeedbackService(db)

    try:
        feedback = await feedback_service.update_user_feedback(
            auth_user_id=auth_user.id if auth_user else None,
            public_user_id=public_user.id if public_user else None,
            rating=feedback_request.rating,
            comment=feedback_request.comment,
        )

        return FeedbackResponse(
            id=feedback.id,
            auth_user_id=feedback.auth_user_id,
            public_user_id=feedback.public_user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error updating user feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback",
        ) from e
