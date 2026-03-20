#!/bin/bash
# Monitor the background collector

echo "=========================================="
echo "Background Collector Monitor"
echo "=========================================="
echo ""

# Check if process is running
PID=$(cat /tmp/collector.pid 2>/dev/null)
if [ -n "$PID" ]; then
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Collector is running"
        echo "   PID: $PID"
        ps -p $PID -o pid,stat,etime,cmd | tail -1
    else
        echo "❌ Collector process not found (PID: $PID)"
    fi
else
    echo "❌ No PID file found"
fi

echo ""
echo "=========================================="
echo "Database Status"
echo "=========================================="

# Check database
python3 -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()
from cases.models import TrainingCase, TestCase
training = TrainingCase.objects.count()
test = TestCase.objects.count()
total = training + test
print(f'Training cases: {training}')
print(f'Test cases:     {test}')
print(f'Total:          {total}')
print(f'Target:         1000+ cases')
print(f'Progress:       {total/10:.1f}%')
print(f'Remaining:      {max(0, 1000-total)} cases')
"

echo ""
echo "=========================================="
echo "Log File (last 20 lines)"
echo "=========================================="

if [ -f /var/log/collector.log ]; then
    LOG_SIZE=$(wc -l < /var/log/collector.log)
    echo "Log file size: $LOG_SIZE lines"
    echo ""
    if [ $LOG_SIZE -gt 0 ]; then
        tail -20 /var/log/collector.log
    else
        echo "Log file is empty (buffered)"
    fi
else
    echo "Log file not found"
fi

echo ""
echo "=========================================="
echo "Management Commands"
echo "=========================================="
echo "View live log:     tail -f /var/log/collector.log"
echo "Stop collector:    kill \$(cat /tmp/collector.pid)"
echo "Restart collector: python3 run_background_collector.py &"
echo "=========================================="