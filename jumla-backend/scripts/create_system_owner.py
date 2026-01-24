"""
scripts/create_system_owner.py
ONE-TIME script to create the system owner account
Run this ONCE during initial deployment
"""
import asyncio
import sys
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.user import User
from app.models.audit_log import AuditLog
from sqlalchemy import select


async def create_system_owner():
    """Create the system owner account"""
    print("=== Create System Owner Account ===\n")
    print("⚠️  This should only be run ONCE during initial deployment")
    print("⚠️  System Owner has god-mode access to all organizations\n")
    
    async with get_db_context() as db:
        # Check if system owner already exists
        result = await db.execute(
            select(User).where(User.is_system_owner == True)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✗ System Owner already exists: {existing.email}")
            print(f"  Created at: {existing.created_at}")
            sys.exit(1)
        
        # Get system owner details
        email = input("System Owner email: ").strip()
        
        # Check if email is already in use
        result = await db.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"✗ Email {email} is already in use")
            sys.exit(1)
        
        full_name = input("Full name: ").strip()
        password = getpass("Password (min 12 characters): ")
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("\n✗ Passwords do not match")
            sys.exit(1)
        
        if len(password) < 12:
            print("\n✗ Password must be at least 12 characters for System Owner")
            sys.exit(1)
        
        # Create system owner
        system_owner = User(
            organization_id=None,  # System owner has no organization
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",  # Role doesn't matter, is_system_owner is what counts
            is_active=True,
            is_system_owner=True
        )
        
        db.add(system_owner)
        await db.flush()
        
        # Create audit log
        audit = AuditLog(
            organization_id=None,
            user_id=None,
            performed_by="deployment_script",
            entity_type="user",
            entity_id=system_owner.id,
            action="create_system_owner",
            before=None,
            after={
                "email": system_owner.email,
                "full_name": system_owner.full_name,
                "is_system_owner": True
            }
        )
        db.add(audit)
        
        await db.commit()
        
        print(f"\n✓ System Owner created successfully!")
        print(f"\nEmail: {email}")
        print(f"ID: {system_owner.id}")
        print(f"\n⚠️  Keep these credentials EXTREMELY secure!")
        print(f"⚠️  This account can access and modify ALL organizations")


if __name__ == "__main__":
    asyncio.run(create_system_owner())