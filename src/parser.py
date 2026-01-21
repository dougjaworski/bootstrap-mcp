"""Parser for Bootstrap MDX documentation files."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

try:
    import frontmatter
except ImportError:
    raise ImportError("python-frontmatter is required. Install with: pip install python-frontmatter")

logger = logging.getLogger(__name__)

# Regex patterns for Bootstrap-specific extraction
CLASS_PATTERN = re.compile(r'class(?:Name)?=["\']([^"\']+)["\']')
EXAMPLE_PATTERN = re.compile(r'<Example[^>]*>(.*?)</Example>', re.DOTALL)
CALLOUT_PATTERN = re.compile(r'<Callout[^>]*>(.*?)</Callout>', re.DOTALL)

# Bootstrap utility class patterns
UTILITY_PATTERNS = [
    # Spacing utilities: m-*, mt-*, mb-*, ml-*, mr-*, mx-*, my-*, p-*, pt-*, pb-*, pl-*, pr-*, px-*, py-*
    re.compile(r'\b([mp][tblrxy]?-[0-5]|[mp][tblrxy]?-auto)\b'),
    # Display utilities: d-*
    re.compile(r'\b(d-(?:none|inline|inline-block|block|grid|table|table-cell|table-row|flex|inline-flex))\b'),
    # Responsive display: d-{breakpoint}-*
    re.compile(r'\b(d-(?:sm|md|lg|xl|xxl)-(?:none|inline|inline-block|block|grid|table|table-cell|table-row|flex|inline-flex))\b'),
    # Flexbox utilities
    re.compile(r'\b(flex-(?:row|row-reverse|column|column-reverse|wrap|nowrap|wrap-reverse|fill|grow-[01]|shrink-[01]))\b'),
    re.compile(r'\b(justify-content-(?:start|end|center|between|around|evenly))\b'),
    re.compile(r'\b(align-items-(?:start|end|center|baseline|stretch))\b'),
    re.compile(r'\b(align-self-(?:start|end|center|baseline|stretch))\b'),
    # Grid system: col-*, col-{breakpoint}-*
    re.compile(r'\b(col(?:-(?:sm|md|lg|xl|xxl))?(?:-(?:\d{1,2}|auto))?)\b'),
    # Color utilities: text-*, bg-*
    re.compile(r'\b(text-(?:primary|secondary|success|danger|warning|info|light|dark|body|muted|white|black-50|white-50))\b'),
    re.compile(r'\b(bg-(?:primary|secondary|success|danger|warning|info|light|dark|body|white|transparent))\b'),
    # Border utilities
    re.compile(r'\b(border(?:-(?:top|bottom|start|end|0))?)\b'),
    re.compile(r'\b(border-(?:primary|secondary|success|danger|warning|info|light|dark|white))\b'),
    re.compile(r'\b(rounded(?:-(?:top|bottom|start|end|circle|pill|[0-3]))?)\b'),
    # Sizing utilities
    re.compile(r'\b([wh]-(?:25|50|75|100|auto))\b'),
    # Position utilities
    re.compile(r'\b(position-(?:static|relative|absolute|fixed|sticky))\b'),
    # Text utilities
    re.compile(r'\b(text-(?:start|end|center|justify|wrap|nowrap|break|truncate))\b'),
    re.compile(r'\b(text-(?:lowercase|uppercase|capitalize))\b'),
    re.compile(r'\b(fw-(?:light|lighter|normal|bold|bolder))\b'),
    re.compile(r'\b(fs-[1-6])\b'),
]


class BootstrapDocParser:
    """Parser for Bootstrap MDX documentation files."""

    def __init__(self, docs_root: Path):
        """
        Initialize the parser.

        Args:
            docs_root: Root directory of Bootstrap documentation
        """
        self.docs_root = Path(docs_root)

    def parse_file(self, filepath: Path) -> Optional[dict[str, Any]]:
        """
        Parse a single MDX file.

        Args:
            filepath: Path to the MDX file

        Returns:
            Dictionary with parsed content or None if parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Extract frontmatter metadata
            metadata = post.metadata
            content = post.content

            # Generate relative path from docs root
            relative_path = filepath.relative_to(self.docs_root)

            # Extract section and component name from path
            section, component_name = self._extract_path_info(relative_path)

            # Extract utility classes from content
            utility_classes = self._extract_utility_classes(content)

            # Extract code examples
            code_examples = self._extract_code_examples(content)

            # Generate Bootstrap documentation URL
            doc_url = self._generate_doc_url(relative_path)

            return {
                'filepath': str(relative_path),
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'section': section,
                'component_name': component_name,
                'utility_classes': utility_classes,
                'code_examples': code_examples,
                'aliases': metadata.get('aliases', []),
                'toc': metadata.get('toc', False),
                'content': content,
                'url': doc_url
            }
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            return None

    def _extract_path_info(self, relative_path: Path) -> tuple[str, str]:
        """
        Extract section and component name from file path.

        Args:
            relative_path: Relative path from docs root

        Returns:
            Tuple of (section, component_name)
        """
        parts = relative_path.parts

        # Get section (first directory after docs root)
        section = parts[0] if len(parts) > 0 else ''

        # Get component name (filename without extension)
        component_name = relative_path.stem

        return section, component_name

    def _extract_utility_classes(self, content: str) -> list[str]:
        """
        Extract Bootstrap utility classes from content.

        Args:
            content: MDX content

        Returns:
            List of unique utility classes found
        """
        classes = set()

        # Find all class attributes
        class_matches = CLASS_PATTERN.findall(content)

        for class_string in class_matches:
            # Split into individual classes
            individual_classes = class_string.split()

            for cls in individual_classes:
                # Check against utility patterns
                for pattern in UTILITY_PATTERNS:
                    if pattern.match(cls):
                        classes.add(cls)

        return sorted(list(classes))

    def _extract_code_examples(self, content: str) -> list[dict[str, str]]:
        """
        Extract code examples from <Example> JSX components.

        Args:
            content: MDX content

        Returns:
            List of code examples with their content
        """
        examples = []
        example_matches = EXAMPLE_PATTERN.findall(content)

        for idx, example_content in enumerate(example_matches, 1):
            # Clean up the content (remove extra whitespace, but preserve structure)
            cleaned_content = example_content.strip()

            if cleaned_content:
                examples.append({
                    'id': f'example_{idx}',
                    'content': cleaned_content
                })

        return examples

    def _generate_doc_url(self, relative_path: Path) -> str:
        """
        Generate Bootstrap documentation URL from file path.

        Args:
            relative_path: Relative path from docs root

        Returns:
            Full Bootstrap documentation URL
        """
        parts = relative_path.parts
        section = parts[0] if len(parts) > 0 else ''
        page = relative_path.stem

        # Bootstrap documentation base URL (version 5.3)
        base_url = "https://getbootstrap.com/docs/5.3"

        return f"{base_url}/{section}/{page}/"

    def parse_directory(self, recursive: bool = True) -> list[dict[str, Any]]:
        """
        Parse all MDX files in the documentation directory.

        Args:
            recursive: Whether to search recursively

        Returns:
            List of parsed documents
        """
        pattern = "**/*.mdx" if recursive else "*.mdx"
        mdx_files = list(self.docs_root.glob(pattern))

        logger.info(f"Found {len(mdx_files)} MDX files to parse")

        parsed_docs = []
        for filepath in mdx_files:
            parsed = self.parse_file(filepath)
            if parsed:
                parsed_docs.append(parsed)

        logger.info(f"Successfully parsed {len(parsed_docs)} documents")
        return parsed_docs


def extract_bootstrap_components(content: str) -> list[str]:
    """
    Extract Bootstrap component names from content.

    Args:
        content: Documentation content

    Returns:
        List of component names mentioned
    """
    # Common Bootstrap components
    components = [
        'accordion', 'alert', 'badge', 'breadcrumb', 'button', 'button-group',
        'card', 'carousel', 'close-button', 'collapse', 'dropdown', 'list-group',
        'modal', 'nav', 'navbar', 'offcanvas', 'pagination', 'placeholder',
        'popovers', 'progress', 'scrollspy', 'spinners', 'toasts', 'tooltips'
    ]

    found_components = []
    content_lower = content.lower()

    for component in components:
        # Look for component mentions in various formats
        if (f'.{component}' in content_lower or
            f'-{component}' in content_lower or
            f'#{component}' in content_lower or
            f' {component} ' in content_lower):
            found_components.append(component)

    return found_components
