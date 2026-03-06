import re
from typing import Dict, List


class ModuleClassifier:
    """Kernel module classifier based on keyword matching.
    
    Classifies text into one of the following kernel modules:
    - memory: Memory Management
    - network: Network
    - scheduler: Scheduler
    - lock: Lock/Synchronization
    - timer: Timer
    - storage: Storage/Filesystem
    - irq: Interrupt
    - driver: Device Driver
    - other: Other
    """

    # Module keywords configuration
    # Higher weight for more specific keywords
    MODULE_KEYWORDS: Dict[str, List[str]] = {
        "memory": [
            # Core memory terms
            "memory", "mem", "kmalloc", "vmalloc", "slab", "page", "swap",
            "oom", "out of memory", "memory leak", "page fault", "mmap",
            "malloc", "free", "allocator", "buddy", "vmalloc", "kmem_cache",
            # Chinese terms
            "内存", "内存泄漏", "内存不足", "页面错误", "交换区", "内存分配",
            "页表", "slab分配器", "伙伴系统", "OOM"
        ],
        "network": [
            # Core network terms
            "network", "net", "tcp", "udp", "socket", "ip", "nic", "ethernet",
            "driver", "interface", "packets", "skb", "network stack", "route",
            "iptables", "netfilter", "bridge", "vlan", "ndis", "wifi", "connection", "connect", "timeout",
            # Chinese terms
            "网络", "TCP", "UDP", "套接字", "网卡", "数据包", "网络栈",
            "路由", "防火墙", "桥接", "VLAN", "连接", "超时"
        ],
        "scheduler": [
            # Core scheduler terms
            "schedule", "scheduler", "task", "process", "thread", "cpu",
            "cfs", "rt", "real-time", "priority", "nice", "load", "context switch",
            "wakeup", "sleep", "wait", "task_struct", "runqueue",
            # Chinese terms
            "调度", "进程", "线程", "CPU", "优先级", "实时", "上下文切换",
            "调度器", "运行队列"
        ],
        "lock": [
            # Core lock terms
            "lock", "mutex", "spinlock", "rwlock", "rcu", "semaphore", "mutex",
            "deadlock", "contention", "spin", "lockup", "atomic", "critical section",
            "unlock", "acquire", "release", "spin_lock", "spin_unlock",
            # Chinese terms
            "锁", "互斥锁", "自旋锁", "读写锁", "RCU", "信号量", "死锁",
            "锁竞争", "临界区", "软锁", "硬锁", "spinlock死锁"
        ],
        "timer": [
            # Core timer terms
            "timer", "hrtimer", "tick", "delay", "timeout", "jiffies", "timekeeping",
            "watchdog", "alarm", "schedule_timeout", "mod_timer", "del_timer",
            # Chinese terms
            "定时器", "超时", "延迟", "滴答", "时钟", "看门狗"
        ],
        "storage": [
            # Core storage terms
            "storage", "disk", "fs", "filesystem", "block", "io", "mount",
            "ext4", "xfs", "btrfs", "ntfs", "fat", "vfs", "inode", "block device",
            "driver", "scsi", "sata", "nvme", "raid", "lvm", "dm", "disk quota",
            # Chinese terms
            "存储", "磁盘", "文件系统", "块设备", "IO", "挂载", "分区",
            "驱动", "SCSI", "SATA", "NVMe", "RAID", "LVM"
        ],
        "irq": [
            # Core IRQ terms
            "irq", "interrupt", "irq handler", "softirq", "tasklet", "workqueue",
            "irqbalance", "irqchip", "msi", "interrupt controller", "irq line",
            "disable_irq", "enable_irq", "request_irq",
            # Chinese terms
            "中断", "软中断", "任务队列", "IRQ", "中断处理程序", "中断控制器"
        ],
        "driver": [
            # Core driver terms
            "driver", "device", "driver model", "probe", "remove", "init",
            "exit", "device tree", "platform", "pci", "usb", "i2c", "spi",
            "driver_register", "driver_unregister", "module_init", "module_exit",
            # Chinese terms
            "驱动", "设备", "驱动模型", "探测", "移除", "初始化", "设备树",
            "PCI", "USB", "I2C", "SPI"
        ]
    }

    def __init__(self):
        self.module_choices = list(self.MODULE_KEYWORDS.keys()) + ["other"]

    def classify_module(self, text: str) -> str:
        """Classify text into a kernel module based on keyword matching.
        
        Args:
            text: The text to classify (usually problem description, analysis, etc.)
            
        Returns:
            str: The classified module name (one of the MODULE_KEYWORDS keys or "other")
        """
        if not text or not isinstance(text, str):
            return "other"

        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()

        # Count keyword matches for each module
        module_scores = {}
        for module, keywords in self.MODULE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # For English words, use word boundary matching
                if all(ord(c) < 128 for c in keyword):
                    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    matches = re.findall(pattern, text_lower)
                    score += len(matches)
                # For Chinese words or mixed, use substring matching
                else:
                    score += text_lower.count(keyword_lower)
            module_scores[module] = score

        # Find module with highest score
        if module_scores:
            best_module = max(module_scores, key=module_scores.get)
            # Only return the best module if it has at least one match
            if module_scores[best_module] > 0:
                return best_module

        # Default to "other" if no matches found
        return "other"

    def get_module_keywords(self, module: str) -> List[str]:
        """Get keywords for a specific module.
        
        Args:
            module: The module name
            
        Returns:
            List[str]: List of keywords for the module
        """
        return self.MODULE_KEYWORDS.get(module, [])

    def validate_module(self, module: str) -> bool:
        """Check if a module name is valid.
        
        Args:
            module: The module name to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        return module in self.module_choices


# Singleton instance for easy reuse
module_classifier = ModuleClassifier()