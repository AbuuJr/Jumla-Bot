"""
scripts/delete_organization.py
System Owner script to soft-delete or hard-delete organization
"""
import asyncio
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.models.organization import Organization
from app.models.user import User
from app.models.audit_log import AuditLog
from sqlalchemy import select, func


async def delete_organization(slug: str, force: bool = False):
    """
    Delete organization (soft delete by default, hard delete with --force)
    
    Args:
        slug: Organization slug
        force: If True, perform hard delete (PERMANENT)
    """
    async with get_db_context() as db:
        # Find organization
        result = await db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            print(f"✗ Organization '{slug}' not found")
            sys.exit(1)
        
        # Count users
        result = await db.execute(
            select(func.count()).select_from(User).where(User.organization_id == org.id)
        )
        user_count = result.scalar()
        
        print(f"Organization: {org.name} ({org.slug})")
        print(f"Users: {user_count}")
        print(f"Status: {'Active' if org.is_active else 'Inactive'}")
        print(f"Created: {org.created_at}")
        
        if force:
            print(f"\n⚠️  HARD DELETE - This will PERMANENTLY delete:")
            print(f"  - Organization record")
            print(f"  - All {user_count} users")
            print(f"  - All leads, buyers, and related data")
            print(f"  - All audit logs")
            print(f"\n⚠️  THIS CANNOT BE UNDONE!")
        else:
            print(f"\n→ SOFT DELETE - This will:")
            print(f"  - Mark organization as inactive")
            print(f"  - Prevent all users from logging in")
            print(f"  - Preserve all data for recovery")
        
        confirm = input(f"\nType '{org.slug}' to confirm: ").strip()
        if confirm != org.slug:
            print("Cancelled - slug did not match")
            sys.exit(0)
        
        # Store before state for audit
        before_state = {
            "name": org.name,
            "slug": org.slug,
            "is_active": org.is_active,
            "user_count": user_count
        }
        
        if force:
            # Hard delete - CASCADE will handle related records
            audit = AuditLog(
                organization_id=None,  # Org will be deleted
                user_id=None,
                performed_by="system_owner_script",
                entity_type="organization",
                entity_id=org.id,
                action="hard_delete",
                before=before_state,
                after=None
            )
            db.add(audit)
            await db.flush()  # Write audit before deleting org
            
            await db.delete(org)
            await db.commit()
            
            print(f"\n✓ Organization '{slug}' permanently deleted")
        else:
            # Soft delete - mark as inactive
            org.is_active = False
            
            # Deactivate all users
            result = await db.execute(
                select(User).where(User.organization_id == org.id)
            )
            users = result.scalars().all()
            for user in users:
                user.is_active = False
            
            audit = AuditLog(
                organization_id=org.id,
                user_id=None,
                performed_by="system_owner_script",
                entity_type="organization",
                entity_id=org.id,
                action="soft_delete",
                before=before_state,
                after={
                    "name": org.name,
                    "slug": org.slug,
                    "is_active": False,
                    "users_deactivated": len(users)
                }
            )
            db.add(audit)
            
            await db.commit()
            
            print(f"\n✓ Organization '{slug}' deactivated")
            print(f"✓ {len(users)} users deactivated")
            print(f"\nTo reactivate: python scripts/update_organization.py --slug {slug} --activate")


def main():
    parser = argparse.ArgumentParser(
        description="Delete organization (System Owner only)"
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Organization slug"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="HARD DELETE - permanently remove organization and all data"
    )
    
    args = parser.parse_args()
    
    asyncio.run(delete_organization(
        slug=args.slug,
        force=args.force
    ))


if __name__ == "__main__":
    main()