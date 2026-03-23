#!/usr/bin/env python3
"""
Process existing raw cases to create training/test cases
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()

from cases.models import RawCase, TrainingCase, TestCase
from cases.acquisition.llm_parser import LLMParser
from cases.acquisition.validators import CaseValidator
from cases.acquisition.vector_service import get_vector_service
import random

def process_raw_cases(batch_size=10):
    """Process raw cases into structured cases"""
    print("=" * 60)
    print("📦 Processing Raw Cases")
    print("=" * 60)
    
    raw_cases = RawCase.objects.filter(status='pending')[:batch_size]
    total = raw_cases.count()
    
    if total == 0:
        print("No pending raw cases found")
        return
    
    print(f"Found {total} pending raw cases")
    
    llm_parser = LLMParser()
    validator = CaseValidator()
    vector_service = get_vector_service()
    
    processed = 0
    failed = 0
    
    for raw_case in raw_cases:
        print(f"\nProcessing: {raw_case.raw_title[:60] if raw_case.raw_title else 'No title'}...")
        
        try:
            case_data = llm_parser.parse(raw_case.raw_content)
            
            if not case_data:
                print(f"  ❌ Failed to parse")
                raw_case.status = 'failed'
                raw_case.save()
                failed += 1
                continue
            
            case_data['source'] = raw_case.source
            case_data['source_id'] = raw_case.source_id
            case_data['url'] = raw_case.url
            
            is_valid, quality_score = validator.validate(case_data)
            
            if not is_valid:
                print(f"  ❌ Invalid (quality: {quality_score})")
                raw_case.status = 'low_quality'
                raw_case.quality_score = quality_score
                raw_case.save()
                failed += 1
                continue
            
            case_data['quality_score'] = quality_score
            
            embedding = vector_service.generate_embedding(
                f"{case_data['title']} {case_data['phenomenon']} {case_data['root_cause']}"
            )
            case_data['embedding'] = embedding
            
            if random.random() < 0.8:
                case = TrainingCase(**case_data)
            else:
                case = TestCase(**case_data)
            
            case.save()
            
            raw_case.status = 'processed'
            raw_case.quality_score = quality_score
            raw_case.save()
            
            print(f"  ✅ Processed (quality: {quality_score:.1f})")
            processed += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            raw_case.status = 'failed'
            raw_case.save()
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 Processing Summary")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {processed/total*100:.1f}%" if total > 0 else "N/A")
    
    return processed

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=10, help='Number of cases to process')
    args = parser.parse_args()
    
    process_raw_cases(args.batch_size)