#!/usr/bin/env python3
"""
Script to initialize default data for SBM Rajasthan application.
This creates default roles, admin user, and some sample geographical data.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text  # Add this import
from database import AsyncSessionLocal, init_db
from models.database.auth import User, Role, PositionHolder
from models.database.geography import District, Block, Village
from models.database.complaint import ComplaintType, ComplaintStatus
from services.auth import AuthService


async def create_default_roles():
    """Create default roles."""
    async with AsyncSessionLocal() as session:
        roles = [
            ("SUPERADMIN", "Super Administrator with full system access"),
            ("ADMIN", "System Administrator"),
            ("CEO", "District Collector"),
            ("BDO", "Block Development Officer"),
            ("VDO", "Village Development Officer"),
            ("WORKER", "Field Worker"),
            ("PUBLIC", "Public User"),
        ]
        
        for role_name, description in roles:
            # Check if role exists
            result = await session.execute(
                text("SELECT id FROM roles WHERE name = :name"),  # Wrap with text()
                {"name": role_name}
            )
            if not result.fetchone():
                role = Role(name=role_name, description=description)
                session.add(role)
        
        await session.commit()
        print("✓ Default roles created")


async def create_admin_user():
    """Create default admin user."""
    try:
        user = "admin4"
        async with AsyncSessionLocal() as session:
            auth_service = AuthService(session)
            
            # Check if admin user exists
            admin_user = await auth_service.get_user_by_username(user)
            if not admin_user:
                # Create admin user
                admin_user = await auth_service.create_user(
                    username=user,
                    email=f"{user}@sbm-rajasthan.gov.in",
                    password="admin123",
                    is_active=True
                )
                
                # Get admin role
                admin_role = await auth_service.get_role_by_name("ADMIN")
                if admin_role:
                    # Create position holder for admin
                    await auth_service.create_position_holder(
                        user_id=admin_user.id,
                        role_id=admin_role.id,
                        first_name="System",
                        last_name="Administrator",
                    )
                
                print("✓ Admin user created (username: admin, password: admin123)")
            else:
                print("✓ Admin user already exists")
    except:
        import traceback
        traceback.print_exc()


async def create_sample_geography():
    """Create sample geographical data."""
    async with AsyncSessionLocal() as session:
        # Create sample district
        result = await session.execute(
            text("SELECT id FROM districts WHERE name = :name"),  # Wrap with text()
            {"name": "Jaipur"}
        )
        district_data = result.fetchone()
        
        if not district_data:
            district = District(name="Jaipur", description="Jaipur District")
            session.add(district)
            await session.flush()
            district_id = district.id
            print("✓ Sample district 'Jaipur' created")
        else:
            district_id = district_data[0]
            print("✓ Sample district 'Jaipur' already exists")
        
        # Create sample block
        result = await session.execute(
            text("SELECT id FROM blocks WHERE name = :name AND district_id = :district_id"),  # Wrap with text()
            {"name": "Jaipur Central", "district_id": district_id}
        )
        block_data = result.fetchone()
        
        if not block_data:
            block = Block(
                name="Jaipur Central",
                description="Central Block of Jaipur",
                district_id=district_id
            )
            session.add(block)
            await session.flush()
            block_id = block.id
            print("✓ Sample block 'Jaipur Central' created")
        else:
            block_id = block_data[0]
            print("✓ Sample block 'Jaipur Central' already exists")
        
        # Create sample village
        result = await session.execute(
            text("SELECT id FROM villages WHERE name = :name AND block_id = :block_id"),  # Wrap with text()
            {"name": "Sample Village", "block_id": block_id}
        )
        village_data = result.fetchone()
        
        if not village_data:
            village = Village(
                name="Sample Village",
                description="A sample village for testing",
                block_id=block_id,
                district_id=district_id
            )
            session.add(village)
            print("✓ Sample village 'Sample Village' created")
        else:
            print("✓ Sample village 'Sample Village' already exists")
        
        await session.commit()


async def create_default_complaint_data():
    """Create default complaint types and statuses."""
    async with AsyncSessionLocal() as session:
        # Create complaint types
        complaint_types = [
            ("Road Repair", "Issues related to road maintenance and repair"),
            ("Water Supply", "Issues related to water supply and quality"),
            ("Sanitation", "Issues related to cleanliness and sanitation"),
            ("Street Lighting", "Issues related to street lights and electrical"),
            ("Drainage", "Issues related to drainage and sewerage"),
        ]
        
        for name, description in complaint_types:
            result = await session.execute(
                text("SELECT id FROM complaint_types WHERE name = :name"),  # Wrap with text()
                {"name": name}
            )
            if not result.fetchone():
                complaint_type = ComplaintType(name=name, description=description)
                session.add(complaint_type)
        
        # Create complaint statuses
        complaint_statuses = [
            ("OPEN", "Complaint has been registered"),
            ("ASSIGNED", "Complaint has been assigned to a worker"),
            ("IN_PROGRESS", "Work is in progress"),
            ("COMPLETED", "Work has been completed by worker"),
            ("VERIFIED", "Work has been verified by VDO"),
            ("CLOSED", "Complaint has been closed"),
            ("INVALID", "Complaint marked as invalid or not actionable"),
        ]
        
        for name, description in complaint_statuses:
            result = await session.execute(
                text("SELECT id FROM complaint_statuses WHERE name = :name"),  # Wrap with text()
                {"name": name}
            )
            if not result.fetchone():
                status = ComplaintStatus(name=name, description=description)
                session.add(status)
        
        await session.commit()
        print("✓ Default complaint types and statuses created")


async def main():
    """Main initialization function."""
    print("🚀 Initializing SBM Rajasthan Application...")
    
    try:
        # Initialize database tables
        print("\n📊 Creating database tables...")
        await init_db()
        print("✓ Database tables created")
        
        # Create default data
        print("\n👥 Creating default roles...")
        await create_default_roles()
        
        print("\n🔐 Creating admin user...")
        await create_admin_user()
        
        print("\n🗺️ Creating sample geography...")
        await create_sample_geography()
        
        print("\n📋 Creating default complaint data...")
        await create_default_complaint_data()
        
        print("\n✅ Initialization completed successfully!")
        print("\n📌 Next steps:")
        print("   1. Start the application: docker compose up -d")
        print("   2. Access API documentation: http://localhost:8000/docs")
        print("   3. Login with admin credentials: username=admin, password=admin123")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())