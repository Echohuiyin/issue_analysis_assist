#!/usr/bin/env python3
"""
批量获取内核案例脚本
目标：获取至少1000个内核相关案例
"""
import os
import sys
import time

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.acquisition.main import CaseAcquisition

# 扩展的内核相关关键词列表
EXTENDED_KEYWORDS = [
    # 基础内核错误
    "kernel panic",
    "kernel oops",
    "kernel deadlock",
    "kernel null pointer dereference",
    "kernel OOM",
    "kernel page allocation failure",
    
    # 内核模块问题
    "module init failed",
    "module unload error",
    "insmod failed",
    "rmmod failed",
    "kernel module development",
    
    # 设备驱动问题
    "device driver not found",
    "driver initialization failed",
    "kernel driver crash",
    "driver ioctl failed",
    "driver probe failed",
    
    # 内存管理
    "kernel memory leak",
    "slab corruption",
    "page fault",
    "vmalloc failed",
    "kmem_cache_alloc",
    "page reclaim failure",
    
    # 文件系统
    "filesystem corruption",
    "ext4 error",
    "btrfs error",
    "mount failed",
    "fsck error",
    "block device error",
    
    # 网络相关
    "network card not working",
    "tcp stack error",
    "udp socket error",
    "netfilter iptables",
    "socket bind failed",
    "network timeout",
    
    # 编译问题
    "kernel compile error",
    "kernel build failed",
    "kconfig error",
    "make menuconfig failed",
    "gcc version mismatch",
    "linker error",
    
    # 性能问题
    "high cpu usage",
    "system hang",
    "slow system",
    "context switch high",
    "interrupt storm",
    "soft lockup",
    
    # 硬件相关
    "hardware interrupt",
    "PCI device not detected",
    "USB device error",
    "SATA controller error",
    "DMA error",
    "IRQ conflict",
    
    # 安全相关
    "kernel vulnerability",
    "CVE kernel",
    "privilege escalation",
    "buffer overflow",
    "use after free",
    
    # 调试相关
    "kernel debug",
    "gdb kernel",
    "crash utility",
    "kdump",
    "sysrq-trigger",
    "ftrace"
]

def main():
    print("=" * 70)
    print("批量内核案例获取脚本")
    print("=" * 70)
    print(f"准备获取案例，关键词数量: {len(EXTENDED_KEYWORDS)}")
    print(f"数据源: StackOverflow, CSDN, 知乎, 掘金")
    print()
    
    # 初始化获取器
    acquisition = CaseAcquisition()
    
    # 第一次运行：使用所有关键词，每个关键词每个数据源获取5个案例
    print("第一次获取：")
    print("- 每个关键词每个数据源获取5个案例")
    print(f"- 预计获取: {len(EXTENDED_KEYWORDS) * 4 * 5} 个案例")
    print()
    
    results = acquisition.run(
        keywords=EXTENDED_KEYWORDS,
        max_per_keyword=5,
        sources=["stackoverflow", "csdn", "zhihu", "juejin"]
    )
    
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n第一次获取完成: 成功 {success_count} 个案例")
    print()
    
    # 第二次运行：使用更多关键词变体，每个关键词每个数据源获取3个案例
    print("第二次获取：")
    print("- 使用更多关键词变体")
    print("- 每个关键词每个数据源获取3个案例")
    print()
    
    # 创建关键词变体
    keyword_variants = [
        f"linux {kw}" for kw in EXTENDED_KEYWORDS[:40]  # 前40个关键词加linux前缀
    ]
    
    results2 = acquisition.run(
        keywords=keyword_variants,
        max_per_keyword=3,
        sources=["stackoverflow", "csdn", "zhihu", "juejin"]
    )
    
    success_count2 = sum(1 for r in results2 if r.get("success"))
    print(f"\n第二次获取完成: 成功 {success_count2} 个案例")
    print()
    
    # 统计总数
    total_success = success_count + success_count2
    print("=" * 70)
    print(f"获取完成！")
    print(f"- 总共成功获取: {total_success} 个案例")
    print(f"- 来自 {len(EXTENDED_KEYWORDS) + len(keyword_variants)} 个关键词")
    print("=" * 70)

if __name__ == "__main__":
    main()