"""Parser for Bootstrap HTML example templates."""

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# Template metadata - manually curated for better search results
TEMPLATE_METADATA = {
    'album': {
        'category': 'content',
        'description': 'Photo album layout with grid of cards',
        'complexity': 'simple',
        'components': ['navbar', 'card', 'grid', 'buttons']
    },
    'album-rtl': {
        'category': 'content',
        'description': 'Photo album layout with RTL (right-to-left) support',
        'complexity': 'simple',
        'components': ['navbar', 'card', 'grid', 'buttons']
    },
    'badges': {
        'category': 'components',
        'description': 'Badge component examples and variations',
        'complexity': 'simple',
        'components': ['badge']
    },
    'blog': {
        'category': 'content',
        'description': 'Multi-column blog layout with featured posts',
        'complexity': 'intermediate',
        'components': ['navbar', 'card', 'grid', 'pagination']
    },
    'blog-rtl': {
        'category': 'content',
        'description': 'Multi-column blog layout with RTL support',
        'complexity': 'intermediate',
        'components': ['navbar', 'card', 'grid', 'pagination']
    },
    'breadcrumbs': {
        'category': 'navigation',
        'description': 'Breadcrumb navigation examples',
        'complexity': 'simple',
        'components': ['breadcrumb']
    },
    'buttons': {
        'category': 'components',
        'description': 'Button component examples and variations',
        'complexity': 'simple',
        'components': ['buttons', 'button-group']
    },
    'carousel': {
        'category': 'components',
        'description': 'Image carousel with controls and indicators',
        'complexity': 'simple',
        'components': ['carousel']
    },
    'carousel-rtl': {
        'category': 'components',
        'description': 'Image carousel with RTL support',
        'complexity': 'simple',
        'components': ['carousel']
    },
    'cheatsheet': {
        'category': 'reference',
        'description': 'Complete reference of all Bootstrap components',
        'complexity': 'complex',
        'components': ['accordion', 'alerts', 'badge', 'breadcrumb', 'buttons', 'card',
                      'carousel', 'dropdown', 'forms', 'list-group', 'modal', 'navbar',
                      'pagination', 'progress', 'spinners', 'toasts', 'tooltips']
    },
    'cheatsheet-rtl': {
        'category': 'reference',
        'description': 'Complete reference of all Bootstrap components with RTL support',
        'complexity': 'complex',
        'components': ['accordion', 'alerts', 'badge', 'breadcrumb', 'buttons', 'card',
                      'carousel', 'dropdown', 'forms', 'list-group', 'modal', 'navbar',
                      'pagination', 'progress', 'spinners', 'toasts', 'tooltips']
    },
    'checkout': {
        'category': 'forms',
        'description': 'E-commerce checkout form with validation',
        'complexity': 'complex',
        'components': ['forms', 'validation', 'card', 'grid']
    },
    'checkout-rtl': {
        'category': 'forms',
        'description': 'E-commerce checkout form with RTL support',
        'complexity': 'complex',
        'components': ['forms', 'validation', 'card', 'grid']
    },
    'cover': {
        'category': 'layouts',
        'description': 'Full-page cover template for landing pages',
        'complexity': 'simple',
        'components': ['navbar', 'buttons']
    },
    'dashboard': {
        'category': 'admin',
        'description': 'Admin dashboard with sidebar, charts, and data tables',
        'complexity': 'complex',
        'components': ['navbar', 'offcanvas', 'table', 'card', 'dropdown', 'forms']
    },
    'dashboard-rtl': {
        'category': 'admin',
        'description': 'Admin dashboard with RTL support',
        'complexity': 'complex',
        'components': ['navbar', 'offcanvas', 'table', 'card', 'dropdown', 'forms']
    },
    'dropdowns': {
        'category': 'components',
        'description': 'Dropdown menu examples and variations',
        'complexity': 'simple',
        'components': ['dropdown', 'buttons']
    },
    'features': {
        'category': 'layouts',
        'description': 'Feature sections for marketing pages',
        'complexity': 'simple',
        'components': ['grid', 'icons', 'card']
    },
    'footers': {
        'category': 'layouts',
        'description': 'Footer layout examples and variations',
        'complexity': 'simple',
        'components': ['grid', 'forms']
    },
    'grid': {
        'category': 'layouts',
        'description': 'Grid system examples and responsive layouts',
        'complexity': 'intermediate',
        'components': ['grid', 'containers']
    },
    'headers': {
        'category': 'layouts',
        'description': 'Header layout examples and variations',
        'complexity': 'simple',
        'components': ['navbar', 'nav', 'dropdown']
    },
    'heroes': {
        'category': 'layouts',
        'description': 'Hero section examples for landing pages',
        'complexity': 'simple',
        'components': ['grid', 'buttons', 'carousel']
    },
    'jumbotron': {
        'category': 'components',
        'description': 'Large callout section for featured content',
        'complexity': 'simple',
        'components': ['buttons', 'typography']
    },
    'list-groups': {
        'category': 'components',
        'description': 'List group component examples',
        'complexity': 'simple',
        'components': ['list-group', 'badge']
    },
    'masonry': {
        'category': 'layouts',
        'description': 'Masonry grid layout with cards',
        'complexity': 'intermediate',
        'components': ['card', 'grid']
    },
    'modals': {
        'category': 'components',
        'description': 'Modal dialog examples and variations',
        'complexity': 'intermediate',
        'components': ['modal', 'buttons', 'forms']
    },
    'navbars': {
        'category': 'navigation',
        'description': 'Navbar examples and variations',
        'complexity': 'intermediate',
        'components': ['navbar', 'nav', 'dropdown', 'forms']
    },
    'navbars-offcanvas': {
        'category': 'navigation',
        'description': 'Navbar with offcanvas mobile menu',
        'complexity': 'intermediate',
        'components': ['navbar', 'offcanvas', 'nav']
    },
    'navbars-static': {
        'category': 'navigation',
        'description': 'Static navbar examples',
        'complexity': 'simple',
        'components': ['navbar', 'nav']
    },
    'offcanvas': {
        'category': 'components',
        'description': 'Offcanvas sidebar examples',
        'complexity': 'simple',
        'components': ['offcanvas', 'buttons']
    },
    'offcanvas-navbar': {
        'category': 'navigation',
        'description': 'Navbar with integrated offcanvas menu',
        'complexity': 'intermediate',
        'components': ['navbar', 'offcanvas', 'nav', 'dropdown']
    },
    'pricing': {
        'category': 'content',
        'description': 'Pricing table layouts',
        'complexity': 'intermediate',
        'components': ['card', 'grid', 'buttons', 'list-group']
    },
    'product': {
        'category': 'content',
        'description': 'Product page layout for e-commerce',
        'complexity': 'complex',
        'components': ['navbar', 'card', 'carousel', 'grid', 'buttons']
    },
    'sign-in': {
        'category': 'forms',
        'description': 'Simple sign-in form layout',
        'complexity': 'simple',
        'components': ['forms', 'card']
    },
    'sidebars': {
        'category': 'navigation',
        'description': 'Sidebar navigation examples',
        'complexity': 'intermediate',
        'components': ['offcanvas', 'nav', 'dropdown']
    },
    'starter-template': {
        'category': 'layouts',
        'description': 'Minimal starter template',
        'complexity': 'simple',
        'components': ['navbar']
    },
    'sticky-footer': {
        'category': 'layouts',
        'description': 'Layout with sticky footer',
        'complexity': 'simple',
        'components': []
    },
    'sticky-footer-navbar': {
        'category': 'layouts',
        'description': 'Layout with sticky footer and navbar',
        'complexity': 'simple',
        'components': ['navbar']
    }
}


