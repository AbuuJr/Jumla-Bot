"""
scripts/reset_admin_password.py
System Owner script to reset admin passwords (emergency recovery)
"""
import asyncio
import sys
import argparse
import secrets
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.user import User
from app.models.audit_log import AuditLog
from sqlalchemy import select


async def reset_admin_password(
    admin_email: str,
    new_password: str = None,
    system_owner_email: str = None
):
    """
    Reset admin password (System Owner only)
    
    Args:
        admin_email: Email of admin whose password to reset
        new_password: New password (generated if not provided)
        system_owner_email: Email of system owner performing action
    """
    async with get_db_context() as db:
        # Verify system owner if email provided
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
        else:
            system_owner_email = "system_owner_script"
        
        # Find target admin
        result = await db.execute(
            select(User).where(User.email == admin_email)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f"✗ User {admin_email} not found")
            sys.exit(1)
        
        if admin.role != "admin":
            print(f"✗ User {admin_email} is not an admin (role: {admin.role})")
            print(f"  Use admin UI to reset non-admin passwords")
            sys.exit(1)
        
        # Generate password if not provided
        if not new_password:
            new_password = secrets.token_urlsafe(16)
            temp_password_generated = True
        else:
            temp_password_generated = False
        
        # Store before state
        before_state = {
            "email": admin.email,
            "role": admin.role,
            "organization_id": str(admin.organization_id),
            "is_active": admin.is_active
        }
        
        # Update password
        admin.password_hash = hash_password(new_password)
        
        # Create audit log
        audit = AuditLog(
            organization_id=admin.organization_id,
            user_id=None,
            performed_by=system_owner_email,
            entity_type="user",
            entity_id=admin.id,
            action="reset_password",
            before=before_state,
            after={
                "email": admin.email,
                "role": admin.role,
                "organization_id": str(admin.organization_id),
                "is_active": admin.is_active,
                "password_reset": True
            }
        )
        db.add(audit)
        
        await db.commit()
        
        print(f"✓ Password reset successful for {admin_email}")
        
        if temp_password_generated:
            print(f"\nTemporary password: {new_password}")
            print(f"⚠️  Share this securely with the admin")
            print(f"⚠️  Admin should change this password immediately after login")
        else:
            print(f"\nPassword has been updated")


def main():
    parser = argparse.ArgumentParser(
        description="Reset admin password (System Owner only)"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email of admin whose password to reset"
    )
    parser.add_argument(
        "--new-password",
        help="New password (optional, will generate if not provided)"
    )
    parser.add_argument(
        "--system-owner",
        help="Email of system owner performing this action (for audit trail)"
    )
    
    args = parser.parse_args()
    
    print("=== Reset Admin Password ===\n")
    print(f"Admin: {args.email}")
    print(f"Performed by: {args.system_owner or 'system_owner_script'}\n")
    
    print("⚠️  This action requires System Owner privileges")
    print("⚠️  The admin's existing sessions will NOT be revoked")
    print("⚠️  Consider using the AuthService API for full session revocation\n")
    
    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        sys.exit(0)
    
    asyncio.run(reset_admin_password(
        admin_email=args.email,
        new_password=args.new_password,
        system_owner_email=args.system_owner
    ))


if __name__ == "__main__":
    main()