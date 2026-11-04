"""Service for managing in-app notifications."""

import logging
from typing import List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, insert, update
from sqlalchemy.orm import selectinload

from models.database.auth import User, PublicUser, PositionHolder, Role
from models.database.notification import InAppNotification, InAppNotificationRead
from models.database.notice import Notice
from models.database.complaint import Complaint
from models.database.event import Event
from models.database.scheme import Scheme
from models.database.geography import GramPanchayat, Block, District
from models.response.notification import InAppNotificationItem

logger = logging.getLogger(__name__)


class InAppNotificationService:
    """Service to create, query, and manage in-app notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_direct_notification(
        self,
        title: str,
        message: str,
        category: str,
        priority: str = "MEDIUM",
        user_id: Optional[int] = None,
        public_user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action_url: Optional[str] = None,
    ) -> InAppNotification:
        """Create a notification targeted directly to a specific user."""
        notification = InAppNotification(
            user_id=user_id,
            public_user_id=public_user_id,
            is_broadcast=False,
            target_audience=None,
            title=title,
            message=message,
            category=category,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            is_read=False,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def create_broadcast_notification(
        self,
        title: str,
        message: str,
        category: str,
        priority: str = "MEDIUM",
        target_audience: str = "ALL",  # "ALL", "STAFF", "PUBLIC"
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action_url: Optional[str] = None,
    ) -> InAppNotification:
        """Create a broadcast notification visible to all users or an audience group."""
        notification = InAppNotification(
            user_id=None,
            public_user_id=None,
            is_broadcast=True,
            target_audience=target_audience,
            title=title,
            message=message,
            category=category,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            is_read=False,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    # -------------------------------------------------------------------------
    # 1. NOTICE NOTIFICATIONS
    # -------------------------------------------------------------------------
    async def notify_notice_received(
        self,
        notice: Notice,
        receiver_user_id: int,
        sender_name: str,
        sender_role: str,
    ) -> Optional[InAppNotification]:
        """Notify the person who received the notice."""
        try:
            return await self.create_direct_notification(
                user_id=receiver_user_id,
                title=f"New Official Notice: {notice.title}",
                message=(
                    f"You have received an official notice from {sender_name} ({sender_role}). "
                    f"Please review and submit your reply."
                ),
                category="NOTICE",
                priority="HIGH",
                entity_type="notice",
                entity_id=notice.id,
                action_url=f"/notices/received/{notice.id}",
            )
        except Exception as e:
            logger.error(f"Error creating notice received notification: {e}")
            return None

    async def notify_notice_reply_received(
        self,
        notice: Notice,
        sender_user_id: int,
        replier_name: str,
        replier_role: str,
    ) -> Optional[InAppNotification]:
        """Notify the person who originally gave the notice that a reply was submitted."""
        try:
            return await self.create_direct_notification(
                user_id=sender_user_id,
                title=f"Reply Received on Notice #{notice.id}",
                message=(
                    f"{replier_name} ({replier_role}) has submitted a response to notice: '{notice.title}'."
                ),
                category="NOTICE_REPLY",
                priority="MEDIUM",
                entity_type="notice",
                entity_id=notice.id,
                action_url=f"/notices/sent/{notice.id}",
            )
        except Exception as e:
            logger.error(f"Error creating notice reply notification: {e}")
            return None

    # -------------------------------------------------------------------------
    # 2. SLA BREACH NOTIFICATIONS
    # -------------------------------------------------------------------------
    async def notify_sla_breach(
        self,
        complaint: Complaint,
        breach_level: str,
        days_elapsed: int,
    ) -> List[InAppNotification]:
        """
        Trigger hierarchical notifications when a complaint breaches SLA:
        - GP Level (>7 days): Notify VDO of the Gram Panchayat
        - BLOCK Level (>15 days): Notify BDO of the Block
        - DISTRICT Level (>30 days): Notify CEO of the District
        """
        notifications: List[InAppNotification] = []
        try:
            if breach_level == "GP":
                # Find VDO for complaint.gp_id
                vdo_query = (
                    select(User.id)
                    .join(PositionHolder, User.id == PositionHolder.user_id)
                    .join(Role, PositionHolder.role_id == Role.id)
                    .where(
                        and_(
                            Role.name == "VDO",
                            PositionHolder.gp_id == complaint.gp_id,
                            PositionHolder.end_date.is_(None),
                            User.is_active.is_(True),
                        )
                    )
                )
                vdo_res = await self.db.execute(vdo_query)
                vdo_user_ids = vdo_res.scalars().all()

                for uid in vdo_user_ids:
                    notif = await self.create_direct_notification(
                        user_id=uid,
                        title=f"SLA Warning: Complaint #{complaint.id} Unresolved (7+ Days)",
                        message=(
                            f"Complaint #{complaint.id} has remained unresolved for {days_elapsed} days. "
                            f"Please take prompt action before it escalates to Block level."
                        ),
                        category="SLA",
                        priority="WARNING",
                        entity_type="complaint",
                        entity_id=complaint.id,
                        action_url=f"/complaints/{complaint.id}",
                    )
                    notifications.append(notif)

            elif breach_level == "BLOCK":
                # Find BDO for complaint.block_id
                bdo_query = (
                    select(User.id)
                    .join(PositionHolder, User.id == PositionHolder.user_id)
                    .join(Role, PositionHolder.role_id == Role.id)
                    .where(
                        and_(
                            Role.name == "BDO",
                            PositionHolder.block_id == complaint.block_id,
                            PositionHolder.end_date.is_(None),
                            User.is_active.is_(True),
                        )
                    )
                )
                bdo_res = await self.db.execute(bdo_query)
                bdo_user_ids = bdo_res.scalars().all()

                for uid in bdo_user_ids:
                    notif = await self.create_direct_notification(
                        user_id=uid,
                        title=f"SLA Escalation: Complaint #{complaint.id} Escalated (15+ Days)",
                        message=(
                            f"Complaint #{complaint.id} in your block has been unresolved for {days_elapsed} days. "
                            f"Block intervention is required."
                        ),
                        category="SLA",
                        priority="CRITICAL",
                        entity_type="complaint",
                        entity_id=complaint.id,
                        action_url=f"/complaints/{complaint.id}",
                    )
                    notifications.append(notif)

            elif breach_level == "DISTRICT":
                # Find CEO for complaint.district_id
                ceo_query = (
                    select(User.id)
                    .join(PositionHolder, User.id == PositionHolder.user_id)
                    .join(Role, PositionHolder.role_id == Role.id)
                    .where(
                        and_(
                            Role.name == "CEO",
                            PositionHolder.district_id == complaint.district_id,
                            PositionHolder.end_date.is_(None),
                            User.is_active.is_(True),
                        )
                    )
                )
                ceo_res = await self.db.execute(ceo_query)
                ceo_user_ids = ceo_res.scalars().all()

                for uid in ceo_user_ids:
                    notif = await self.create_direct_notification(
                        user_id=uid,
                        title=f"Severe SLA Breach: Complaint #{complaint.id} (30+ Days)",
                        message=(
                            f"Complaint #{complaint.id} has remained unresolved for {days_elapsed} days. "
                            f"Escalated to District leadership."
                        ),
                        category="SLA",
                        priority="CRITICAL",
                        entity_type="complaint",
                        entity_id=complaint.id,
                        action_url=f"/complaints/{complaint.id}",
                    )
                    notifications.append(notif)

        except Exception as e:
            logger.error(f"Error dispatching SLA breach notification: {e}")

        return notifications

    # -------------------------------------------------------------------------
    # 3. EVENT START & EXPIRE NOTIFICATIONS (BROADCAST TO ALL)
    # -------------------------------------------------------------------------
    async def check_and_trigger_event_notifications(self) -> int:
        """
        Checks active events and triggers:
        1. Event Start: when event is currently ongoing (start_time <= now <= end_time)
        2. Event Expire: when event is nearing conclusion (now <= end_time <= now + 24 hours)
        """
        now = datetime.now(tz=timezone.utc)
        triggered_count = 0

        try:
            # Query active events
            events_result = await self.db.execute(select(Event).where(Event.active.is_(True)))
            events = events_result.scalars().all()

            for event in events:
                start_time = event.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

                end_time = event.end_time
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                # 1. Event Start Notification
                if start_time <= now <= end_time:
                    existing_start = await self.db.execute(
                        select(InAppNotification.id).where(
                            and_(
                                InAppNotification.is_broadcast.is_(True),
                                InAppNotification.category == "EVENT_START",
                                InAppNotification.entity_id == event.id,
                            )
                        )
                    )
                    if not existing_start.scalar_one_or_none():
                        await self.create_broadcast_notification(
                            title=f"Event Started: {event.name}",
                            message=(
                                f"The event '{event.name}' is now active! "
                                f"Scheduled from {start_time.strftime('%d %b %Y')} to {end_time.strftime('%d %b %Y')}."
                            ),
                            category="EVENT_START",
                            priority="MEDIUM",
                            target_audience="ALL",
                            entity_type="event",
                            entity_id=event.id,
                            action_url=f"/events/{event.id}",
                        )
                        triggered_count += 1

                # 2. Event Expire (24 hours before end_time)
                if now <= end_time <= now + timedelta(hours=24):
                    existing_expire = await self.db.execute(
                        select(InAppNotification.id).where(
                            and_(
                                InAppNotification.is_broadcast.is_(True),
                                InAppNotification.category == "EVENT_EXPIRE",
                                InAppNotification.entity_id == event.id,
                            )
                        )
                    )
                    if not existing_expire.scalar_one_or_none():
                        await self.create_broadcast_notification(
                            title=f"Event Ending Soon: {event.name}",
                            message=(
                                f"The event '{event.name}' is concluding soon on {end_time.strftime('%d %b %Y %H:%M')}. "
                                f"Make sure all activities and report submissions are completed."
                            ),
                            category="EVENT_EXPIRE",
                            priority="HIGH",
                            target_audience="ALL",
                            entity_type="event",
                            entity_id=event.id,
                            action_url=f"/events/{event.id}",
                        )
                        triggered_count += 1

        except Exception as e:
            logger.error(f"Error checking event notifications: {e}")

        return triggered_count

    # -------------------------------------------------------------------------
    # 4. SCHEME START & EXPIRE NOTIFICATIONS (BROADCAST TO ALL)
    # -------------------------------------------------------------------------
    async def check_and_trigger_scheme_notifications(self) -> int:
        """
        Checks active schemes and triggers:
        1. Scheme Start: when scheme is open for applications (start_time <= now <= end_time)
        2. Scheme Expire: when scheme deadline is within 7 days (now <= end_time <= now + 7 days)
        """
        now = datetime.now(tz=timezone.utc)
        triggered_count = 0

        try:
            # Query active schemes
            schemes_result = await self.db.execute(select(Scheme).where(Scheme.active.is_(True)))
            schemes = schemes_result.scalars().all()

            for scheme in schemes:
                start_time = scheme.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

                end_time = scheme.end_time
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                # 1. Scheme Start Notification
                if start_time <= now <= end_time:
                    existing_start = await self.db.execute(
                        select(InAppNotification.id).where(
                            and_(
                                InAppNotification.is_broadcast.is_(True),
                                InAppNotification.category == "SCHEME_START",
                                InAppNotification.entity_id == scheme.id,
                            )
                        )
                    )
                    if not existing_start.scalar_one_or_none():
                        await self.create_broadcast_notification(
                            title=f"New Scheme Launched: {scheme.name}",
                            message=(
                                f"Applications are now open for '{scheme.name}'. "
                                f"Review guidelines and eligibility criteria to apply."
                            ),
                            category="SCHEME_START",
                            priority="HIGH",
                            target_audience="ALL",
                            entity_type="scheme",
                            entity_id=scheme.id,
                            action_url=f"/schemes/{scheme.id}",
                        )
                        triggered_count += 1

                # 2. Scheme Expire (within 7 days)
                if now <= end_time <= now + timedelta(days=7):
                    existing_expire = await self.db.execute(
                        select(InAppNotification.id).where(
                            and_(
                                InAppNotification.is_broadcast.is_(True),
                                InAppNotification.category == "SCHEME_EXPIRE",
                                InAppNotification.entity_id == scheme.id,
                            )
                        )
                    )
                    if not existing_expire.scalar_one_or_none():
                        await self.create_broadcast_notification(
                            title=f"Scheme Closing Soon: {scheme.name}",
                            message=(
                                f"Applications for '{scheme.name}' will close on {end_time.strftime('%d %b %Y')}. "
                                f"Submit any pending applications before the deadline."
                            ),
                            category="SCHEME_EXPIRE",
                            priority="HIGH",
                            target_audience="ALL",
                            entity_type="scheme",
                            entity_id=scheme.id,
                            action_url=f"/schemes/{scheme.id}",
                        )
                        triggered_count += 1

        except Exception as e:
            logger.error(f"Error checking scheme notifications: {e}")

        return triggered_count

    # -------------------------------------------------------------------------
    # 5. USER QUERIES & READ ACTIONS
    # -------------------------------------------------------------------------
    def _build_user_filter(self, user: Union[User, PublicUser]):
        """Build SQLAlchemy filter matching notifications applicable to this user."""
        is_authority_user = isinstance(user, User)
        target_audience_options = ["ALL", "STAFF"] if is_authority_user else ["ALL", "PUBLIC"]

        if is_authority_user:
            return or_(
                InAppNotification.user_id == user.id,
                and_(
                    InAppNotification.is_broadcast.is_(True),
                    InAppNotification.target_audience.in_(target_audience_options),
                ),
            )
        else:
            return or_(
                InAppNotification.public_user_id == user.id,
                and_(
                    InAppNotification.is_broadcast.is_(True),
                    InAppNotification.target_audience.in_(target_audience_options),
                ),
            )

    async def get_user_notifications(
        self,
        user: Union[User, PublicUser],
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        category: Optional[str] = None,
    ) -> Tuple[List[InAppNotificationItem], int, int]:
        """
        Fetch notifications for a user (direct + broadcasts), computing real-time read states.
        Returns: (items, total_count, unread_count)
        """
        is_authority = isinstance(user, User)
        read_join_cond = (
            and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.user_id == user.id,
            )
            if is_authority
            else and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.public_user_id == user.id,
            )
        )

        base_filter = self._build_user_filter(user)
        conditions = [base_filter]
        if category:
            conditions.append(InAppNotification.category == category)

        # Expression to determine if notification is read
        effective_is_read = or_(
            InAppNotification.is_read.is_(True),
            InAppNotificationRead.id.is_not(None),
        )

        # Compute unread count across all user notifications
        unread_stmt = (
            select(func.count(InAppNotification.id))
            .outerjoin(InAppNotificationRead, read_join_cond)
            .where(and_(*conditions, ~effective_is_read))
        )
        unread_count_res = await self.db.execute(unread_stmt)
        unread_count = unread_count_res.scalar() or 0

        # If unread_only is requested
        if unread_only:
            conditions.append(~effective_is_read)

        # Total count
        total_stmt = (
            select(func.count(InAppNotification.id))
            .outerjoin(InAppNotificationRead, read_join_cond)
            .where(and_(*conditions))
        )
        total_res = await self.db.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # Query items with join
        query = (
            select(
                InAppNotification,
                InAppNotificationRead.read_at.label("broadcast_read_at"),
                effective_is_read.label("computed_is_read"),
            )
            .outerjoin(InAppNotificationRead, read_join_cond)
            .where(and_(*conditions))
            .order_by(InAppNotification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        results = await self.db.execute(query)
        items: List[InAppNotificationItem] = []

        for row in results.all():
            notif: InAppNotification = row[0]
            b_read_at = row[1]
            is_read = bool(row[2])
            read_at = notif.read_at or b_read_at if is_read else None

            items.append(
                InAppNotificationItem(
                    id=notif.id,
                    title=notif.title,
                    message=notif.message,
                    category=notif.category,
                    priority=notif.priority,
                    entity_type=notif.entity_type,
                    entity_id=notif.entity_id,
                    action_url=notif.action_url,
                    is_read=is_read,
                    read_at=read_at,
                    created_at=notif.created_at,
                )
            )

        return items, total_count, unread_count

    async def get_unread_count(self, user: Union[User, PublicUser]) -> int:
        """Fast lookup of unread notification count for the badge."""
        is_authority = isinstance(user, User)
        read_join_cond = (
            and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.user_id == user.id,
            )
            if is_authority
            else and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.public_user_id == user.id,
            )
        )

        base_filter = self._build_user_filter(user)
        effective_is_read = or_(
            InAppNotification.is_read.is_(True),
            InAppNotificationRead.id.is_not(None),
        )

        stmt = (
            select(func.count(InAppNotification.id))
            .outerjoin(InAppNotificationRead, read_join_cond)
            .where(and_(base_filter, ~effective_is_read))
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def mark_notification_as_read(
        self,
        user: Union[User, PublicUser],
        notification_id: int,
    ) -> bool:
        """Mark a single notification as read for the user."""
        base_filter = self._build_user_filter(user)
        stmt = select(InAppNotification).where(
            and_(InAppNotification.id == notification_id, base_filter)
        )
        res = await self.db.execute(stmt)
        notif = res.scalar_one_or_none()
        if not notif:
            return False

        now = datetime.now(tz=timezone.utc)
        is_authority = isinstance(user, User)

        if notif.is_broadcast:
            # Insert read receipt if not already recorded
            read_cond = (
                and_(
                    InAppNotificationRead.notification_id == notif.id,
                    InAppNotificationRead.user_id == user.id,
                )
                if is_authority
                else and_(
                    InAppNotificationRead.notification_id == notif.id,
                    InAppNotificationRead.public_user_id == user.id,
                )
            )
            existing = await self.db.execute(select(InAppNotificationRead).where(read_cond))
            if not existing.scalar_one_or_none():
                read_receipt = InAppNotificationRead(
                    notification_id=notif.id,
                    user_id=user.id if is_authority else None,
                    public_user_id=user.id if not is_authority else None,
                    read_at=now,
                )
                self.db.add(read_receipt)
                await self.db.commit()
        else:
            notif.is_read = True
            notif.read_at = now
            await self.db.commit()

        return True

    async def mark_all_as_read(self, user: Union[User, PublicUser]) -> int:
        """Mark all unread notifications as read for the user."""
        now = datetime.now(tz=timezone.utc)
        is_authority = isinstance(user, User)
        marked_count = 0

        # 1. Update all unread direct notifications
        direct_filter = (
            and_(
                InAppNotification.user_id == user.id,
                InAppNotification.is_read.is_(False),
            )
            if is_authority
            else and_(
                InAppNotification.public_user_id == user.id,
                InAppNotification.is_read.is_(False),
            )
        )
        update_stmt = (
            update(InAppNotification)
            .where(direct_filter)
            .values(is_read=True, read_at=now)
        )
        res = await self.db.execute(update_stmt)
        marked_count += res.rowcount

        # 2. Insert read records for unread broadcast notifications
        target_audience_options = ["ALL", "STAFF"] if is_authority else ["ALL", "PUBLIC"]
        read_join_cond = (
            and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.user_id == user.id,
            )
            if is_authority
            else and_(
                InAppNotificationRead.notification_id == InAppNotification.id,
                InAppNotificationRead.public_user_id == user.id,
            )
        )

        unread_broadcasts_stmt = (
            select(InAppNotification.id)
            .outerjoin(InAppNotificationRead, read_join_cond)
            .where(
                and_(
                    InAppNotification.is_broadcast.is_(True),
                    InAppNotification.target_audience.in_(target_audience_options),
                    InAppNotificationRead.id.is_(None),
                )
            )
        )
        b_res = await self.db.execute(unread_broadcasts_stmt)
        unread_b_ids = b_res.scalars().all()

        for b_id in unread_b_ids:
            read_receipt = InAppNotificationRead(
                notification_id=b_id,
                user_id=user.id if is_authority else None,
                public_user_id=user.id if not is_authority else None,
                read_at=now,
            )
            self.db.add(read_receipt)
            marked_count += 1

        await self.db.commit()
        return marked_count
