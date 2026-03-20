"""
Kernel Bugzilla Case Collector
Collects high-quality kernel issue cases from kernel.org Bugzilla
"""
import requests
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time


class BugzillaFetcher:
    """Fetch kernel cases from Kernel Bugzilla"""
    
    BASE_URL = "https://bugzilla.kernel.org"
    API_URL = "https://bugzilla.kernel.org/rest"
    
    # High-priority components
    HIGH_PRIORITY_COMPONENTS = [
        'Memory Management', 'Scheduler', 'Drivers', 'Network',
        'File System', 'Block Layer', 'Power Management',
        'Virtualization', 'Security', 'Other'
    ]
    
    def __init__(self, rate_limit_delay=1.0):
        """
        Initialize Bugzilla fetcher
        
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
    
    def search_bugs(self, keywords: List[str], days_back: int = 90, max_results: int = 100) -> List[Dict]:
        """
        Search Bugzilla for bugs matching keywords
        
        Args:
            keywords: List of search keywords
            days_back: Number of days to search back
            max_results: Maximum number of results to return
            
        Returns:
            List of bug metadata
        """
        bugs = []
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search using Bugzilla API
            for keyword in keywords[:10]:  # Limit keywords
                print(f"  Searching for: {keyword}")
                
                params = {
                    'summary': keyword,
                    'chfieldfrom': start_date.strftime('%Y-%m-%d'),
                    'chfieldto': end_date.strftime('%Y-%m-%d'),
                    'resolution': '---',  # Open bugs
                    'limit': max_results // len(keywords[:10])
                }
                
                try:
                    response = self.session.get(
                        f"{self.API_URL}/bug",
                        params=params,
                        timeout=30
                    )
                    time.sleep(self.rate_limit_delay)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'bugs' in data:
                            for bug in data['bugs']:
                                bugs.append({
                                    'bug_id': bug['id'],
                                    'summary': bug.get('summary', ''),
                                    'status': bug.get('status', ''),
                                    'component': bug.get('component', ''),
                                    'priority': bug.get('priority', ''),
                                    'severity': bug.get('severity', ''),
                                    'creation_time': bug.get('creation_time', ''),
                                    'url': f"{self.BASE_URL}/show_bug.cgi?id={bug['id']}"
                                })
                    
                    self.stats['total_fetched'] += 1
                    
                except Exception as e:
                    print(f"    Error searching {keyword}: {e}")
                    self.stats['failed'] += 1
                    continue
                
                if len(bugs) >= max_results:
                    break
        
        except Exception as e:
            print(f"Search error: {e}")
        
        # Remove duplicates
        seen = set()
        unique_bugs = []
        for bug in bugs:
            if bug['bug_id'] not in seen:
                seen.add(bug['bug_id'])
                unique_bugs.append(bug)
        
        print(f"  Found {len(unique_bugs)} unique bugs")
        return unique_bugs[:max_results]
    
    def fetch_bug_details(self, bug_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a single bug
        
        Args:
            bug_id: Bug ID
            
        Returns:
            Bug details dictionary or None
        """
        try:
            response = self.session.get(
                f"{self.API_URL}/bug/{bug_id}",
                timeout=30
            )
            time.sleep(self.rate_limit_delay)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'bugs' not in data or not data['bugs']:
                return None
            
            bug = data['bugs'][0]
            
            bug_data = {
                'bug_id': bug_id,
                'url': f"{self.BASE_URL}/show_bug.cgi?id={bug_id}",
                'title': bug.get('summary', ''),
                'status': bug.get('status', ''),
                'resolution': bug.get('resolution', ''),
                'component': bug.get('component', ''),
                'priority': bug.get('priority', ''),
                'severity': bug.get('severity', ''),
                'creator': bug.get('creator', ''),
                'creation_time': bug.get('creation_time', ''),
                'description': '',
                'comments': [],
                'attachments': [],
                'quality_score': 0
            }
            
            # Get description and comments
            if 'comments' in bug:
                for comment in bug['comments']:
                    if comment.get('count') == 0:
                        bug_data['description'] = comment.get('text', '')
                    else:
                        bug_data['comments'].append({
                            'author': comment.get('creator', ''),
                            'text': comment.get('text', ''),
                            'time': comment.get('creation_time', '')
                        })
            
            # Get attachments (patches, logs, etc.)
            if 'attachments' in bug:
                for attachment in bug['attachments']:
                    bug_data['attachments'].append({
                        'id': attachment.get('id'),
                        'description': attachment.get('summary', ''),
                        'type': attachment.get('content_type', '')
                    })
            
            # Calculate quality score
            bug_data['quality_score'] = self._calculate_quality_score(bug_data)
            
            self.stats['successful'] += 1
            return bug_data
            
        except Exception as e:
            print(f"    Error fetching bug {bug_id}: {e}")
            self.stats['failed'] += 1
            return None
    
    def _calculate_quality_score(self, bug_data: Dict) -> int:
        """
        Calculate quality score for a bug report
        
        Args:
            bug_data: Bug data dictionary
            
        Returns:
            Quality score (0-100)
        """
        score = 0
        
        # Title quality (20 points)
        if bug_data['title']:
            if len(bug_data['title']) > 20:
                score += 10
            if any(kw in bug_data['title'].lower() for kw in ['crash', 'panic', 'leak', 'deadlock', 'bug']):
                score += 10
        
        # Description quality (30 points)
        desc_len = len(bug_data['description'])
        if desc_len > 200:
            score += 10
        if desc_len > 500:
            score += 10
        if desc_len > 1000:
            score += 10
        
        # Technical content (20 points)
        desc_lower = bug_data['description'].lower()
        
        if 'stack' in desc_lower or 'trace' in desc_lower:
            score += 10
        if 'log' in desc_lower or 'dmesg' in desc_lower:
            score += 10
        
        # Community engagement (15 points)
        if len(bug_data['comments']) > 0:
            score += 5
        if len(bug_data['comments']) > 3:
            score += 5
        if len(bug_data['attachments']) > 0:
            score += 5
        
        # Severity (15 points)
        severity = bug_data.get('severity', '').lower()
        if severity in ['critical', 'high', 'blocker']:
            score += 15
        elif severity in ['normal', 'medium']:
            score += 10
        else:
            score += 5
        
        return min(score, 100)
    
    def extract_case_from_bug(self, bug_data: Dict) -> Optional[Dict]:
        """
        Extract structured case data from bug report
        
        Args:
            bug_data: Bug data dictionary
            
        Returns:
            Structured case data or None
        """
        if bug_data['quality_score'] < 60:
            return None
        
        case = {
            'title': bug_data['title'],
            'phenomenon': '',
            'key_logs': '',
            'environment': '',
            'root_cause': '',
            'analysis_process': '',
            'troubleshooting_steps': [],
            'solution': '',
            'prevention': '',
            'confidence': 0.0,
            'source': 'bugzilla',
            'source_id': str(bug_data['bug_id']),
            'url': bug_data['url'],
            'quality_score': bug_data['quality_score']
        }
        
        description = bug_data['description']
        
        # Extract phenomenon (first part of description)
        lines = description.split('\n')
        phenomenon_lines = []
        
        for line in lines[:15]:
            line = line.strip()
            if line:
                phenomenon_lines.append(line)
            if len(phenomenon_lines) >= 5:
                break
        
        case['phenomenon'] = ' '.join(phenomenon_lines)
        
        # Extract logs
        log_patterns = [
            r'(?:dmesg|kernel log|console output):?\s*```?(.*?)```?',
            r'(?:stack trace|call trace):?\s*```?(.*?)```?',
            r'```\n?(.*?)\n?```'
        ]
        
        for pattern in log_patterns:
            match = re.search(pattern, description, re.DOTALL | re.IGNORECASE)
            if match:
                case['key_logs'] = match.group(1).strip()[:1000]
                break
        
        # Extract environment
        env_patterns = [
            r'(?:kernel version|kernel):?\s*(.+?)(?:\n|$)',
            r'(?:distribution|distro):?\s*(.+?)(?:\n|$)',
            r'(?:architecture|arch):?\s*(.+?)(?:\n|$)'
        ]
        
        env_info = []
        for pattern in env_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                env_info.append(match.group(1).strip())
        
        if env_info:
            case['environment'] = ', '.join(env_info)
        
        # Extract solution from comments
        if bug_data['resolution'] and bug_data['resolution'] != '---':
            case['solution'] = f"Bug resolved as: {bug_data['resolution']}"
        else:
            # Look for solution in comments
            for comment in bug_data['comments']:
                text = comment['text'].lower()
                if any(kw in text for kw in ['fix', 'patch', 'solution', 'workaround']):
                    case['solution'] = comment['text'][:500]
                    break
        
        # Set confidence
        case['confidence'] = bug_data['quality_score'] / 100.0
        
        # Validate minimum requirements
        if not case['phenomenon'] or len(case['phenomenon']) < 50:
            return None
        
        return case
    
    def collect_cases(self, max_cases: int = 100, min_quality: int = 60) -> List[Dict]:
        """
        Collect high-quality cases from Bugzilla
        
        Args:
            max_cases: Maximum number of cases to collect
            min_quality: Minimum quality score (0-100)
            
        Returns:
            List of structured case data
        """
        print("="*70)
        print("Collecting Bugzilla Cases")
        print("="*70)
        
        cases = []
        
        # Search keywords
        keywords = [
            'crash', 'panic', 'deadlock', 'memory leak', 'null pointer',
            'race condition', 'hang', 'regression', 'performance', 'bug'
        ]
        
        # Search for bugs
        print("\n1. Searching for relevant bugs...")
        bugs = self.search_bugs(
            keywords=keywords,
            days_back=180,
            max_results=max_cases * 2
        )
        
        if not bugs:
            print("  No bugs found")
            return cases
        
        # Fetch bug details
        print(f"\n2. Fetching {len(bugs)} bug details...")
        for i, bug_meta in enumerate(bugs[:max_cases * 2], 1):
            print(f"  [{i}/{len(bugs[:max_cases*2])}] Fetching bug {bug_meta['bug_id']}...")
            
            bug_data = self.fetch_bug_details(bug_meta['bug_id'])
            
            if not bug_data:
                continue
            
            # Extract case
            case = self.extract_case_from_bug(bug_data)
            
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
    """Test Bugzilla fetcher"""
    print("Testing Bugzilla Fetcher")
    print("="*70)
    
    fetcher = BugzillaFetcher(rate_limit_delay=0.5)
    
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
        print(f"Bug ID: {sample['source_id']}")
        
        # Save to file
        output_file = 'bugzilla_cases_sample.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved to {output_file}")
    else:
        print("\n❌ No cases collected")


if __name__ == '__main__':
    main()