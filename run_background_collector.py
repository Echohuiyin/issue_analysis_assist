#!/usr/bin/env python3
"""
Background Case Collection Runner
Runs continuously and logs progress to /var/log/collector.log
"""
import os
import sys
import time
import logging
import signal
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

import django
django.setup()

from cases.models import TrainingCase, TestCase
from collect_high_quality_cases import HighQualityCaseCollector
from collect_real_cases import RealCaseCollector

# Configure logging
log_file = Path('/var/log/collector.log')
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

def get_current_stats():
    """Get current database statistics"""
    try:
        training_count = TrainingCase.objects.count()
        test_count = TestCase.objects.count()
        return {
            'training': training_count,
            'test': test_count,
            'total': training_count + test_count,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None

def run_collection_cycle(cycle_number):
    """Run one collection cycle"""
    logger.info("="*70)
    logger.info(f"Starting Collection Cycle #{cycle_number}")
    logger.info("="*70)
    
    # Get initial stats
    initial_stats = get_current_stats()
    if initial_stats:
        logger.info(f"Initial stats: {initial_stats['total']} cases "
                   f"(Training: {initial_stats['training']}, Test: {initial_stats['test']})")
    
    try:
        # Run high-quality case collection
        logger.info("\n" + "-"*70)
        logger.info("Running High-Quality Case Collection")
        logger.info("-"*70)
        
        hq_collector = HighQualityCaseCollector()
        hq_collector.run(max_cases_per_source=30)
        
        logger.info(f"HQ Collection stats: {hq_collector.stats}")
        
        # Small delay between collections
        time.sleep(5)
        
        # Run real case collection
        logger.info("\n" + "-"*70)
        logger.info("Running Real Case Collection")
        logger.info("-"*70)
        
        real_collector = RealCaseCollector()
        real_collector.run(max_cases_per_source=10)
        
        logger.info(f"Real Collection stats: {real_collector.stats}")
        
        # Get final stats
        final_stats = get_current_stats()
        if final_stats and initial_stats:
            new_cases = final_stats['total'] - initial_stats['total']
            logger.info("\n" + "="*70)
            logger.info("Cycle Summary")
            logger.info("="*70)
            logger.info(f"Cases before: {initial_stats['total']}")
            logger.info(f"Cases after:  {final_stats['total']}")
            logger.info(f"New cases:    {new_cases}")
            logger.info(f"Target:       1000+ cases")
            logger.info(f"Progress:     {final_stats['total']}/1000 ({final_stats['total']/10:.1f}%)")
            logger.info("="*70)
            
            # Check if target reached
            if final_stats['total'] >= 1000:
                logger.info("🎉 TARGET REACHED! 1000+ cases collected!")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in collection cycle: {e}", exc_info=True)
        return False

def main():
    """Main background collection loop"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("\n" + "="*70)
    logger.info("Background Case Collection Runner Started")
    logger.info("="*70)
    logger.info(f"Log file: {log_file}")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check initial database status
    stats = get_current_stats()
    if stats:
        logger.info(f"\nCurrent database status:")
        logger.info(f"  Training cases: {stats['training']}")
        logger.info(f"  Test cases:     {stats['test']}")
        logger.info(f"  Total cases:    {stats['total']}")
        logger.info(f"  Target:         1000+ cases")
        
        if stats['total'] >= 1000:
            logger.info("✅ Target already reached! Exiting...")
            return
    
    cycle_number = 1
    target_reached = False
    
    # Main collection loop
    while running and not target_reached:
        try:
            target_reached = run_collection_cycle(cycle_number)
            
            if target_reached:
                logger.info("🎉 Collection complete! Target reached.")
                break
            
            if not running:
                logger.info("Shutdown signal received, stopping...")
                break
            
            # Wait before next cycle
            wait_time = 300  # 5 minutes
            logger.info(f"\nWaiting {wait_time} seconds before next cycle...")
            logger.info(f"Next cycle at: {(datetime.now().timestamp() + wait_time)}")
            
            # Sleep in small increments to allow graceful shutdown
            for _ in range(wait_time):
                if not running:
                    break
                time.sleep(1)
            
            cycle_number += 1
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            logger.info("Waiting 60 seconds before retry...")
            time.sleep(60)
    
    # Final status
    final_stats = get_current_stats()
    if final_stats:
        logger.info("\n" + "="*70)
        logger.info("Final Database Status")
        logger.info("="*70)
        logger.info(f"Training cases: {final_stats['training']}")
        logger.info(f"Test cases:     {final_stats['test']}")
        logger.info(f"Total cases:    {final_stats['total']}")
        logger.info(f"Cycles run:     {cycle_number}")
        logger.info("="*70)
    
    logger.info("Background collector stopped.")

if __name__ == '__main__':
    main()