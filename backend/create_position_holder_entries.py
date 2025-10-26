"""
Script to create PositionHolder entries for all users based on their geographic assignments.

This script:
1. Fetches all users from the database
2. Determines their role based on geographic assignment (district_id, block_id, gp_id)
3. Creates a PositionHolder entry for each user with appropriate role and geographic assignment
4. Ensures roles exist in the database before creating position holders

Role Assignment Logic:
- No geographic assignment (no district, block, or GP) -> ADMIN
- District only (no block or GP) -> CEO (Chief Executive Officer)
- Block only (no GP) -> BDO (Block Development Officer)
- GP assigned -> VDO (Village Development Officer)
- Default -> WORKER

Usage:
    python create_position_holder_entries.py

Configuration:
    Set dry_run=True in main() function to preview changes without committing to database
"""

import asyncio
from datetime import date
from typing import Dict, List

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.database.auth import User, Role, PositionHolder
from services.auth import AuthService, UserRole


async def ensure_roles_exist(db: AsyncSession) -> dict[str, Role]:
    """
    Ensure all required roles exist in the database.
    Returns a dictionary mapping role names to Role objects.
    """
    roles_map = {}

    # Define all roles that should exist
    role_definitions = [
        (UserRole.SUPERADMIN, "Super Administrator with full system access"),
        (UserRole.ADMIN, "Administrator with full system access"),
        (UserRole.SMD, "State Mission Director"),
        (UserRole.CEO, "District Collector/Chief Executive Officer"),
        (UserRole.BDO, "Block Development Officer"),
        (UserRole.VDO, "Village Development Officer"),
        (UserRole.WORKER, "Worker"),
    ]

    for role_name, description in role_definitions:
        # Check if role exists
        result = await db.execute(select(Role).where(Role.name == role_name.value))
        role = result.scalar_one_or_none()

        if not role:
            # Create role if it doesn't exist
            role = Role(name=role_name.value, description=description)
            db.add(role)
            await db.flush()
            print(f"Created role: {role_name.value}")

        roles_map[role_name.value] = role

    await db.commit()
    return roles_map


def determine_role(user: User) -> UserRole:
    """
    Determine the role of a user based on their geographic assignment.

    Logic:
    - No geographic assignment (no district, block, or GP) -> ADMIN
    - District only (no block or GP) -> CEO
    - Block only (no GP) -> BDO
    - GP assigned -> VDO
    - Default -> WORKER
    """
    if not user.district_id and not user.block_id and not user.gp_id:
        return UserRole.ADMIN
    if user.district_id and not user.block_id and not user.gp_id:
        return UserRole.CEO
    if user.block_id and not user.gp_id:
        return UserRole.BDO
    if user.gp_id:
        return UserRole.VDO
    return UserRole.WORKER


async def create_position_holders(db: AsyncSession, dry_run: bool = False):
    """
    Create PositionHolder entries for all users based on their geographic assignments.

    Args:
        db: Database session
        dry_run: If True, don't actually create entries, just print what would be created
    """
    print("=" * 80)
    print("CREATING POSITION HOLDER ENTRIES")
    print("=" * 80)

    # Ensure all roles exist
    print("\n[1/4] Ensuring roles exist...")
    roles_map = await ensure_roles_exist(db)
    print(f"✓ {len(roles_map)} roles available")

    # Fetch all users
    print("\n[2/4] Fetching all users...")
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    print(f"✓ Found {len(users)} users")

    # Process each user
    print("\n[3/4] Processing users and determining roles...")
    created_count = 0
    skipped_count = 0
    error_count = 0

    created_count, skipped_count, error_count = await create_users(db, dry_run, roles_map, users)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total users processed: {len(users)}")
    print(f"Position holders created: {created_count}")
    print(f"Users skipped (already have position holder): {skipped_count}")
    print(f"Errors encountered: {error_count}")
    print("=" * 80)


async def create_users(
    db: AsyncSession, dry_run: bool, roles_map: Dict[str, Role], users: List[User]
) -> tuple[int, int, int]:
    """Create PositionHolder entries for users."""
    created_count = 0
    skipped_count = 0
    error_count = 0

    for user in users:
        try:
            # Check if position holder already exists for this user
            existing_ph = await db.execute(select(PositionHolder).where(PositionHolder.user_id == user.id))
            if existing_ph.scalar_one_or_none():
                print(f"  ⊙ User {user.username} (ID: {user.id}) already has a PositionHolder entry - skipping")
                skipped_count += 1
                continue

            # Determine role based on geographic assignment
            user_role = AuthService.get_role_by_user(user)
            role = roles_map[user_role.value]

            # Extract user details for position holder
            # Generate name from username if no other source available
            name_parts = user.username.split(".")
            first_name = name_parts[0].title() if name_parts else "Unknown"
            last_name = name_parts[-1].title() if len(name_parts) > 1 else "User"

            # Create position holder entry
            position_holder = PositionHolder(
                user_id=user.id,
                role_id=role.id,
                district_id=user.district_id,
                block_id=user.block_id,
                village_id=user.gp_id,
                first_name=first_name,
                last_name=last_name,
                middle_name=None,
                date_of_joining=date.today(),
                start_date=date(2025, 1, 1),
                end_date=None,  # Active position
            )

            if dry_run:
                print(
                    f"  [DRY RUN] Would create PositionHolder for user {user.username} (ID: {user.id}) with role {user_role.value}"
                )
            else:
                await insertion(db, user, role, first_name, last_name)
                created_count += 1

                # Build geographic info string
                geo_info: List[str] = []
                if user.district_id:
                    geo_info.append(f"District: {user.district_id}")
                if user.block_id:
                    geo_info.append(f"Block: {user.block_id}")
                if user.gp_id:
                    geo_info.append(f"GP: {user.gp_id}")
                geo_str = ", ".join(geo_info) if geo_info else "No geographic assignment"

                print(
                    f"  ✓ Created PositionHolder for user {user.username} (ID: {user.id}) - Role: {user_role.value} - {geo_str}"
                )

        except Exception as e:
            error_count += 1
            print(f"  ✗ Error processing user {user.username} (ID: {user.id}): {str(e)}")

    # Commit changes if not dry run
    if not dry_run:
        print("\n[4/4] Committing changes to database...")
        await db.commit()
        print("✓ Changes committed successfully")
    else:
        print("\n[4/4] Dry run completed - no changes made to database")
    return created_count, skipped_count, error_count


async def insertion(db: AsyncSession, user: User, role: Role, first_name: str, last_name: str):
    """Insert a PositionHolder entry into the database."""
    if not user.gp_id:
        return
    if user.gp_id <= 3445:
        return
    await db.execute(
        insert(PositionHolder).values(
            user_id=user.id,
            role_id=role.id,
            district_id=user.district_id,
            block_id=user.block_id,
            village_id=user.gp_id,
            first_name=first_name,
            last_name=last_name,
            middle_name=None,
            date_of_joining=date.today(),
            start_date=date(2025, 1, 1),
            end_date=None,
        )
    )
    await db.commit()


async def main():
    """Main entry point for the script."""
    # You can set dry_run=True to preview what would be created without actually creating entries
    dry_run = False  # Set to True to preview changes

    async with AsyncSessionLocal() as db:
        try:
            await create_position_holders(db, dry_run=dry_run)
        except Exception as e:
            print(f"\n✗ Fatal error: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Position Holder Entry Creation Script")
    print("=" * 80)
    print("\nThis script will create PositionHolder entries for all users")
    print("based on their geographic assignments (district, block, GP).\n")

    asyncio.run(main())
