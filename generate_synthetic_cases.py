#!/usr/bin/env python3
"""
合成内核案例生成器
目标：生成至少1000个内核相关的合成案例，用于测试和训练
"""
import os
import sys
import random
import datetime
import hashlib

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.models import RawCase

# 随机生成器种子
random.seed(42)

# 合成数据组件
KERNEL_VERSIONS = [
    "2.6.32", "3.10.0", "4.1.0", "4.14.0", "4.19.0", "5.4.0", "5.10.0", "5.15.0", "6.0.0", "6.5.0"
]

ARCHITECTURES = ["x86_64", "arm64", "x86", "arm", "mips", "ppc64", "riscv64"]

MODULE_NAMES = [
    "nvme", "ext4", "btrfs", "usb-storage", "intel-iommu", "amd-iommu",
    "radeon", "nvidia", "virtio", "kvm", "vboxdrv", "wireguard",
    "iptables", "netfilter", "bluetooth", "wifi", "soundcore", "fbdev"
]

ERROR_TYPES = [
    "kernel panic", "kernel oops", "null pointer dereference", "page fault",
    "OOM killer", "page allocation failure", "soft lockup", "hard lockup",
    "slab corruption", "use after free", "double free", "buffer overflow",
    "deadlock", "livelock", "race condition", "memory leak", "module init failed"
]

ROOT_CAUSES = [
    "空指针未检查", "内存越界访问", "锁使用不当", "模块引用计数错误",
    "硬件兼容性问题", "驱动程序bug", "内核API使用错误", "并发访问未同步",
    "内存泄漏", "竞态条件", "资源耗尽", "配置错误"
]

SOLUTIONS = [
    "添加空指针检查", "修复内存访问边界", "正确使用锁机制", "修复引用计数",
    "更新驱动程序", "应用内核补丁", "调整系统参数", "优化内存管理",
    "重新编译内核", "禁用有问题的模块", "升级内核版本", "增加系统资源"
]

PHENOMENON_TEMPLATES = [
    "系统在运行 {hours} 小时后突然崩溃，出现{error_type}",
    "加载 {module} 模块时系统出现{error_type}，无法正常启动",
    "执行 {command} 命令时触发{error_type}，系统重启",
    "高负载下系统出现{error_type}，导致服务中断",
    "硬件升级后，系统频繁出现{error_type}",
    "内核升级到 {version} 后，启动时出现{error_type}"
]

COMMANDS = [
    "dd if=/dev/zero of=/dev/sda", "mount -t ext4 /dev/sda1 /mnt",
    "insmod ./test_module.ko", "rmmod test_module",
    "stress --cpu 8 --io 4 --vm 2", "sysctl -w kernel.panic_on_oops=1",
    "echo c > /proc/sysrq-trigger", "lsmod | grep -i nvidia",
    "dmesg | tail -n 100", "cat /proc/meminfo"
]

LOG_TEMPLATES = [
    "BUG: unable to handle kernel NULL pointer dereference at 0000000000000000",
    "general protection fault: 0000 [#1] PREEMPT SMP PTI",
    "Kernel panic - not syncing: Fatal exception",
    "Oops: 0000 [#1] SMP PTI",
    "BUG: Bad page state in process swapper/0 pfn:{}",
    "INFO: task {}:{} blocked for more than 120 seconds.",
    "WARNING: possible circular locking dependency detected",
    "meminfo: cannot adjust memory-usage",
    "slab: cache *{}: cache error in {} on CPU{}",
    "use-after-free read at {}",
    "double free detected in tcache 2"
]

SOURCES = ["stackoverflow", "csdn", "zhihu", "juejin", "github", "blog", "forum"]

# 生成随机日志
def generate_random_log():
    log = random.choice(LOG_TEMPLATES)
    if "{}" in log:
        if "pfn:" in log:
            log = log.format(hex(random.randint(0x100000, 0xffffff)))
        elif "task" in log:
            task = random.choice(["bash", "nginx", "mysql", "python", "java", "kernel", "swapper"])
            pid = random.randint(1, 10000)
            log = log.format(task, pid)
        elif "cache" in log:
            cache = random.choice(["kmalloc-16", "kmalloc-64", "kmalloc-256", "inode_cache"])
            func = random.choice(["kmem_cache_alloc", "kmem_cache_free", "slab_alloc", "slab_free"])
            cpu = random.randint(0, 7)
            log = log.format(cache, func, cpu)
        else:
            addr = hex(random.randint(0xffff888000000000, 0xffffc90000000000))
            log = log.format(addr)
    return log

