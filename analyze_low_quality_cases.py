#!/usr/bin/env python3
"""
分析低质量案例
找出为什么案例被标记为低质量
"""
import os
import sys
import json
from collections import Counter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import RawCase

def analyze_low_quality_cases():
    print("=" * 70)
    print("低质量案例分析")
    print("=" * 70)
    print()
    
    low_quality_cases = RawCase.objects.filter(status='low_quality')
    total = low_quality_cases.count()
    print(f"低质量案例总数: {total}")
    print()
    
    if total == 0:
        print("没有低质量案例")
        return
    
    # 分析质量分数分布
    score_distribution = Counter()
    quality_scores_distribution = {
        'phenomenon': Counter(),
        'key_logs': Counter(),
        'analysis_process': Counter(),
        'root_cause': Counter(),
        'solution': Counter()
    }
    
    issues = []
    
    for case in low_quality_cases[:100]:  # 分析前100个
        # 总体分数分布
        if case.quality_score:
            score_range = int(case.quality_score // 10) * 10
            score_distribution[score_range] += 1
        
        # 各项分数分布
        if case.quality_details:
            try:
                details = json.loads(case.quality_details)
                qs = details.get('quality_scores', {})
                for field in quality_scores_distribution.keys():
                    score = qs.get(field, 0)
                    score_range = int(score // 10) * 10
                    quality_scores_distribution[field][score_range] += 1
                
                # 收集问题
                if not details.get('is_high_quality'):
                    issues.append({
                        'id': case.raw_id,
                        'overall': case.quality_score,
                        'scores': qs
                    })
            except:
                pass
    
    # 打印总体分数分布
    print("总体质量分数分布:")
    for score_range in sorted(score_distribution.keys(), reverse=True):
        count = score_distribution[score_range]
        bar = '█' * (count // 2)
        print(f"  {score_range:3d}-{score_range+9:3d}: {count:4d} {bar}")
    print()
    
    # 打印各项分数分布
    for field, dist in quality_scores_distribution.items():
        print(f"{field} 分数分布:")
        for score_range in sorted(dist.keys(), reverse=True):
            count = dist[score_range]
            bar = '█' * (count // 2)
            print(f"  {score_range:3d}-{score_range+9:3d}: {count:4d} {bar}")
        print()
    
    # 分析具体问题
    print("=" * 70)
    print("具体问题分析（前10个）:")
    print("=" * 70)
    for i, issue in enumerate(issues[:10], 1):
        print(f"\n案例 {i}: ID={issue['id']}, 总分={issue['overall']:.1f}")
        print("各项分数:")
        for field, score in issue['scores'].items():
            status = "✓" if score >= 50 else "✗"
            print(f"  {status} {field}: {score:.1f}")
        
        # 找出最低分的项
        min_field = min(issue['scores'].items(), key=lambda x: x[1])
        print(f"  最低分项: {min_field[0]} ({min_field[1]:.1f})")
    
    # 统计主要问题
    print()
    print("=" * 70)
    print("主要问题统计:")
    print("=" * 70)
    
    problem_counts = Counter()
    for issue in issues:
        scores = issue['scores']
        if scores.get('phenomenon', 0) < 40:
            problem_counts['现象描述不足'] += 1
        if scores.get('key_logs', 0) < 30:
            problem_counts['缺少关键日志'] += 1
        if scores.get('analysis_process', 0) < 30:
            problem_counts['分析过程不足'] += 1
        if scores.get('root_cause', 0) < 50:
            problem_counts['根因分析不足'] += 1
        if scores.get('solution', 0) < 50:
            problem_counts['解决方案不足'] += 1
    
    for problem, count in problem_counts.most_common():
        percentage = count / len(issues) * 100 if issues else 0
        print(f"  {problem}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    analyze_low_quality_cases()