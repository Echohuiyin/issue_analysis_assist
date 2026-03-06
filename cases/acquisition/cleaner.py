import re
import hashlib
from bs4 import BeautifulSoup
from typing import List, Optional


class ContentCleaner:
    """Content cleaner for HTML processing and content deduplication.
    
    Provides methods to:
    - Clean HTML tags while preserving code blocks
    - Extract code blocks from HTML
    - Compute content hash for deduplication
    - Remove noise content like ads, watermarks
    - Normalize whitespace
    """

    def clean_html(self, html: str) -> str:
        """Clean HTML tags while preserving code blocks.
        
        Args:
            html: The HTML content to clean
            
        Returns:
            str: Cleaned text with preserved code blocks
        """
        if not html or not isinstance(html, str):
            return ""

        soup = BeautifulSoup(html, 'lxml')

        # Replace code blocks with placeholders first to preserve them
        code_blocks = []
        code_placeholders = []

        # Extract and replace <pre><code> blocks
        for i, code_tag in enumerate(soup.find_all(['pre', 'code'])):
            code_text = code_tag.get_text(separator='\n', strip=True)
            if code_text:
                code_blocks.append(code_text)
                placeholder = f"[CODE_BLOCK_{i}]"
                code_placeholders.append(placeholder)
                # Replace with placeholder
                code_tag.string = placeholder

        # Remove script, style, and other noise elements
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            tag.decompose()

        # Get clean text with placeholders
        clean_text = soup.get_text(separator='\n', strip=True)

        # Restore code blocks
        for i, placeholder in enumerate(code_placeholders):
            if placeholder in clean_text and i < len(code_blocks):
                clean_text = clean_text.replace(placeholder, f"\n[CODE]\n{code_blocks[i]}\n[/CODE]\n")

        # Clean up whitespace and remove empty lines
        clean_text = self.normalize_whitespace(clean_text)
        
        return clean_text

    def extract_code_blocks(self, html: str) -> List[str]:
        """Extract code blocks from HTML content.
        
        Args:
            html: The HTML content to extract code from
            
        Returns:
            List[str]: List of extracted code blocks
        """
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, 'lxml')
        code_blocks = []

        # Extract from <pre><code> tags
        for pre_tag in soup.find_all('pre'):
            code_tag = pre_tag.find('code')
            if code_tag:
                code_text = code_tag.get_text(separator='\n', strip=True)
                if code_text:
                    code_blocks.append(code_text)
            else:
                # Handle <pre> without <code>
                code_text = pre_tag.get_text(separator='\n', strip=True)
                if code_text:
                    code_blocks.append(code_text)

        # Extract standalone <code> tags
        for code_tag in soup.find_all('code'):
            if not code_tag.parent.name == 'pre':
                code_text = code_tag.get_text(separator='\n', strip=True)
                if code_text and code_text not in code_blocks:
                    code_blocks.append(code_text)

        return code_blocks

    def compute_content_hash(self, content: str) -> str:
        """Compute MD5 hash of content for deduplication.
        
        Args:
            content: The content to hash
            
        Returns:
            str: MD5 hash in hexadecimal format
        """
        if not content or not isinstance(content, str):
            return ""

        # Normalize content first
        normalized = self.normalize_whitespace(content.strip())
        if not normalized:
            return ""

        # Compute MD5 hash
        md5_hash = hashlib.md5()
        md5_hash.update(normalized.encode('utf-8'))
        return md5_hash.hexdigest()

    def remove_noise(self, text: str) -> str:
        """Remove noise content like ads, watermarks, and irrelevant text.
        
        Args:
            text: The text to clean
            
        Returns:
            str: Cleaned text with noise removed
        """
        if not text or not isinstance(text, str):
            return ""

        # Pattern to remove common ads and watermarks
        noise_patterns = [
            # Chinese ads patterns
            r'本文由.*?原创',
            r'转载请注明出处',
            r'本文链接：.*?$',
            r'关注.*?公众号',
            r'扫码关注',
            r'广告位.*?招租',
            r'广告\s*\d+',
            r'赞助商链接',
            r'点击查看.*?详情',
            r'查看更多.*?内容',
            # English ads patterns
            r'Advertisement',
            r'ADVERTISEMENT',
            r'Sponsored Content',
            r'Read more.*?$',
            r'Click here.*?$',
            r'Follow us on.*?$',
            r'Subscribe to our.*?$',
            # Common noise patterns
            r'\[图片.*?\]',
            r'\[视频.*?\]',
            r'\[附件.*?\]',
            r'\n\s*\n\s*\n',  # Multiple empty lines
        ]

        cleaned_text = text
        for pattern in noise_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)

        return self.normalize_whitespace(cleaned_text)

    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: The text to normalize
            
        Returns:
            str: Text with normalized whitespace
        """
        if not text or not isinstance(text, str):
            return ""

        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace multiple newlines with single newline
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove leading/trailing whitespace
        return text.strip()


# Singleton instance for easy reuse
content_cleaner = ContentCleaner()