class BootstrapExampleParser:
    """Parse Bootstrap HTML example templates."""

    def __init__(self, examples_path: Path):
        """
        Initialize the parser.

        Args:
            examples_path: Path to the bootstrap examples directory
        """
        self.examples_path = Path(examples_path)

    def parse_directory(self) -> list[dict[str, Any]]:
        """
        Parse all example templates in the directory.

        Returns:
            List of parsed template dictionaries
        """
        templates = []

        if not self.examples_path.exists():
            logger.warning(f"Examples directory not found: {self.examples_path}")
            return templates

        # Iterate through all subdirectories
        for template_dir in sorted(self.examples_path.iterdir()):
            if not template_dir.is_dir():
                continue

            # Skip assets directory
            if template_dir.name == 'assets':
                continue

            # Parse the template
            template = self.parse_template(template_dir)
            if template:
                templates.append(template)
                logger.debug(f"Parsed template: {template['name']}")

        logger.info(f"Parsed {len(templates)} templates")
        return templates

    def parse_template(self, template_dir: Path) -> Optional[dict[str, Any]]:
        """
        Parse a single template directory.

        Args:
            template_dir: Path to template directory

        Returns:
            Parsed template dictionary or None if parsing fails
        """
        template_name = template_dir.name
        html_file = template_dir / 'index.html'

        if not html_file.exists():
            logger.warning(f"No index.html found in {template_dir}")
            return None

        try:
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Get metadata
            metadata = TEMPLATE_METADATA.get(template_name, {
                'category': 'other',
                'description': f'{template_name.replace("-", " ").title()} template',
                'complexity': 'intermediate',
                'components': []
            })

            # Extract title from HTML
            title = self._extract_title(html_content)

            # Find custom CSS and JS files
            css_files = self._find_files(template_dir, '*.css')
            js_files = self._find_files(template_dir, '*.js')

            # Extract Bootstrap utility classes
            utility_classes = self._extract_utility_classes(html_content)

            # Extract component usage from HTML
            components_used = self._extract_components(html_content)

            # Combine with metadata components
            all_components = list(set(metadata['components'] + components_used))

            # Check for RTL variant
            is_rtl = template_name.endswith('-rtl')
            has_rtl_variant = False
            rtl_template_name = None

            if not is_rtl:
                # Check if RTL variant exists
                rtl_variant_name = f"{template_name}-rtl"
                rtl_variant_path = self.examples_path / rtl_variant_name / 'index.html'
                if rtl_variant_path.exists():
                    has_rtl_variant = True
                    rtl_template_name = rtl_variant_name

            return {
                'name': template_name,
                'title': title,
                'category': metadata['category'],
                'description': metadata['description'],
                'complexity': metadata['complexity'],
                'html_path': str(html_file),
                'html_content': html_content,
                'css_files': css_files,
                'js_files': js_files,
                'components': all_components,
                'utility_classes': utility_classes,
                'has_rtl_variant': has_rtl_variant,
                'rtl_template_name': rtl_template_name,
                'is_rtl': is_rtl,
                'url': f"https://getbootstrap.com/docs/5.3/examples/{template_name}/"
            }

        except Exception as e:
            logger.error(f"Error parsing template {template_name}: {e}")
            return None

    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML."""
        match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "Bootstrap Example"

    def _find_files(self, directory: Path, pattern: str) -> list[str]:
        """Find files matching pattern in directory."""
        import glob
        files = []
        for file_path in glob.glob(str(directory / pattern)):
            # Skip .rtl.css files as they're variants
            if '.rtl.' not in os.path.basename(file_path):
                files.append(file_path)
        return files

    def _extract_utility_classes(self, html_content: str) -> list[str]:
        """
        Extract Bootstrap utility classes from HTML.

        Args:
            html_content: HTML content to parse

        Returns:
            List of unique utility class names
        """
        # Pattern to match class attributes
        class_pattern = r'class=["\']([^"\']+)["\']'
        classes = set()

        for match in re.finditer(class_pattern, html_content):
            class_list = match.group(1).split()
            for cls in class_list:
                # Filter for common Bootstrap utility patterns
                if any(cls.startswith(prefix) for prefix in [
                    'd-', 'flex-', 'justify-', 'align-', 'text-', 'bg-', 'border-',
                    'm-', 'mt-', 'mb-', 'ms-', 'me-', 'mx-', 'my-',
                    'p-', 'pt-', 'pb-', 'ps-', 'pe-', 'px-', 'py-',
                    'w-', 'h-', 'mw-', 'mh-', 'vw-', 'vh-',
                    'position-', 'top-', 'bottom-', 'start-', 'end-',
                    'rounded-', 'shadow-', 'opacity-', 'overflow-',
                    'gap-', 'col-', 'row-', 'g-', 'gx-', 'gy-',
                    'fs-', 'fw-', 'fst-', 'lh-', 'font-'
                ]):
                    classes.add(cls)

        return sorted(list(classes))

    def _extract_components(self, html_content: str) -> list[str]:
        """
        Extract Bootstrap component usage from HTML.

        Args:
            html_content: HTML content to parse

        Returns:
            List of component names used
        """
        components = set()

        # Component patterns to search for
        component_patterns = {
            'accordion': r'class=["\'][^"\']*accordion[^"\']*["\']',
            'alert': r'class=["\'][^"\']*alert[^"\']*["\']',
            'badge': r'class=["\'][^"\']*badge[^"\']*["\']',
            'breadcrumb': r'class=["\'][^"\']*breadcrumb[^"\']*["\']',
            'button': r'class=["\'][^"\']*btn[^"\']*["\']',
            'button-group': r'class=["\'][^"\']*btn-group[^"\']*["\']',
            'card': r'class=["\'][^"\']*card[^"\']*["\']',
            'carousel': r'class=["\'][^"\']*carousel[^"\']*["\']',
            'dropdown': r'class=["\'][^"\']*dropdown[^"\']*["\']',
            'forms': r'<form|class=["\'][^"\']*form-control[^"\']*["\']',
            'list-group': r'class=["\'][^"\']*list-group[^"\']*["\']',
            'modal': r'class=["\'][^"\']*modal[^"\']*["\']',
            'nav': r'class=["\'][^"\']*\bnav\b[^"\']*["\']',
            'navbar': r'class=["\'][^"\']*navbar[^"\']*["\']',
            'offcanvas': r'class=["\'][^"\']*offcanvas[^"\']*["\']',
            'pagination': r'class=["\'][^"\']*pagination[^"\']*["\']',
            'progress': r'class=["\'][^"\']*progress[^"\']*["\']',
            'spinner': r'class=["\'][^"\']*spinner[^"\']*["\']',
            'table': r'<table[^>]*class=["\'][^"\']*table[^"\']*["\']',
            'toast': r'class=["\'][^"\']*toast[^"\']*["\']',
            'tooltip': r'data-bs-toggle=["\']tooltip["\']',
            'popover': r'data-bs-toggle=["\']popover["\']'
        }

        for component, pattern in component_patterns.items():
            if re.search(pattern, html_content, re.IGNORECASE):
                components.add(component)

        return sorted(list(components))
