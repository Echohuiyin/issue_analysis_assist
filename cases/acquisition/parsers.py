import re
import json
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from bs4 import BeautifulSoup


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> Optional[Dict]:
        """Parse the given content into a structured case format"""
        pass


class BlogParser(BaseParser):
    """Parse blog/article HTML content into structured kernel case data.
    Uses BeautifulSoup to extract title, body, and then applies keyword-based
    section extraction for phenomenon, environment, root cause, etc.
    """

    # Keywords for section extraction (Chinese + English)
    SECTION_KEYWORDS = {
        "phenomenon": [
            "现象", "症状", "问题描述", "问题现象", "故障现象", "故障描述",
            "Symptom", "Problem", "Issue", "Bug Description", "现场",
        ],
        "environment": [
            "环境", "内核版本", "系统环境", "测试环境", "运行环境", "软件版本",
            "Environment", "Kernel version", "System Info", "Platform",
        ],
        "root_cause": [
            "根因", "原因分析", "根本原因", "原因", "问题分析", "分析",
            "Root cause", "Root Cause", "Analysis", "Cause",
        ],
        "troubleshooting": [
            "排查过程", "排查步骤", "分析过程", "调试过程", "定位过程", "排查",
            "Troubleshooting", "Debug", "Investigation", "Steps",
        ],
        "solution": [
            "解决方案", "解决办法", "修复方案", "修复", "解决", "方案",
            "Solution", "Fix", "Workaround", "Resolution", "Patch",
        ],
    }

    # Regex for kernel version extraction
    KERNEL_VERSION_RE = re.compile(
        r'(?:Linux|kernel|内核)\s*(?:version\s*)?(\d+\.\d+[\.\d]*(?:-[\w.]+)?)',
        re.IGNORECASE
    )

    def parse(self, content: str) -> Optional[Dict]:
        """Parse blog HTML content into structured case"""
        if not content:
            return None

        soup = BeautifulSoup(content, 'lxml')

        # Extract title
        title = self._extract_title(soup)
        if not title:
            return None

        # Extract body text
        body_text = self._extract_body(soup)
        if not body_text or len(body_text.strip()) < 50:
            return None

        # Extract sections by keyword matching
        sections = self._extract_sections(body_text)

        # Extract kernel version from full text
        kernel_ver = self._extract_kernel_version(body_text)
        env = sections.get("environment", "")
        if kernel_ver and kernel_ver not in env:
            env = f"{env}, kernel {kernel_ver}".strip(", ")

        # Build troubleshooting steps list
        ts_text = sections.get("troubleshooting", "")
        troubleshooting_steps = self._text_to_steps(ts_text) if ts_text else ["See full article for details"]

        # Fallback: if no phenomenon extracted, use first paragraph of body
        phenomenon = sections.get("phenomenon", "")
        if not phenomenon:
            first_para = body_text.strip().split('\n')[0][:500]
            phenomenon = first_para

        # Fallback: if no root_cause, use a portion of body
        root_cause = sections.get("root_cause", "")
        if not root_cause or len(root_cause) < 10:
            root_cause = f"See article: {title}"

        solution = sections.get("solution", "")
        if not solution or len(solution) < 10:
            solution = f"See article for solution details: {title}"

        return {
            "title": title[:200],
            "phenomenon": phenomenon[:2000],
            "environment": env[:500] if env else "Not specified",
            "root_cause": root_cause[:2000],
            "troubleshooting_steps": troubleshooting_steps,
            "solution": solution[:2000],
            "related_code": "",
            "reference_url": "",
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML"""
        for selector in ['h1', 'title', '.article-title', '.post-title', '#title']:
            tag = soup.select_one(selector)
            if tag and tag.get_text(strip=True):
                return tag.get_text(strip=True)
        return ""

    def _extract_body(self, soup: BeautifulSoup) -> str:
        """Extract main body text from HTML"""
        # Remove script/style/nav elements
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # Try common article containers
        for selector in ['article', '.article-content', '.post-content', '.blog-content',
                         '.markdown-body', '.content', '#content', 'main', '.entry-content']:
            container = soup.select_one(selector)
            if container:
                text = container.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    return text

        # Fallback: use body text
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from text using keyword matching."""
        sections = {}
        lines = text.split('\n')

        for section_name, keywords in self.SECTION_KEYWORDS.items():
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                if any(kw.lower() in line_stripped.lower() for kw in keywords):
                    section_lines = []
                    for j in range(i + 1, min(i + 50, len(lines))):
                        next_line = lines[j].strip()
                        if self._is_heading(next_line):
                            break
                        if next_line:
                            section_lines.append(next_line)
                    if section_lines:
                        sections[section_name] = '\n'.join(section_lines)
                    break

        return sections

    def _is_heading(self, line: str) -> bool:
        """Check if a line looks like a section heading"""
        if not line:
            return False
        if line.startswith('#'):
            return True
        if len(line) < 50 and (line.endswith(':') or line.endswith('\uff1a')):
            return True
        for keywords in self.SECTION_KEYWORDS.values():
            if any(kw.lower() in line.lower() for kw in keywords):
                return True
        return False

    def _extract_kernel_version(self, text: str) -> str:
        """Extract kernel version from text"""
        match = self.KERNEL_VERSION_RE.search(text)
        return match.group(1) if match else ""

    def _text_to_steps(self, text: str) -> List[str]:
        """Convert text block into a list of steps"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        steps = []
        for line in lines:
            cleaned = re.sub(r'^[\d]+[.)\uff1a:]\s*', '', line)
            cleaned = re.sub(r'^[-\u2022*]\s*', '', cleaned)
            cleaned = re.sub(r'^Step\s*\d+[.:\uff1a]?\s*', '', cleaned, flags=re.IGNORECASE)
            if cleaned and len(cleaned) > 5:
                steps.append(cleaned)
        return steps if steps else ["See full article for details"]


class ForumParser(BaseParser):
    """Parse StackOverflow API JSON response into structured kernel case data.
    Expects JSON string with 'question' and 'answer' fields as produced by
    StackOverflowFetcher. Also supports HTML forum pages as fallback.
    """

    KERNEL_VERSION_RE = re.compile(
        r'(?:Linux|kernel|内核)\s*(?:version\s*)?(\d+\.\d+[\.\d]*(?:-[\w.]+)?)',
        re.IGNORECASE
    )

    def parse(self, content: str) -> Optional[Dict]:
        """Parse StackOverflow question+answer JSON into structured case"""
        if not content:
            return None

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return self._parse_html_forum(content)

        question = data.get("question", {})
        answer_body = data.get("answer", "")

        title = question.get("title", "")
        if not title:
            return None

        # Extract question body text
        q_body_html = question.get("body", "")
        q_body = BeautifulSoup(q_body_html, 'lxml').get_text(separator='\n', strip=True) if q_body_html else ""

        # Extract answer text
        a_text = BeautifulSoup(answer_body, 'lxml').get_text(separator='\n', strip=True) if answer_body else ""

        # Extract tags as affected components
        tags = question.get("tags", [])
        components = ", ".join(tags) if tags else "linux-kernel"

        # Extract kernel version
        full_text = f"{q_body}\n{a_text}"
        kernel_ver = ""
        match = self.KERNEL_VERSION_RE.search(full_text)
        if match:
            kernel_ver = match.group(1)

        # Build environment string
        env_parts = []
        if kernel_ver:
            env_parts.append(f"Linux {kernel_ver}")
        if tags:
            env_parts.append(f"Tags: {', '.join(tags)}")
        environment = ", ".join(env_parts) if env_parts else "Linux kernel (version not specified)"

        # Root cause from answer
        root_cause = a_text[:2000] if a_text else q_body[:2000]
        if len(root_cause) < 10:
            root_cause = f"See StackOverflow question: {title}"

        # Solution from answer
        solution = a_text[:2000] if a_text else f"See StackOverflow for answers: {title}"
        if len(solution) < 10:
            solution = f"See StackOverflow for answers: {title}"

        # Troubleshooting steps from answer
        troubleshooting_steps = []
        if a_text:
            for line in a_text.split('\n'):
                line = line.strip()
                if line and len(line) > 10:
                    troubleshooting_steps.append(line[:200])
                if len(troubleshooting_steps) >= 5:
                    break
        if not troubleshooting_steps:
            troubleshooting_steps = ["See StackOverflow answer for details"]

        return {
            "title": title[:200],
            "phenomenon": q_body[:2000] if q_body else title,
            "environment": environment[:500],
            "root_cause": root_cause,
            "troubleshooting_steps": troubleshooting_steps,
            "solution": solution,
            "affected_components": components,
            "related_code": "",
            "reference_url": question.get("link", ""),
        }

    def _parse_html_forum(self, content: str) -> Optional[Dict]:
        """Fallback: parse HTML forum page"""
        if not content or len(content) < 50:
            return None

        soup = BeautifulSoup(content, 'lxml')

        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None

        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        body = soup.get_text(separator='\n', strip=True)

        kernel_ver = ""
        match = self.KERNEL_VERSION_RE.search(body)
        if match:
            kernel_ver = match.group(1)

        return {
            "title": title[:200],
            "phenomenon": body[:2000],
            "environment": f"Linux {kernel_ver}" if kernel_ver else "Not specified",
            "root_cause": f"See forum discussion: {title}",
            "troubleshooting_steps": ["See forum discussion for details"],
            "solution": f"See forum discussion for solution: {title}",
            "related_code": "",
            "reference_url": "",
        }
