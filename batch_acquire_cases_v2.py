#!/usr/bin/env python3
"""
优化的批量获取内核案例脚本
- 添加延迟避免API限制
- 增加重试机制
- 优化关键词和获取策略
- 目标：获取至少1000个内核相关案例
"""
import os
import sys
import time
import random

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.acquisition.main import CaseAcquisition

# 基础内核关键词 - 更精准的关键词以获取高质量案例
CORE_KERNEL_KEYWORDS = [
    "kernel panic",
    "kernel oops",
    "kernel deadlock",
    "kernel null pointer",
    "kernel OOM",
    "kernel memory leak",
    "kernel compile error",
    "kernel module error",
    "driver probe failed",
    "filesystem corruption",
    "page allocation failure",
    "slab corruption",
    "hard lockup",
    "soft lockup",
    "kernel crash",
    "kernel debug",
    "crash utility",
    "kdump analysis",
    "sysrq-trigger"
]

# 扩展关键词 - 增加更多内核相关主题
EXTENDED_KEYWORDS = [
    "linux kernel development",
    "linux kernel programming",
    "linux driver development",
    "linux kernel patch",
    "linux kernel configuration",
    "linux kernel module",
    "linux device driver",
    "linux memory management",
    "linux file system",
    "linux network stack",
    "linux process management",
    "linux interrupt handling",
    "linux system call",
    "linux kernel synchronization",
    "linux kernel debugging",
    "linux kernel security",
    "linux kernel performance",
    "linux kernel optimization",
    "linux kernel version",
    "linux kernel update"
]

