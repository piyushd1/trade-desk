#!/bin/bash

# Project Cleanup Script
# Removes outdated and redundant files

set -e

echo "🧹 Starting project cleanup..."
echo ""

# Create backup directory for safety
BACKUP_DIR=".cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Backup directory: $BACKUP_DIR"
echo ""

# Function to safely remove files
safe_remove() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "  Removing: $file"
        cp "$file" "$BACKUP_DIR/" 2>/dev/null || true
        rm "$file"
    fi
}

# 1. Remove all old test result files
echo "🗑️  Removing old test result files..."
for file in *_test_*.md; do
    if [ -f "$file" ]; then
        safe_remove "$file"
    fi
done
echo ""

# 2. Remove duplicate/redundant documentation
echo "🗑️  Removing duplicate/redundant documentation..."
safe_remove "STREAMING_API_FIX.md"
safe_remove "ZERODHA_API_EXPLORATION.md"
safe_remove "day_1_work.md"
safe_remove "day_2_work.md"
echo ""

# 3. Remove completed migration/setup docs (can be archived)
echo "🗑️  Removing completed migration/setup docs..."
safe_remove "JWT_MIGRATION_PLAN.md"
safe_remove "JWT_MIGRATION_COMPLETE.md"
safe_remove "SSL_SETUP_COMPLETE.md"
safe_remove "GCP_FIREWALL_SETUP.md"
safe_remove "AUTH_SUMMARY_AND_NEXT_STEPS.md"
echo ""

# 4. Remove outdated status/planning docs
echo "🗑️  Removing outdated status/planning docs..."
safe_remove "STATUS_CHECK.md"
safe_remove "TESTING_STATUS.md"
safe_remove "REMAINING_WORK.md"
safe_remove "REMAINING_ENDPOINTS_TESTING.md"
safe_remove "NEXT_API_TESTING.md"
safe_remove "PHASE2_PROGRESS.md"
echo ""

# 5. Remove superseded testing guides
echo "🗑️  Removing superseded testing guides..."
safe_remove "FINAL_TESTING_GUIDE.md"
safe_remove "TESTING_STEPS.md"
safe_remove "ZERODHA_TESTING_GUIDE.md"
safe_remove "API_TESTING_PLAN.md"
echo ""

# 6. Remove redundant summary docs (consolidated into DAY_4_WORK.md)
echo "🗑️  Removing redundant summary docs..."
safe_remove "API_FIXES_SUMMARY.md"
safe_remove "STREAMING_UPDATE_FIX.md"
safe_remove "SWAGGER_UI_FIX.md"
safe_remove "STREAMING_API_FIX_FINAL.md"
echo ""

# 7. Check and remove potentially outdated scripts
echo "🗑️  Checking potentially outdated scripts..."
# Keep these for now, but list them
echo "  Note: Review these scripts manually:"
echo "    - QUICK_TEST.sh"
echo "    - test_zerodha_complete.sh"
echo "    - test_oauth_flow.sh"
echo "    - test_audit_logging.sh"
echo "    - test_auth_me.sh"
echo "    - test_risk_api.sh"
echo ""

# 8. Check MASTER_REFERENCE.md and BACKEND_REFACTORING_SUMMARY.md
echo "⚠️  Files to review manually:"
echo "    - MASTER_REFERENCE.md (check if still needed)"
echo "    - BACKEND_REFACTORING_SUMMARY.md (check if still needed)"
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Backup location: $BACKUP_DIR"
echo "  - Files removed: $(ls -1 "$BACKUP_DIR" 2>/dev/null | wc -l)"
echo ""
echo "💡 To restore any file:"
echo "  cp $BACKUP_DIR/<filename> ./<filename>"
echo ""

