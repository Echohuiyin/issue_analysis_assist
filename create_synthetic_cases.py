#!/usr/bin/env python3
"""
Create synthetic test cases for SKILL demonstration
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()

from cases.models import TrainingCase, TestCase
from cases.acquisition.vector_service import get_vector_service
import random
import hashlib


def generate_content_hash(title, phenomenon, root_cause):
    """Generate content hash for deduplication"""
    content = f"{title}|{phenomenon}|{root_cause}"
    return hashlib.sha256(content.encode()).hexdigest()


def create_synthetic_cases():
    """Create synthetic test cases"""
    
    test_cases = [
        {
            'title': 'Kernel Panic Due to Memory Corruption in Network Driver',
            'phenomenon': 'System experiences kernel panic with error message "BUG: unable to handle page fault" when transferring large files over network. The crash occurs randomly after 10-30 minutes of heavy network traffic.',
            'key_logs': '[  123.456789] BUG: unable to handle page fault at address 0x00000000\n[  123.456790] IP: my_network_driver_xmit+0x123/0x200\n[  123.456791] Call Trace:\n[  123.456792]  my_network_driver_xmit\n[  123.456793]  dev_queue_xmit',
            'environment': 'Linux kernel 5.15.0, x86_64, 16GB RAM, Custom network driver',
            'root_cause': 'The network driver was using a freed skb (socket buffer) pointer. The driver did not properly manage skb reference counting, leading to use-after-free when the memory was reused by other parts of the kernel.',
            'analysis_process': '1. Analyzed kernel panic log and identified crash location in network driver\n2. Reviewed driver code and found skb handling issues\n3. Used kmemleak to detect memory leaks\n4. Traced skb lifecycle with ftrace',
            'troubleshooting_steps': [
                'Enable kernel debugging and capture full crash dump',
                'Analyze crash location in driver code',
                'Check skb reference counting in driver',
                'Use kmemleak to find memory issues',
                'Add debug logging to track skb lifecycle'
            ],
            'solution': 'Fixed skb reference counting in the network driver. Added proper skb_get() before storing skb pointer and kfree_skb() when done. Also added NULL checks before accessing skb data.',
            'prevention': 'Implement proper reference counting for all shared kernel objects. Use static analysis tools to detect use-after-free bugs. Add memory debugging options during development.',
            'kernel_version': '5.15.0',
            'affected_components': 'Network driver, SKB management',
            'module': 'network',
            'severity': 'Critical',
            'source': 'synthetic',
            'tags': ['kernel-panic', 'memory-corruption', 'network-driver', 'use-after-free']
        },
        {
            'title': 'Memory Leak in Kernel Module Causing OOM',
            'phenomenon': 'System becomes unresponsive after running for several hours. Memory usage continuously increases until OOM killer is triggered. The issue occurs when a custom kernel module is loaded.',
            'key_logs': '[  456.789012] Out of memory: Killed process 1234 (myapp) score 987 or sacrifice child\n[  456.789013] memory: usage 15728640kB, limit 15728640kB, failcnt 12345\n[  456.789014] Slab: my_module_objects 16384KB',
            'environment': 'Linux kernel 5.10.0, x86_64, 16GB RAM, Custom kernel module',
            'root_cause': 'The kernel module was allocating memory for each operation but not freeing it when the operation completed. The memory leak was in the error handling path where allocated memory was not freed on failure.',
            'analysis_process': '1. Monitored memory usage with /proc/meminfo\n2. Identified growing slab cache with slabtop\n3. Traced memory allocations with kmemleak\n4. Reviewed module code for allocation/free pairs',
            'troubleshooting_steps': [
                'Monitor memory usage over time',
                'Check slab cache statistics',
                'Enable kmemleak to detect leaks',
                'Review module memory allocation code',
                'Test with kernel memory debugging enabled'
            ],
            'solution': 'Added proper cleanup in the error handling path. Ensured all allocated memory is freed in both success and failure cases. Added memory tracking to detect future leaks.',
            'prevention': 'Use devm_kzalloc() for device-managed memory when possible. Always implement proper cleanup in error paths. Use static analysis tools to check for memory leaks.',
            'kernel_version': '5.10.0',
            'affected_components': 'Memory management, Kernel module',
            'module': 'memory',
            'severity': 'High',
            'source': 'synthetic',
            'tags': ['memory-leak', 'oom', 'kernel-module', 'slab-cache']
        },
        {
            'title': 'Process Hang Due to Deadlock in Mutex',
            'phenomenon': 'Multiple processes hang indefinitely. System load average increases but CPU usage remains low. Processes are stuck in uninterruptible sleep (D state).',
            'key_logs': '[  789.012345] INFO: task myapp:1234 blocked for more than 120 seconds.\n[  789.012346]       Tainted: P           OE     5.15.0\n[  789.012347] "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.\n[  789.012348] task:myapp         state:D stack:0     pid:1234  ppid:1',
            'environment': 'Linux kernel 5.15.0, x86_64, Multi-core system, Custom application',
            'root_cause': 'ABBA deadlock caused by incorrect mutex locking order. Two threads were acquiring mutexes in opposite order, leading to circular wait condition.',
            'analysis_process': '1. Identified hung processes with ps and top\n2. Analyzed process stack traces with /proc/<pid>/stack\n3. Used lockdep to detect potential deadlocks\n4. Reviewed mutex locking patterns in code',
            'troubleshooting_steps': [
                'Identify hung processes and their state',
                'Capture stack traces of blocked processes',
                'Enable lockdep for deadlock detection',
                'Analyze mutex acquisition order',
                'Review code for locking patterns'
            ],
            'solution': 'Fixed mutex locking order to be consistent across all code paths. Added lockdep annotations to enforce locking order. Implemented timeout-based mutex acquisition where appropriate.',
            'prevention': 'Use lockdep to validate locking patterns. Always acquire locks in consistent order. Consider using lock-free data structures where possible. Add timeout mechanisms for critical locks.',
            'kernel_version': '5.15.0',
            'affected_components': 'Locking subsystem, Process scheduler',
            'module': 'lock',
            'severity': 'High',
            'source': 'synthetic',
            'tags': ['deadlock', 'mutex', 'hang', 'lockdep']
        },
        {
            'title': 'Filesystem Corruption After Power Failure',
            'phenomenon': 'After unexpected power loss, filesystem shows corruption errors. Some files are missing or contain garbage data. fsck reports inode and block bitmap errors.',
            'key_logs': '[  123.456789] EXT4-fs error (device sda1): ext4_find_entry: inode #12345: comm myapp: reading directory\n[  123.456790] EXT4-fs error (device sda1): ext4_validate_block_bitmap: comm myapp: bg 123: bad block bitmap checksum',
            'environment': 'Linux kernel 5.10.0, x86_64, EXT4 filesystem, SSD storage',
            'root_cause': 'Filesystem was mounted without journaling or with insufficient journaling mode. Data was not properly flushed to disk before power loss, leading to metadata inconsistency.',
            'analysis_process': '1. Booted system and checked dmesg for filesystem errors\n2. Ran fsck to identify corruption\n3. Reviewed filesystem mount options\n4. Analyzed journal configuration',
            'troubleshooting_steps': [
                'Check filesystem errors in dmesg',
                'Run fsck in read-only mode first',
                'Review mount options and journal mode',
                'Check disk health with smartctl',
                'Restore from backup if necessary'
            ],
            'solution': 'Remounted filesystem with data=journal mode for critical data. Added UPS to prevent unexpected power loss. Implemented regular filesystem checks and backups.',
            'prevention': 'Use journaling filesystems with appropriate journal mode. Ensure proper shutdown procedures. Implement UPS for critical systems. Schedule regular filesystem checks and backups.',
            'kernel_version': '5.10.0',
            'affected_components': 'EXT4 filesystem, Block layer',
            'module': 'storage',
            'severity': 'Critical',
            'source': 'synthetic',
            'tags': ['filesystem-corruption', 'ext4', 'power-failure', 'data-loss']
        },
        {
            'title': 'High CPU Usage in SoftIRQ Context',
            'phenomenon': 'System shows high CPU usage but no process is consuming CPU. Load average is high. Network throughput is degraded. ksoftirqd processes are consuming significant CPU.',
            'key_logs': '[  456.789012] NOHZ: local_softirq_pending 08\n[  456.789013] ksoftirqd/0     R  running task     1234  1232      1 0x00000008\n[  456.789014]  [<ffffffff81234567>] __do_softirq',
            'environment': 'Linux kernel 5.15.0, x86_64, High network traffic, Custom network driver',
            'root_cause': 'Network driver was scheduling too many softirqs without proper throttling. Each packet triggered a softirq, overwhelming the CPU with interrupt processing.',
            'analysis_process': '1. Identified high CPU usage in ksoftirqd\n2. Traced softirq activity with /proc/softirqs\n3. Used perf to profile softirq handlers\n4. Reviewed network driver interrupt handling',
            'troubleshooting_steps': [
                'Monitor softirq statistics',
                'Profile CPU usage with perf',
                'Check network driver interrupt rate',
                'Analyze NAPI configuration',
                'Review interrupt coalescing settings'
            ],
            'solution': 'Implemented NAPI (New API) in network driver to poll for packets instead of interrupt per packet. Added interrupt coalescing to batch interrupts. Optimized softirq handler.',
            'prevention': 'Use NAPI for high-speed network drivers. Implement interrupt coalescing. Monitor softirq statistics regularly. Test under high load conditions.',
            'kernel_version': '5.15.0',
            'affected_components': 'Network subsystem, SoftIRQ',
            'module': 'network',
            'severity': 'Medium',
            'source': 'synthetic',
            'tags': ['softirq', 'high-cpu', 'network-driver', 'napi']
        }
    ]
    
    print("=" * 60)
    print("ðŸ“ Creating Synthetic Test Cases")
    print("=" * 60)
    
    vector_service = get_vector_service()
    
    for i, case_data in enumerate(test_cases, 1):
        print(f"\nCreating case {i}/{len(test_cases)}: {case_data['title'][:60]}...")
        
        case_data['case_id'] = f'SYN_{i:04d}'
        
        embedding = vector_service.generate_embedding(
            f"{case_data['title']} {case_data['phenomenon']} {case_data['root_cause']}"
        )
        case_data['embedding'] = embedding
        
        if random.random() < 0.8:
            case = TrainingCase(**case_data)
            case_type = 'Training'
        else:
            case = TestCase(**case_data)
            case_type = 'Test'
        
        case.save()
        print(f"  âœ… Created {case_type} case: {case.case_id}")
    
    print("\n" + "=" * 60)
    print("ðŸ“Š Summary")
    print("=" * 60)
    training_count = TrainingCase.objects.count()
    test_count = TestCase.objects.count()
    print(f"Training cases: {training_count}")
    print(f"Test cases: {test_count}")
    print(f"Total: {training_count + test_count}")
    
    return training_count + test_count

if __name__ == '__main__':
    create_synthetic_cases()