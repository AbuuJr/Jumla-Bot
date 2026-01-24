"""
scripts/create_admin.py
Script to create admin user
"""
import asyncio
import sys
from getpass import getpass
from pathlib import Path
import sys

# --- Project root & python path (so imports work) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from sqlalchemy import select


async def create_admin_user():
    """Interactive script to create admin user"""
    print("=== Create Admin User ===\n")
    
    # Get organization
    org_slug = input("Organization slug (leave empty to list organizations): ").strip()
    
    async with get_db_context() as db:
        if not org_slug:
            # List existing organizations
            result = await db.execute(select(Organization))
            orgs = result.scalars().all()
            
            if not orgs:
                print("\nNo organizations found. Creating new organization...\n")
                org_name = input("Organization name: ").strip()
                org_slug = input("Organization slug: ").strip()
                
                org = Organization(
                    name=org_name,
                    slug=org_slug,
                    settings={}
                )
                db.add(org)
                await db.flush()
                print(f"\n✓ Created organization: {org_name}")
            else:
                print("\nExisting organizations:")
                for i, org in enumerate(orgs, 1):
                    print(f"{i}. {org.name} ({org.slug})")
                
                choice = int(input("\nSelect organization (number): "))
                org = orgs[choice - 1]
        else:
            # Find organization by slug
            result = await db.execute(
                select(Organization).where(Organization.slug == org_slug)
            )
            org = result.scalar_one_or_none()
            
            if not org:
                print(f"\nOrganization '{org_slug}' not found.")
                sys.exit(1)
        
        print(f"\nCreating admin for: {org.name}\n")
        
        # Get user details
        email = input("Admin email: ").strip()
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"\n✗ User with email {email} already exists")
            sys.exit(1)
        
        full_name = input("Full name: ").strip()
        password = getpass("Password (min 8 characters): ")
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("\n✗ Passwords do not match")
            sys.exit(1)
        
        if len(password) < 8:
            print("\n✗ Password must be at least 8 characters")
            sys.exit(1)
        
        # Create admin user
        admin = User(
            organization_id=org.id,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        
        print(f"\n✓ Admin user created successfully!")
        print(f"\nEmail: {email}")
        print(f"Role: admin")
        print(f"Organization: {org.name}")
        print(f"\nYou can now login at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(create_admin_user())