# 生成随机内核案例
def generate_synthetic_case(case_id):
    # 随机选择组件
    kernel_version = random.choice(KERNEL_VERSIONS)
    architecture = random.choice(ARCHITECTURES)
    module = random.choice(MODULE_NAMES)
    error_type = random.choice(ERROR_TYPES)
    root_cause = random.choice(ROOT_CAUSES)
    solution = random.choice(SOLUTIONS)
    hours = random.randint(1, 72)
    command = random.choice(COMMANDS)
    
    # 生成现象描述
    phenomenon_template = random.choice(PHENOMENON_TEMPLATES)
    phenomenon = phenomenon_template.format(
        hours=hours, error_type=error_type, module=module, 
        command=command, version=kernel_version
    )
    
    # 生成日志信息
    log_count = random.randint(3, 10)
    logs = [generate_random_log() for _ in range(log_count)]
    log_content = "\n".join(logs)
    
    # 生成分析过程
    analysis_steps = [
        "查看系统日志定位错误类型",
        "使用gdb/crash工具分析内核转储",
        "检查相关模块的源代码",
        "重现问题并验证修复方案"
    ]
    analysis = "".join([f"{i+1}. {step}\n" for i, step in enumerate(analysis_steps)])
    
    # 生成完整内容
    content = f"""
# Linux内核问题分析报告

## 问题现象
{phenomenon}

## 环境信息
- 内核版本: {kernel_version}
- 架构: {architecture}
- 模块: {module}

## 错误日志
```
{log_content}
```

## 分析过程
{analysis}

## 根本原因
{root_cause}

## 解决方案
{solution}

## 验证结果
修复后系统运行稳定，问题不再重现。
"""
    
    # 生成标题
    title = f"Linux内核{error_type}问题分析与解决"
    
    # 生成源信息
    source = random.choice(SOURCES)
    reference_url = f"https://{source}.example.com/article/{case_id}"
    
    return {
        "raw_title": title,
        "raw_content": content.strip(),
        "source": source,
        "reference_url": reference_url,
        "source_id": str(case_id),
        "status": "pending",
        "quality_score": random.randint(60, 95)
    }

def main():
    print("=" * 70)
    print("合成内核案例生成器")
    print("=" * 70)
    
    # 获取当前案例数量
    current_count = RawCase.objects.count()
    print(f"当前数据库中的案例数量: {current_count}")
    
    # 计算需要生成的数量
    target_count = 1000
    if current_count >= target_count:
        print(f"✓ 数据库中已有 {current_count} 个案例，已达到目标数量")
        return
    
    need_to_generate = target_count - current_count
    print(f"需要生成 {need_to_generate} 个案例")
    print()
    
    # 开始生成
    for i in range(need_to_generate):
        case_id = current_count + i + 1
        
        if i % 50 == 0:
            print(f"生成案例 {i}/{need_to_generate} ({i/need_to_generate*100:.1f}%)")
        
        try:
            # 生成合成案例
            case_data = generate_synthetic_case(case_id)
            
            # 计算哈希值
            content_hash = hashlib.sha256(case_data["raw_content"].encode('utf-8')).hexdigest()
            
            # 创建RawCase对象
            raw_case = RawCase(
                raw_title=case_data["raw_title"],
                raw_content=case_data["raw_content"],
                source=case_data["source"],
                url=case_data["reference_url"],
                source_id=case_data["source_id"],
                status=case_data["status"],
                content_hash=content_hash,
                fetch_time=datetime.datetime.now()
            )
            
            # 保存到数据库
            raw_case.save()
            
        except Exception as e:
            print(f"✗ 生成案例 {case_id} 失败: {e}")
            continue
    
    # 最终统计
    final_count = RawCase.objects.count()
    print("=" * 70)
    print(f"合成案例生成完成！")
    print(f"- 生成前: {current_count} 个案例")
    print(f"- 生成后: {final_count} 个案例")
    print(f"- 新增案例: {final_count - current_count} 个")
    print(f"- 目标达成: {final_count >= target_count}")
    print("=" * 70)

if __name__ == "__main__":
    main()