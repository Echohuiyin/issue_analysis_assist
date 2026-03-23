"""
Reprocess failed cases with improved parsing logic
"""
import os
import sys
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()

from cases.models import RawCase, TrainingCase, TestCase
from cases.acquisition.vector_service import VectorService
from cases.acquisition.validators import CaseValidator
import json


def is_already_structured(content):
    """Check if content is already in structured report format"""
    if not content:
        return False
    
    structured_indicators = [
        '# Linux内核问题分析报告',
        '## 问题现象',
        '## 环境信息',
        '## 错误日志',
        '## 分析过程',
        '## 根本原因',
        '## 解决方案',
    ]
    
    matches = sum(1 for indicator in structured_indicators if indicator in content)
    return matches >= 3


def parse_structured_content(content):
    """Parse already-structured content directly"""
    if not content:
        return None
    
    result = {
        'title': '',
        'phenomenon': '',
        'key_logs': '',
        'environment': '',
        'root_cause': '',
        'analysis_process': '',
        'troubleshooting_steps': [],
        'solution': '',
        'prevention': '',
        'confidence': 0.8
    }
    
    lines = content.split('\n')
    
    # Extract title
    for line in lines[:5]:
        if line.startswith('# ') and 'Linux内核' in line:
            result['title'] = line.replace('# ', '').strip()
            break
    
    # Extract sections
    current_section = None
    section_content = []
    
    for line in lines:
        if line.startswith('## '):
            if current_section and section_content:
                content_text = '\n'.join(section_content).strip()
                if current_section == '问题现象':
                    result['phenomenon'] = content_text
                elif current_section == '环境信息':
                    result['environment'] = content_text
                elif current_section == '错误日志':
                    result['key_logs'] = content_text
                elif current_section == '分析过程':
                    result['analysis_process'] = content_text
                elif current_section == '根本原因':
                    result['root_cause'] = content_text
                elif current_section == '解决方案':
                    result['solution'] = content_text
            
            current_section = line.replace('## ', '').strip()
            section_content = []
        elif current_section:
            section_content.append(line)
    
    # Handle last section
    if current_section and section_content:
        content_text = '\n'.join(section_content).strip()
        if current_section == '问题现象':
            result['phenomenon'] = content_text
        elif current_section == '环境信息':
            result['environment'] = content_text
        elif current_section == '错误日志':
            result['key_logs'] = content_text
        elif current_section == '分析过程':
            result['analysis_process'] = content_text
        elif current_section == '根本原因':
            result['root_cause'] = content_text
        elif current_section == '解决方案':
            result['solution'] = content_text
    
    # Extract environment info
    if result['environment']:
        env_lines = result['environment'].split('\n')
        env_info = {}
        for line in env_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                env_info[key.strip().lstrip('- ')] = value.strip()
        if env_info:
            result['environment'] = json.dumps(env_info, ensure_ascii=False)
    
    # Validate required fields
    if not result['phenomenon']:
        return None
    if not result['root_cause']:
        result['root_cause'] = '见分析过程'
    if not result['solution']:
        result['solution'] = '见分析过程'
    
    # Set title if not found
    if not result['title']:
        result['title'] = 'Linux内核问题案例'
    
    return result


def reprocess_failed_case(raw_case, vector_service, validator):
    """Reprocess a single failed case"""
    print(f"\n{'='*70}")
    print(f"Reprocessing case {raw_case.raw_id}: {raw_case.raw_title[:60]}")
    print(f"{'='*70}")
    
    content = raw_case.raw_content
    
    if not content:
        print("  ❌ No content")
        return False
    
    # Check if already structured
    if is_already_structured(content):
        print("  ✓ Content is already structured, parsing directly...")
        case_data = parse_structured_content(content)
        
        if not case_data:
            print("  ❌ Failed to parse structured content")
            return False
        
        print(f"  ✓ Parsed: {case_data['title']}")
        print(f"    Phenomenon: {case_data['phenomenon'][:50]}...")
        print(f"    Root cause: {case_data['root_cause'][:50]}...")
    else:
        print("  ⚠️ Content is not structured, skipping LLM parsing")
        return False
    
    # Validate quality
    print("  Validating quality...")
    validation_result = validator.validate(case_data)
    is_valid = validation_result['is_valid']
    quality_score = validation_result['quality_score']
    issues = validation_result.get('errors', [])
    
    print(f"  Quality score: {quality_score}")
    if issues:
        print(f"  Issues: {issues[:2]}")
    
    if not is_valid and quality_score < 50:
        print(f"  ❌ Low quality ({quality_score}), skipping")
        raw_case.status = 'low_quality'
        raw_case.process_error = f'Quality score too low: {quality_score}'
        raw_case.save()
        return False
    
    # Generate embedding
    print("  Generating embedding...")
    try:
        embedding = vector_service.generate_embedding(
            f"{case_data['title']} {case_data['phenomenon']} {case_data['root_cause']}"
        )
        if not embedding:
            print("  ❌ Failed to generate embedding")
            return False
        print(f"  ✓ Generated embedding (dim: {len(embedding)})")
    except Exception as e:
        print(f"  ❌ Embedding error: {e}")
        return False
    
    # Save to TrainingCase or TestCase
    try:
        case_data['quality_score'] = quality_score
        case_data['embedding'] = embedding
        case_data['source'] = raw_case.source
        case_data['source_id'] = raw_case.source_id
        case_data['url'] = raw_case.url
        
        # 80% to training, 20% to test
        import random
        if random.random() < 0.8:
            training_case = TrainingCase.objects.create(**case_data)
            print(f"  ✓ Saved as TrainingCase ID: {training_case.case_id}")
        else:
            test_case = TestCase.objects.create(**case_data)
            print(f"  ✓ Saved as TestCase ID: {test_case.case_id}")
        
        # Update raw case status
        raw_case.status = 'processed'
        raw_case.process_error = ''
        raw_case.save()
        
        print(f"  ✅ Successfully reprocessed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Save error: {e}")
        raw_case.status = 'failed'
        raw_case.process_error = f'Save failed: {str(e)}'
        raw_case.save()
        return False


def main():
    print("="*70)
    print("Reprocessing Failed Cases")
    print("="*70)
    
    # Initialize services
    print("\nInitializing services...")
    vector_service = VectorService()
    validator = CaseValidator()
    
    # Get failed cases
    failed_cases = RawCase.objects.filter(status='failed')
    total = failed_cases.count()
    print(f"\nFound {total} failed cases to reprocess")
    
    if total == 0:
        print("No failed cases found!")
        return
    
    # Process each case
    success_count = 0
    failed_count = 0
    low_quality_count = 0
    
    for i, case in enumerate(failed_cases, 1):
        print(f"\n[{i}/{total}] Processing...")
        
        result = reprocess_failed_case(case, vector_service, validator)
        
        if result:
            success_count += 1
        else:
            if case.status == 'low_quality':
                low_quality_count += 1
            else:
                failed_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("Reprocessing Complete")
    print("="*70)
    print(f"Total processed: {total}")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ⚠️  Low quality: {low_quality_count}")
    print(f"  ❌ Failed: {failed_count}")
    
    # Database stats
    print("\n" + "="*70)
    print("Database Statistics")
    print("="*70)
    print(f"TrainingCase: {TrainingCase.objects.count()}")
    print(f"TestCase: {TestCase.objects.count()}")
    print(f"RawCase status:")
    for status_info in RawCase.objects.values('status').annotate(count=django.db.models.Count('raw_id')):
        print(f"  {status_info['status']}: {status_info['count']}")


if __name__ == '__main__':
    main()