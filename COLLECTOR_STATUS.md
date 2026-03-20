# Background Collector Status

## ✅ Current Status

**Process Information:**
- **PID**: 3243205
- **Status**: Running (Sl - sleeping, multi-threaded)
- **Runtime**: 7+ minutes
- **Log file**: /var/log/collector.log

**Database Progress:**
- **Training cases**: 203
- **Test cases**: 57
- **Total cases**: 260
- **Target**: 1000+ cases
- **Progress**: 26.0%
- **Remaining**: 740 cases

## 📊 Collection Strategy

The collector runs in continuous cycles:
1. **High-Quality Case Collection** (30 cases per source)
   - Git fix commits
   - CVE database
   - Kernel documentation

2. **Real Case Collection** (10 cases per source)
   - LKML (Linux Kernel Mailing List)
   - Kernel Bugzilla

3. **Cycle interval**: 5 minutes between cycles

4. **Auto-stop**: When 1000+ cases are collected

## 🔧 Management Commands

### Monitor the collector
```bash
# Quick status check
./monitor_collector.sh

# View live log (when buffered)
tail -f /var/log/collector.log

# Check process status
ps -p $(cat /tmp/collector.pid) -o pid,stat,etime,cmd

# Check database progress
python3 -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()
from cases.models import TrainingCase, TestCase
total = TrainingCase.objects.count() + TestCase.objects.count()
print(f'Total cases: {total}/1000 ({total/10:.1f}%)')
"
```

### Stop the collector
```bash
# Graceful stop
kill $(cat /tmp/collector.pid)

# Force stop (if needed)
kill -9 $(cat /tmp/collector.pid)
```

### Restart the collector
```bash
# Stop existing
kill $(cat /tmp/collector.pid) 2>/dev/null

# Start new
cd /home/lmr/project/issue_analysis_assist
nohup python3 run_background_collector.py > /dev/null 2>&1 &
echo $! > /tmp/collector.pid
echo "Collector restarted with PID: $(cat /tmp/collector.pid)"
```

## 📝 Log File

The log file `/var/log/collector.log` contains:
- Collection cycle progress
- Number of cases collected per source
- Database statistics
- Error messages (if any)

Note: Log output is buffered and may take a few minutes to appear.

## 🎯 Expected Timeline

Based on current collection rate:
- **Current**: 260 cases (26%)
- **Per cycle**: ~30-50 new cases
- **Cycles needed**: ~15-25 cycles
- **Estimated time**: 1-2 hours to reach 1000+ cases

## ✅ Success Indicators

The collector is working correctly when:
1. ✅ Process is running (PID exists)
2. ✅ Database count is increasing
3. ✅ Log file is being written (after buffering)
4. ✅ No error messages in log

## 🚨 Troubleshooting

### If collector stops unexpectedly:
```bash
# Check for errors
tail -100 /var/log/collector.log

# Check system resources
ps aux | grep run_background_collector

# Restart if needed
./restart_collector.sh
```

### If log file is empty:
- Normal behavior (Python logging is buffered)
- Wait 5-10 minutes for buffer to flush
- Or check database directly for progress

---

**Status**: ✅ Collector running successfully
**Last updated**: 2026-03-20 16:21