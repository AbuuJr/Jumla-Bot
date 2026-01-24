"""
scripts/create_admin.py
Enhanced script to create admin user - supports both CLI and interactive modes
"""
import asyncio
import sys
import argparse
import secrets
from getpass import getpass
from pathlib import Path

# --- Project root & python path (so imports work) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.audit_log import AuditLog
from sqlalchemy import select


async def create_admin_user_interactive():
    """Interactive mode (original behavior)"""
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
            is_active=True,
            is_system_owner=False  # Explicitly set
        )
        
        db.add(admin)
        await db.flush()
        
        # Create audit log
        audit = AuditLog(
            organization_id=org.id,
            user_id=None,
            performed_by="admin_creation_script",
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
        db.add(audit)
        
        await db.commit()
        
        print(f"\n✓ Admin user created successfully!")
        print(f"\nEmail: {email}")
        print(f"Role: admin")
        print(f"Organization: {org.name}")
        print(f"\nYou can now login at: http://localhost:8000/docs")


async def create_admin_user_cli(
    org_slug: str,
    email: str,
    full_name: str,
    password: str = None,
    system_owner_email: str = None
):
    """
    CLI mode - create admin with command line arguments
    
    Args:
        org_slug: Organization slug
        email: Admin email
        full_name: Admin full name
        password: Admin password (generated if not provided)
        system_owner_email: Email of system owner performing action (for audit)
    """
    async with get_db_context() as db:
        # Verify system owner if provided
        if system_owner_email:
            result = await db.execute(
                select(User).where(
                    User.email == system_owner_email,
                    User.is_system_owner == True
                )
            )
            system_owner = result.scalar_one_or_none()
            
            if not system_owner:
                print(f"✗ {system_owner_email} is not a System Owner")
                sys.exit(1)
            
            performed_by = system_owner_email
        else:
            performed_by = "admin_creation_script"
        
        # Find organization
        result = await db.execute(
            select(Organization).where(Organization.slug == org_slug)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            print(f"✗ Organization '{org_slug}' not found")
            
            # List available organizations
            result = await db.execute(select(Organization))
            orgs = result.scalars().all()
            
            if orgs:
                print("\nAvailable organizations:")
                for org in orgs:
                    print(f"  - {org.name} ({org.slug})")
            
            sys.exit(1)
        
        # Check if admin email already exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"✗ User with email {email} already exists")
            sys.exit(1)
        
        # Generate password if not provided
        if not password:
            password = secrets.token_urlsafe(16)
            temp_password_generated = True
        else:
            temp_password_generated = False
        
        if len(password) < 8:
            print("✗ Password must be at least 8 characters")
            sys.exit(1)
        
        # Create admin user
        admin = User(
            organization_id=org.id,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True,
            is_system_owner=False
        )
        
        db.add(admin)
        await db.flush()
        
        # Create audit log
        audit = AuditLog(
            organization_id=org.id,
            user_id=None,
            performed_by=performed_by,
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
        db.add(audit)
        
        await db.commit()
        
        print(f"✓ Admin user created successfully!")
        print(f"\nOrganization: {org.name}")
        print(f"Email: {email}")
        print(f"Full Name: {full_name}")
        print(f"Role: admin")
        
        if temp_password_generated:
            print(f"\nTemporary password: {password}")
            print(f"⚠️  Please share this securely with the admin")
            print(f"⚠️  Admin should change this password after first login")
        else:
            print(f"\nPassword has been set")
        
        print(f"\nAdmin can login at: http://localhost:8000/api/v1/auth/login")


def main():
    parser = argparse.ArgumentParser(
        description="Create admin user for an organization",
        epilog="If no arguments provided, runs in interactive mode"
    )
    parser.add_argument(
        "--org",
        help="Organization slug"
    )
    parser.add_argument(
        "--email",
        help="Admin email address"
    )
    parser.add_argument(
        "--fullname",
        help="Admin full name"
    )
    parser.add_argument(
        "--password",
        help="Admin password (optional, will generate if not provided)"
    )
    parser.add_argument(
        "--system-owner",
        help="Email of system owner performing this action (for audit trail)"
    )
    
    args = parser.parse_args()
    
    # Determine mode: CLI or Interactive
    if args.org and args.email and args.fullname:
        # CLI mode
        print("=== Create Admin User (CLI Mode) ===\n")
        
        if args.system_owner:
            print(f"Performed by: {args.system_owner}")
        
        print(f"Organization: {args.org}")
        print(f"Email: {args.email}")
        print(f"Full Name: {args.fullname}\n")
        
        confirm = input("Proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            sys.exit(0)
        
        asyncio.run(create_admin_user_cli(
            org_slug=args.org,
            email=args.email,
            full_name=args.fullname,
            password=args.password,
            system_owner_email=args.system_owner
        ))
    else:
        # Interactive mode (original behavior)
        if any([args.org, args.email, args.fullname]):
            print("⚠️  Incomplete arguments. Switching to interactive mode.\n")
            print("For CLI mode, provide: --org, --email, and --fullname\n")
        
        asyncio.run(create_admin_user_interactive())


if __name__ == "__main__":
    main()