"""
Linux Kernel Mailing List (LKML) Case Collector
Collects high-quality kernel issue cases from LKML archives
"""
import requests
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time


class LKMLFetcher:
    """Fetch kernel cases from LKML archives"""
    
    BASE_URL = "https://lkml.org"
    LORE_URL = "https://lore.kernel.org"
    
    # High-value keywords for kernel issues
    ISSUE_KEYWORDS = [
        'bug', 'fix', 'crash', 'panic', 'deadlock', 'race condition',
        'memory leak', 'null pointer', 'segfault', 'oops', 'hang',
        'regression', 'performance', 'latency', 'timeout', 'failure',
        'corruption', 'overflow', 'underflow', 'use-after-free',
        'double free', 'invalid', 'error', 'warning', 'lockup'
    ]
    
    # Kernel subsystems
    SUBSYSTEMS = [
        'memory', 'scheduler', 'network', 'driver', 'filesystem',
        'block', 'irq', 'timer', 'lock', 'mm', 'net', 'fs',
        'drivers', 'kernel', 'arch', 'security', 'crypto'
    ]
    
    def __init__(self, rate_limit_delay=1.0):
        """
        Initialize LKML fetcher
        
        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; KernelCaseCollector/1.0)'
        })
        self.rate_limit_delay = rate_limit_delay
        self.stats = {
            'total_fetched': 0,
            'successful': 0,
            'failed': 0,
            'filtered': 0
        }
    
    def search_threads(self, keywords: List[str], days_back: int = 30, max_results: int = 100) -> List[Dict]:
        """
        Search LKML for threads matching keywords
        
        Args:
            keywords: List of search keywords
            days_back: Number of days to search back
            max_results: Maximum number of results to return
            
        Returns:
            List of thread metadata
        """
        threads = []
        
        # Use lore.kernel.org API
        search_url = f"{self.LORE_URL}/lkml/"
        
        try:
            # Search for recent threads
            for keyword in keywords[:5]:  # Limit to avoid too many requests
                print(f"  Searching for: {keyword}")
                
                params = {
                    'q': keyword,
                    'x': 'A',  # Search in all fields
                    'o': '1'   # Sort by date
                }
                
                try:
                    response = self.session.get(search_url, params=params, timeout=30)
                    time.sleep(self.rate_limit_delay)
                    
                    if response.status_code == 200:
                        # Parse search results
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract thread links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if '/lkml/' in href and href.endswith('/'):
                                thread_id = href.rstrip('/').split('/')[-1]
                                
                                threads.append({
                                    'thread_id': thread_id,
                                    'url': f"{self.LORE_URL}{href}",
                                    'keyword': keyword
                                })
                                
                                if len(threads) >= max_results:
                                    break
                    
                    self.stats['total_fetched'] += 1
                    
                except Exception as e:
                    print(f"    Error searching {keyword}: {e}")
                    self.stats['failed'] += 1
                    continue
                
                if len(threads) >= max_results:
                    break
        
        except Exception as e:
            print(f"Search error: {e}")
        
        # Remove duplicates
        seen = set()
        unique_threads = []
        for thread in threads:
            if thread['thread_id'] not in seen:
                seen.add(thread['thread_id'])
                unique_threads.append(thread)
        
        print(f"  Found {len(unique_threads)} unique threads")
        return unique_threads[:max_results]
    
    def fetch_thread(self, thread_url: str) -> Optional[Dict]:
        """
        Fetch and parse a single LKML thread
        
        Args:
            thread_url: URL of the thread
            
        Returns:
            Parsed thread data or None
        """
        try:
            response = self.session.get(thread_url, timeout=30)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract thread content
            thread_data = {
                'url': thread_url,
                'title': '',
                'author': '',
                'date': '',
                'content': '',
                'replies': [],
                'patches': [],
                'quality_score': 0
            }
            
            # Get title
            title_elem = soup.find('h1')
            if title_elem:
                thread_data['title'] = title_elem.get_text(strip=True)
            
            # Get author and date
            meta_elem = soup.find('div', class_='meta')
            if meta_elem:
                meta_text = meta_elem.get_text(strip=True)
                
                # Extract author
                author_match = re.search(r'From:\s*(.+?)\s*[<\[]', meta_text)
                if author_match:
                    thread_data['author'] = author_match.group(1).strip()
                
                # Extract date
                date_match = re.search(r'Date:\s*(.+?)(?:\n|$)', meta_text)
                if date_match:
                    thread_data['date'] = date_match.group(1).strip()
            
            # Get main content
            content_elem = soup.find('pre')
            if content_elem:
                content = content_elem.get_text(strip=True)
                thread_data['content'] = content[:10000]  # Limit length
            
            # Check for patches
            if 'diff --git' in thread_data['content'] or '---' in thread_data['content']:
                thread_data['patches'].append('Contains patch')
            
            # Calculate quality score
            thread_data['quality_score'] = self._calculate_quality_score(thread_data)
            
            self.stats['successful'] += 1
            return thread_data
            
        except Exception as e:
            print(f"    Error fetching thread: {e}")
            self.stats['failed'] += 1
            return None
    
    def _calculate_quality_score(self, thread_data: Dict) -> int:
        """
        Calculate quality score for a thread
        
        Args:
            thread_data: Thread data dictionary
            
        Returns:
            Quality score (0-100)
        """
        score = 0
        
        # Title quality (20 points)
        if thread_data['title']:
            if any(kw in thread_data['title'].lower() for kw in self.ISSUE_KEYWORDS):
                score += 20
        
        # Content length (20 points)
        content_len = len(thread_data['content'])
        if content_len > 500:
            score += 10
        if content_len > 1000:
            score += 10
        
        # Contains technical details (30 points)
        content_lower = thread_data['content'].lower()
        
        # Stack traces
        if 'call trace' in content_lower or 'stack trace' in content_lower:
            score += 10
        
        # Error messages
        if 'error' in content_lower or 'bug' in content_lower:
            score += 10
        
        # Patches
        if thread_data['patches']:
            score += 10
        
        # Author reputation (10 points)
        # Known kernel maintainers
        known_maintainers = [
            'torvalds', 'akpm', 'gregkh', 'tglx', 'mingo', 'peterz',
            'davem', 'netdev', 'linux-kernel'
        ]
        if any(maintainer in thread_data['author'].lower() for maintainer in known_maintainers):
            score += 10
        
        # Subsystem identification (10 points)
        if any(subsys in content_lower for subsys in self.SUBSYSTEMS):
            score += 10
        
        # Reproducible steps (10 points)
        if 'reproduce' in content_lower or 'steps' in content_lower:
            score += 10
        
        return min(score, 100)
    
    def extract_case_from_thread(self, thread_data: Dict) -> Optional[Dict]:
        """
        Extract structured case data from LKML thread
        
        Args:
            thread_data: Thread data dictionary
            
        Returns:
            Structured case data or None
        """
        if thread_data['quality_score'] < 60:
            return None
        
        case = {
            'title': thread_data['title'],
            'phenomenon': '',
            'key_logs': '',
            'environment': '',
            'root_cause': '',
            'analysis_process': '',
            'troubleshooting_steps': [],
            'solution': '',
            'prevention': '',
            'confidence': 0.0,
            'source': 'lkml',
            'url': thread_data['url'],
            'quality_score': thread_data['quality_score']
        }
        
        content = thread_data['content']
        
        # Extract phenomenon (first paragraph or error description)
        lines = content.split('\n')
        phenomenon_lines = []
        
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            if not line:
                if phenomenon_lines:
                    break
                continue
            
            # Look for problem description
            if any(kw in line.lower() for kw in ['problem', 'issue', 'bug', 'error', 'crash']):
                phenomenon_lines.append(line)
            elif phenomenon_lines:
                phenomenon_lines.append(line)
        
        case['phenomenon'] = ' '.join(phenomenon_lines[:5])
        
        # Extract stack traces or error logs
        log_patterns = [
            r'Call Trace:(.*?)(?=\n\n|\n[A-Z])',
            r'Stack trace:(.*?)(?=\n\n|\n[A-Z])',
            r'BUG:(.*?)(?=\n\n|\n[A-Z])',
            r'kernel panic:(.*?)(?=\n\n|\n[A-Z])'
        ]
        
        for pattern in log_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                case['key_logs'] = match.group(1).strip()[:1000]
                break
        
        # Extract root cause (look for "caused by", "root cause", etc.)
        cause_patterns = [
            r'(?:root cause|caused by|reason):?\s*(.+?)(?=\n\n|\n[A-Z])',
            r'(?:the problem is|this happens because)\s*(.+?)(?=\n\n|\n[A-Z])'
        ]
        
        for pattern in cause_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                case['root_cause'] = match.group(1).strip()[:500]
                break
        
        # Extract solution (look for "fix", "patch", "solution")
        if thread_data['patches']:
            case['solution'] = 'Patch available in thread'
        else:
            solution_patterns = [
                r'(?:fix|solution|workaround):?\s*(.+?)(?=\n\n|\n[A-Z])',
                r'(?:this patch|the fix)\s*(.+?)(?=\n\n|\n[A-Z])'
            ]
            
            for pattern in solution_patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    case['solution'] = match.group(1).strip()[:500]
                    break
        
        # Set confidence based on quality score
        case['confidence'] = thread_data['quality_score'] / 100.0
        
        # Validate minimum requirements
        if not case['phenomenon'] or len(case['phenomenon']) < 50:
            return None
        
        return case
    
    def collect_cases(self, max_cases: int = 100, min_quality: int = 60) -> List[Dict]:
        """
        Collect high-quality cases from LKML
        
        Args:
            max_cases: Maximum number of cases to collect
            min_quality: Minimum quality score (0-100)
            
        Returns:
            List of structured case data
        """
        print("="*70)
        print("Collecting LKML Cases")
        print("="*70)
        
        cases = []
        
        # Search for threads
        print("\n1. Searching for relevant threads...")
        threads = self.search_threads(
            keywords=self.ISSUE_KEYWORDS,
            days_back=90,
            max_results=max_cases * 2
        )
        
        if not threads:
            print("  No threads found")
            return cases
        
        # Fetch and parse threads
        print(f"\n2. Fetching {len(threads)} threads...")
        for i, thread_meta in enumerate(threads[:max_cases * 2], 1):
            print(f"  [{i}/{len(threads[:max_cases*2])}] Fetching thread {thread_meta['thread_id']}...")
            
            thread_data = self.fetch_thread(thread_meta['url'])
            
            if not thread_data:
                continue
            
            # Extract case
            case = self.extract_case_from_thread(thread_data)
            
            if case and case['quality_score'] >= min_quality:
                cases.append(case)
                print(f"    ✓ Collected case (quality: {case['quality_score']})")
                
                if len(cases) >= max_cases:
                    break
            else:
                self.stats['filtered'] += 1
        
        # Summary
        print("\n" + "="*70)
        print("Collection Summary")
        print("="*70)
        print(f"Total fetched: {self.stats['total_fetched']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Filtered (low quality): {self.stats['filtered']}")
        print(f"Collected cases: {len(cases)}")
        
        if cases:
            avg_quality = sum(c['quality_score'] for c in cases) / len(cases)
            print(f"Average quality score: {avg_quality:.1f}")
        
        return cases


def main():
    """Test LKML fetcher"""
    print("Testing LKML Fetcher")
    print("="*70)
    
    fetcher = LKMLFetcher(rate_limit_delay=0.5)
    
    # Collect cases
    cases = fetcher.collect_cases(max_cases=10, min_quality=60)
    
    if cases:
        print(f"\n✅ Collected {len(cases)} high-quality cases")
        
        # Show sample
        print("\nSample Case:")
        print("-" * 70)
        sample = cases[0]
        print(f"Title: {sample['title'][:80]}")
        print(f"Quality: {sample['quality_score']}")
        print(f"Phenomenon: {sample['phenomenon'][:150]}...")
        print(f"Source: {sample['source']}")
        
        # Save to file
        output_file = 'lkml_cases_sample.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved to {output_file}")
    else:
        print("\n❌ No cases collected")


if __name__ == '__main__':
    main()