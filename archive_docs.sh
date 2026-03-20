#!/bin/bash
# Archive old documentation files

echo "Starting documentation cleanup..."

# Create archive directory
mkdir -p archived_docs

# Archive RAG phase reports
echo "Archiving RAG phase reports..."
mv RAG_PHASE1_COMPLETION_REPORT.md archived_docs/ 2>/dev/null
mv RAG_PHASE2_COMPLETION_REPORT.md archived_docs/ 2>/dev/null
mv RAG_PHASE3_COMPLETION_REPORT.md archived_docs/ 2>/dev/null
mv RAG_PHASE4_COMPLETION_REPORT.md archived_docs/ 2>/dev/null

# Archive RAG duplicate docs
echo "Archiving duplicate RAG docs..."
mv RAG_PROJECT_COMPLETE.md archived_docs/ 2>/dev/null
mv RAG_PROJECT_COMPLETE_REPORT.md archived_docs/ 2>/dev/null
mv RAG_FINAL_SUMMARY.md archived_docs/ 2>/dev/null
mv RAG_QUICK_START.md archived_docs/ 2>/dev/null
mv RAG_API_DOCUMENTATION.md archived_docs/ 2>/dev/null
mv RAG_DEVELOPMENT_PLAN.md archived_docs/ 2>/dev/null
mv RAG_SYSTEM_STATUS.md archived_docs/ 2>/dev/null

# Archive session summaries
echo "Archiving session summaries..."
mv COMPLETE_SESSION_SUMMARY_20260319.md archived_docs/ 2>/dev/null
mv SESSION_SUMMARY_20260319.md archived_docs/ 2>/dev/null

# Archive progress reports
echo "Archiving progress reports..."
mv CURRENT_PROGRESS_SUMMARY.md archived_docs/ 2>/dev/null
mv CURRENT_TASK_STATUS.md archived_docs/ 2>/dev/null
mv PROGRESS_UPDATE_20260316_1901.md archived_docs/ 2>/dev/null
mv SYSTEM_STATUS_REPORT_20260316_1903.md archived_docs/ 2>/dev/null
mv TASK_COMPLETION_SUMMARY.md archived_docs/ 2>/dev/null
mv TASK_EXECUTION_SUMMARY.md archived_docs/ 2>/dev/null
mv TASK_PRIORITY_LIST.md archived_docs/ 2>/dev/null

# Archive processing reports
echo "Archiving processing reports..."
mv PROCESSING_COMPLETE_REPORT.md archived_docs/ 2>/dev/null
mv LLM_PARSING_REPORT.md archived_docs/ 2>/dev/null
mv QUALITY_THRESHOLD_ADJUSTMENT_REPORT.md archived_docs/ 2>/dev/null
mv SHORT_TERM_OPTIMIZATIONS_REPORT.md archived_docs/ 2>/dev/null
mv FINAL_REPORT_20260317.md archived_docs/ 2>/dev/null

# Archive collection reports
echo "Archiving collection reports..."
mv HIGH_QUALITY_CASE_COLLECTION_PLAN.md archived_docs/ 2>/dev/null
mv REAL_CASES_COLLECTION_PLAN.md archived_docs/ 2>/dev/null
mv STACKOVERFLOW_COLLECTION_COMPLETE.md archived_docs/ 2>/dev/null
mv FAILED_CASES_REPROCESSING_REPORT.md archived_docs/ 2>/dev/null

# Archive deployment guides (merged into DEPLOYMENT_GUIDE.md)
echo "Archiving old deployment guides..."
mv LOCAL_LLM_DEPLOYMENT.md archived_docs/ 2>/dev/null
mv OLLAMA_CPU_DEPLOYMENT.md archived_docs/ 2>/dev/null
mv VLLM_CPU_DEPLOYMENT.md archived_docs/ 2>/dev/null
mv LLM_ENGINE_SELECTION.md archived_docs/ 2>/dev/null
mv LLM_PARSER_GUIDE.md archived_docs/ 2>/dev/null

# Create archive index
echo "Creating archive index..."
cat > archived_docs/README.md << 'EOF'
# Archived Documentation

This directory contains archived documentation files that have been consolidated into newer, more comprehensive documents.

## Consolidated Documentation

The following consolidated documents replace the archived files:

1. **RAG_SYSTEM.md** - Complete RAG system documentation
   - Replaces: RAG_PROJECT_COMPLETE.md, RAG_FINAL_SUMMARY.md, RAG_API_DOCUMENTATION.md, etc.
   
2. **DEPLOYMENT_GUIDE.md** - Complete deployment guide
   - Replaces: LOCAL_LLM_DEPLOYMENT.md, OLLAMA_CPU_DEPLOYMENT.md, VLLM_CPU_DEPLOYMENT.md, etc.

3. **PROGRESS_TRACKING.md** - Comprehensive progress tracking
   - Replaces: All session summaries and progress reports

4. **COLLECTOR_STATUS.md** - Current collector status
   - Replaces: Collection plan documents

## Archive Date
- **Date**: 2026-03-20
- **Reason**: Documentation cleanup and consolidation

## Note
These files are kept for historical reference. For current information, refer to the consolidated documentation in the main directory.
EOF

echo "Documentation cleanup complete!"
echo ""
echo "Archived files:"
ls -1 archived_docs/*.md 2>/dev/null | wc -l
echo ""
echo "Consolidated documentation created:"
echo "  - RAG_SYSTEM.md"
echo "  - DEPLOYMENT_GUIDE.md"