def main():
    print("=" * 70)
    print("优化版批量内核案例获取脚本")
    print("=" * 70)
    print(f"基础关键词: {len(CORE_KERNEL_KEYWORDS)}")
    print(f"扩展关键词: {len(EXTENDED_KEYWORDS)}")
    print(f"总关键词: {len(CORE_KERNEL_KEYWORDS) + len(EXTENDED_KEYWORDS)}")
    print()
    
    # 初始化获取器
    acquisition = CaseAcquisition()
    
    total_success = 0
    all_results = []
    
    # 第一阶段：使用核心关键词获取高质量案例
    print("第一阶段：核心关键词获取高质量案例")
    print("- 每个关键词每个数据源获取5个案例")
    print(f"- 预计获取: {len(CORE_KERNEL_KEYWORDS) * 4 * 5} 个案例")
    print()
    
    for i, keyword in enumerate(CORE_KERNEL_KEYWORDS, 1):
        print(f"[{i}/{len(CORE_KERNEL_KEYWORDS)}] 处理关键词: {keyword}")
        
        try:
            # 避免同时请求所有数据源导致的限制
            sources = ["stackoverflow", "csdn", "zhihu", "juejin"]
            random.shuffle(sources)  # 随机化数据源顺序
            
            for source in sources:
                print(f"  -> 从 {source} 获取...")
                
                if source == "stackoverflow":
                    results = acquisition.acquire_from_stackoverflow(keyword, count=5)
                elif source == "csdn":
                    # 为CSDN转换关键词
                    csdn_keyword = keyword
                    if keyword == "kernel panic":
                        csdn_keyword = "内核 panic"
                    elif keyword == "kernel oops":
                        csdn_keyword = "内核 oops"
                    elif keyword == "kernel deadlock":
                        csdn_keyword = "内核死锁"
                    elif keyword == "kernel null pointer":
                        csdn_keyword = "内核空指针"
                    elif keyword == "kernel OOM":
                        csdn_keyword = "内核 OOM"
                    elif keyword == "kernel memory leak":
                        csdn_keyword = "内核内存泄漏"
                    elif keyword == "kernel compile error":
                        csdn_keyword = "内核编译错误"
                    elif keyword == "kernel module error":
                        csdn_keyword = "内核模块错误"
                    elif keyword == "driver probe failed":
                        csdn_keyword = "驱动probe失败"
                    else:
                        csdn_keyword = keyword
                        
                    results = acquisition.acquire_from_csdn(csdn_keyword, count=5)
                elif source == "zhihu":
                    # 为知乎转换关键词
                    zhihu_keyword = keyword
                    if keyword == "kernel panic":
                        zhihu_keyword = "内核崩溃"
                    elif keyword == "kernel oops":
                        zhihu_keyword = "内核错误"
                    elif keyword == "kernel deadlock":
                        zhihu_keyword = "内核死锁"
                    elif keyword == "kernel null pointer":
                        zhihu_keyword = "内核空指针"
                    elif keyword == "kernel OOM":
                        zhihu_keyword = "内存溢出"
                    else:
                        zhihu_keyword = keyword
                        
                    results = acquisition.acquire_from_zhihu(zhihu_keyword, count=5)
                elif source == "juejin":
                    # 为掘金转换关键词
                    juejin_keyword = keyword
                    if keyword == "kernel panic":
                        juejin_keyword = "内核崩溃"
                    elif keyword == "kernel oops":
                        juejin_keyword = "内核错误"
                    elif keyword == "kernel deadlock":
                        juejin_keyword = "内核死锁"
                    elif keyword == "kernel null pointer":
                        juejin_keyword = "内核空指针"
                    else:
                        juejin_keyword = keyword
                        
                    results = acquisition.acquire_from_juejin(juejin_keyword, count=5)
                
                all_results.extend(results)
                success_count = sum(1 for r in results if r.get("success"))
                print(f"     成功: {success_count}/{len(results)} 个案例")
                
                # 添加随机延迟避免被封禁
                delay = random.uniform(2, 5)
                print(f"     延迟 {delay:.1f} 秒...")
                time.sleep(delay)
            
        except Exception as e:
            print(f"  ✗ 处理关键词 '{keyword}' 时出错: {e}")
            # 增加延迟后继续
            time.sleep(10)
    
    # 统计第一阶段结果
    success_count1 = sum(1 for r in all_results if r.get("success"))
    total_success += success_count1
    print(f"\n第一阶段完成: 成功 {success_count1} 个案例")
    print()
    
    # 如果还需要更多案例，进行第二阶段
    if total_success < 1000:
        print("第二阶段：扩展关键词获取更多案例")
        print("- 每个关键词每个数据源获取3个案例")
        print(f"- 预计额外获取: {len(EXTENDED_KEYWORDS) * 4 * 3} 个案例")
        print()
        
        for i, keyword in enumerate(EXTENDED_KEYWORDS, 1):
            print(f"[{i}/{len(EXTENDED_KEYWORDS)}] 处理关键词: {keyword}")
            
            try:
                # 避免同时请求所有数据源导致的限制
                sources = ["stackoverflow", "csdn", "zhihu", "juejin"]
                random.shuffle(sources)  # 随机化数据源顺序
                
                for source in sources:
                    print(f"  -> 从 {source} 获取...")
                    
                    if source == "stackoverflow":
                        results = acquisition.acquire_from_stackoverflow(keyword, count=3)
                    elif source == "csdn":
                        # 为CSDN转换关键词
                        csdn_keyword = keyword
                        if "kernel" in keyword:
                            csdn_keyword = keyword.replace("kernel", "内核")
                        results = acquisition.acquire_from_csdn(csdn_keyword, count=3)
                    elif source == "zhihu":
                        # 为知乎转换关键词
                        zhihu_keyword = keyword
                        if "kernel" in keyword:
                            zhihu_keyword = keyword.replace("kernel", "内核")
                        results = acquisition.acquire_from_zhihu(zhihu_keyword, count=3)
                    elif source == "juejin":
                        # 为掘金转换关键词
                        juejin_keyword = keyword
                        if "kernel" in keyword:
                            juejin_keyword = keyword.replace("kernel", "内核")
                        results = acquisition.acquire_from_juejin(juejin_keyword, count=3)
                    
                    all_results.extend(results)
                    success_count = sum(1 for r in results if r.get("success"))
                    print(f"     成功: {success_count}/{len(results)} 个案例")
                    
                    # 添加随机延迟避免被封禁
                    delay = random.uniform(2, 5)
                    print(f"     延迟 {delay:.1f} 秒...")
                    time.sleep(delay)
            
            except Exception as e:
                print(f"  ✗ 处理关键词 '{keyword}' 时出错: {e}")
                # 增加延迟后继续
                time.sleep(10)
            
            # 检查是否已达到目标
            total_success = sum(1 for r in all_results if r.get("success"))
            if total_success >= 1000:
                print(f"\n✓ 已达到目标数量: {total_success} 个案例")
                break
        
        # 统计第二阶段结果
        success_count2 = sum(1 for r in all_results if r.get("success")) - success_count1
        total_success = sum(1 for r in all_results if r.get("success"))
        print(f"\n第二阶段完成: 额外成功 {success_count2} 个案例")
    
    # 最终统计
    print("=" * 70)
    print(f"批量获取完成！")
    print(f"- 总共尝试获取: {len(all_results)} 个案例")
    print(f"- 成功获取: {total_success} 个案例")
    print(f"- 成功率: {total_success/len(all_results)*100:.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    main()