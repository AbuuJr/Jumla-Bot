"""
scripts/create_organization.py
System Owner script to create organization with primary admin
"""
import asyncio
import sys
import argparse
import secrets
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.audit_log import AuditLog
from sqlalchemy import select


async def create_organization(
    name: str,
    slug: str,
    admin_email: str,
    admin_fullname: str,
    admin_password: str = None
):
    """
    Create organization with primary admin user
    
    Args:
        name: Organization display name
        slug: Organization slug (unique identifier)
        admin_email: Primary admin email
        admin_fullname: Primary admin full name
        admin_password: Optional password (generated if not provided)
    """
    async with get_db_context() as db:
        # Check if organization slug already exists
        result = await db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if result.scalar_one_or_none():
            print(f"✗ Organization with slug '{slug}' already exists")
            sys.exit(1)
        
        # Check if admin email already exists
        result = await db.execute(
            select(User).where(User.email == admin_email)
        )
        if result.scalar_one_or_none():
            print(f"✗ User with email '{admin_email}' already exists")
            sys.exit(1)
        
        # Generate temporary password if not provided
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            temp_password_generated = True
        else:
            temp_password_generated = False
        
        # Create organization
        org = Organization(
            name=name,
            slug=slug,
            settings={},
            is_active=True
        )
        db.add(org)
        await db.flush()  # Get org.id
        
        print(f"✓ Created organization: {name} ({slug})")
        print(f"  Organization ID: {org.id}")
        
        # Create primary admin user
        admin = User(
            organization_id=org.id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=admin_fullname,
            role="admin",
            is_active=True,
            is_system_owner=False
        )
        db.add(admin)
        await db.flush()
        
        print(f"✓ Created primary admin: {admin_fullname} ({admin_email})")
        print(f"  User ID: {admin.id}")
        
        if temp_password_generated:
            print(f"  Temporary password: {admin_password}")
            print(f"  ⚠️  Please share this securely with the admin")
        
        # Create audit log for organization creation
        audit_org = AuditLog(
            organization_id=org.id,
            user_id=None,
            performed_by="system_owner_script",
            entity_type="organization",
            entity_id=org.id,
            action="create",
            before=None,
            after={
                "name": org.name,
                "slug": org.slug,
                "is_active": org.is_active
            }
        )
        db.add(audit_org)
        
        # Create audit log for admin creation
        audit_admin = AuditLog(
            organization_id=org.id,
            user_id=None,
            performed_by="system_owner_script",
            entity_type="user",
            entity_id=admin.id,
            action="create",
            before=None,
            after={
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_active": admin.is_active
            }
        )
        db.add(audit_admin)
        
        await db.commit()
        
        print(f"\n✓ Organization and admin created successfully!")
        print(f"\n=== Summary ===")
        print(f"Organization: {org.name}")
        print(f"Slug: {org.slug}")
        print(f"Admin: {admin.email}")
        print(f"Created at: {datetime.utcnow().isoformat()}Z")


def main():
    parser = argparse.ArgumentParser(
        description="Create organization with primary admin (System Owner only)"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Organization display name (e.g., 'ABC Home Buyers LLC')"
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Organization slug (e.g., 'abc-home-buyers')"
    )
    parser.add_argument(
        "--admin-email",
        required=True,
        help="Primary admin email"
    )
    parser.add_argument(
        "--admin-fullname",
        required=True,
        help="Primary admin full name"
    )
    parser.add_argument(
        "--admin-password",
        help="Admin password (optional, will generate if not provided)"
    )
    
    args = parser.parse_args()
    
    print("=== Create Organization ===\n")
    print(f"Name: {args.name}")
    print(f"Slug: {args.slug}")
    print(f"Admin: {args.admin_fullname} <{args.admin_email}>\n")
    
    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        sys.exit(0)
    
    asyncio.run(create_organization(
        name=args.name,
        slug=args.slug,
        admin_email=args.admin_email,
        admin_fullname=args.admin_fullname,
        admin_password=args.admin_password
    ))


if __name__ == "__main__":
    main()