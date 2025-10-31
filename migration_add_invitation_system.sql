-- Migration: Add invitation system to support_team_members table
-- This migration adds invitation tracking fields to the support_team_members table

-- Step 1: Add new columns
ALTER TABLE support_team_members 
ADD COLUMN invitation_token VARCHAR(100) UNIQUE,
ADD COLUMN invitation_expires_at TIMESTAMP,
ADD COLUMN accepted_at TIMESTAMP;

-- Step 2: Update status column default (existing rows will keep their current status)
ALTER TABLE support_team_members 
ALTER COLUMN status SET DEFAULT 'pending';

-- Step 3: Create index on invitation_token for faster lookups
CREATE INDEX idx_support_team_invitation_token ON support_team_members(invitation_token);

-- Step 4: Update existing active members (optional - run only if you want to mark existing members as accepted)
-- UPDATE support_team_members 
-- SET status = 'active', 
--     accepted_at = created_at 
-- WHERE status = 'active' AND accepted_at IS NULL;

-- Rollback (if needed):
-- ALTER TABLE support_team_members 
-- DROP COLUMN invitation_token,
-- DROP COLUMN invitation_expires_at,
-- DROP COLUMN accepted_at;
-- DROP INDEX IF EXISTS idx_support_team_invitation_token;

