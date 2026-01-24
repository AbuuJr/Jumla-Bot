"""
scripts/update_organization.py
System Owner script to update organization properties
"""
import asyncio
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.models.organization import Organization
from app.models.audit_log import AuditLog
from sqlalchemy import select


async def update_organization(
    slug: str,
    new_name: str = None,
    new_slug: str = None,
    activate: bool = False,
    deactivate: bool = False
):
    """
    Update organization properties
    
    Args:
        slug: Current organization slug
        new_name: New display name (optional)
        new_slug: New slug (optional)
        activate: Set is_active = True
        deactivate: Set is_active = False
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
        
        # Store before state
        before_state = {
            "name": org.name,
            "slug": org.slug,
            "is_active": org.is_active
        }
        
        changes = []
        
        # Update name
        if new_name and new_name != org.name:
            old_name = org.name
            org.name = new_name
            changes.append(f"name: '{old_name}' → '{new_name}'")
        
        # Update slug
        if new_slug and new_slug != org.slug:
            # Check if new slug is available
            result = await db.execute(
                select(Organization).where(Organization.slug == new_slug)
            )
            if result.scalar_one_or_none():
                print(f"✗ Slug '{new_slug}' is already in use")
                sys.exit(1)
            
            old_slug = org.slug
            org.slug = new_slug
            changes.append(f"slug: '{old_slug}' → '{new_slug}'")
        
        # Update active status
        if activate and not org.is_active:
            org.is_active = True
            changes.append("status: inactive → active")
        elif deactivate and org.is_active:
            org.is_active = False
            changes.append("status: active → inactive")
        
        if not changes:
            print("No changes to apply")
            sys.exit(0)
        
        print(f"Organization: {before_state['name']} ({before_state['slug']})")
        print(f"\nChanges to apply:")
        for change in changes:
            print(f"  - {change}")
        
        confirm = input("\nProceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            sys.exit(0)
        
        # Create audit log
        audit = AuditLog(
            organization_id=org.id,
            user_id=None,
            performed_by="system_owner_script",
            entity_type="organization",
            entity_id=org.id,
            action="update",
            before=before_state,
            after={
                "name": org.name,
                "slug": org.slug,
                "is_active": org.is_active
            }
        )
        db.add(audit)
        
        await db.commit()
        
        print(f"\n✓ Organization updated successfully")
        print(f"\nNew state:")
        print(f"  Name: {org.name}")
        print(f"  Slug: {org.slug}")
        print(f"  Status: {'Active' if org.is_active else 'Inactive'}")


def main():
    parser = argparse.ArgumentParser(
        description="Update organization properties (System Owner only)"
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Current organization slug"
    )
    parser.add_argument(
        "--name",
        help="New organization name"
    )
    parser.add_argument(
        "--new-slug",
        help="New organization slug"
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Activate organization"
    )
    parser.add_argument(
        "--deactivate",
        action="store_true",
        help="Deactivate organization"
    )
    
    args = parser.parse_args()
    
    if args.activate and args.deactivate:
        print("✗ Cannot specify both --activate and --deactivate")
        sys.exit(1)
    
    asyncio.run(update_organization(
        slug=args.slug,
        new_name=args.name,
        new_slug=args.new_slug,
        activate=args.activate,
        deactivate=args.deactivate
    ))


if __name__ == "__main__":
    main()