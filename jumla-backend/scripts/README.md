# Jumla-bot System Owner Scripts

System Owner scripts for organization and user management. These scripts require system owner privileges and should be run from a secure environment.

## Prerequisites

```bash
# Ensure you're in the project root
cd /path/to/jumla-bot

# Activate virtual environment
source venv/bin/activate  # or your venv activation command

# Install dependencies (if not already done)
pip install -r requirements.txt
```

## Initial Setup

### 1. Run Database Migrations

```bash
alembic upgrade head
```

### 2. Create System Owner Account (ONE TIME ONLY)

```bash
python scripts/create_system_owner.py
```

This creates the root account with god-mode access. **Run this only once during initial deployment.**

## Organization Management

### Create Organization

Create a new organization with a primary admin:

```bash
python scripts/create_organization.py \
  --name "ABC Home Buyers LLC" \
  --slug "abc-home-buyers" \
  --admin-email "alice@abchomes.com" \
  --admin-fullname "Alice Admin"
```

**Optional**: Specify admin password (otherwise a temporary password is generated):

```bash
python scripts/create_organization.py \
  --name "ABC Home Buyers LLC" \
  --slug "abc-home-buyers" \
  --admin-email "alice@abchomes.com" \
  --admin-fullname "Alice Admin" \
  --admin-password "SecureP@ssw0rd"
```

### Update Organization

Update organization properties:

```bash
# Change name
python scripts/update_organization.py \
  --slug "abc-home-buyers" \
  --name "ABC Home Buyers & Investors LLC"

# Change slug
python scripts/update_organization.py \
  --slug "abc-home-buyers" \
  --new-slug "abc-home-buyers-llc"

# Activate organization
python scripts/update_organization.py \
  --slug "abc-home-buyers" \
  --activate

# Deactivate organization
python scripts/update_organization.py \
  --slug "abc-home-buyers" \
  --deactivate
```

### Delete Organization

**Soft delete** (recommended - can be recovered):

```bash
python scripts/delete_organization.py --slug "abc-home-buyers"
```

**Hard delete** (PERMANENT - cannot be undone):

```bash
python scripts/delete_organization.py --slug "abc-home-buyers" --force
```

⚠️ **Warning**: Hard delete permanently removes:
- Organization record
- All users
- All leads, buyers, and related data
- All audit logs

## Admin Management

### Reset Admin Password

Only System Owner can reset admin passwords (emergency recovery):

```bash
python scripts/reset_admin_password.py --email "alice@abchomes.com"
```

Specify new password:

```bash
python scripts/reset_admin_password.py \
  --email "alice@abchomes.com" \
  --new-password "NewSecureP@ss"
```

With audit trail:

```bash
python scripts/reset_admin_password.py \
  --email "alice@abchomes.com" \
  --system-owner "systemowner@jumla.com"
```

### Create Additional Admin (Interactive)

```bash
python scripts/create_admin.py
```

## Security Best Practices

1. **System Owner Credentials**
   - Use a strong password (minimum 12 characters)
   - Store credentials in a secure password manager
   - Never share system owner credentials
   - Use MFA if available

2. **Script Execution**
   - Run scripts from a secure, audited environment
   - Always review changes before confirming
   - Check audit logs after running scripts

3. **Organization Management**
   - Use soft delete unless absolutely necessary
   - Communicate with organization admins before deactivation
   - Keep audit trail of all system owner actions

4. **Password Management**
   - Use generated temporary passwords when possible
   - Share temporary passwords through secure channels
   - Advise users to change temporary passwords immediately

## Audit Logging

All scripts create audit log entries with:
- `performed_by`: "system_owner_script" or system owner email
- `entity_type`: "organization" or "user"
- `action`: "create", "update", "delete", etc.
- `before`: State before action
- `after`: State after action

View audit logs:

```bash
# Via API (requires admin token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/audit-logs

# Or query database directly
psql jumla_bot -c "SELECT * FROM audit_logs WHERE performed_by = 'system_owner_script' ORDER BY created_at DESC LIMIT 10;"
```

## Troubleshooting

### Script fails with "Module not found"

Ensure you're running from project root and PYTHONPATH is set:

```bash
cd /path/to/jumla-bot
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/create_organization.py --help
```

### Database connection error

Check your `.env` file has correct database credentials:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/jumla_bot
```

### "Organization already exists"

Each slug must be unique. Use `--new-slug` to rename existing organization.

## Examples

### Complete Organization Setup

```bash
# 1. Create organization
python scripts/create_organization.py \
  --name "XYZ Realty" \
  --slug "xyz-realty" \
  --admin-email "john@xyzrealty.com" \
  --admin-fullname "John Doe"

# Output will show temporary password
# Share it securely with john@xyzrealty.com

# 2. Admin logs in and creates agents via UI/API
# (This is done through the application, not scripts)
```

### Emergency Admin Recovery

```bash
# Admin forgot password
python scripts/reset_admin_password.py \
  --email "alice@abchomes.com" \
  --system-owner "admin@jumla.com"

# Share new temporary password securely with Alice
```

### Decommission Organization

```bash
# 1. Soft delete (can be recovered)
python scripts/delete_organization.py --slug "old-org"

# 2. If data must be permanently removed
python scripts/delete_organization.py --slug "old-org" --force
```