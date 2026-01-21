"""Search functions for Bootstrap example templates."""

import json
import logging
import re
import sqlite3
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BootstrapExampleSearch:
    """Search interface for Bootstrap example templates."""

    def __init__(self, db_path: str):
        """
        Initialize the search interface.

        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to the database."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def search_templates(self, query: str, category: Optional[str] = None, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search example templates using FTS5.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of matching templates
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            if category:
                # Search with category filter
                cursor.execute("""
                    SELECT
                        m.id,
                        m.name,
                        m.title,
                        m.category,
                        m.description,
                        m.complexity,
                        m.components,
                        m.has_rtl_variant,
                        m.url,
                        snippet(templates_fts, 3, '<mark>', '</mark>', '...', 64) as snippet,
                        bm25(templates_fts) as relevance_score
                    FROM templates_fts fts
                    JOIN template_metadata m ON m.id = fts.rowid
                    WHERE templates_fts MATCH ? AND m.category = ?
                    ORDER BY bm25(templates_fts)
                    LIMIT ?
                """, (query, category, limit))
            else:
                # Search without category filter
                cursor.execute("""
                    SELECT
                        m.id,
                        m.name,
                        m.title,
                        m.category,
                        m.description,
                        m.complexity,
                        m.components,
                        m.has_rtl_variant,
                        m.url,
                        snippet(templates_fts, 3, '<mark>', '</mark>', '...', 64) as snippet,
                        bm25(templates_fts) as relevance_score
                    FROM templates_fts fts
                    JOIN template_metadata m ON m.id = fts.rowid
                    WHERE templates_fts MATCH ?
                    ORDER BY bm25(templates_fts)
                    LIMIT ?
                """, (query, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'name': row['name'],
                    'title': row['title'],
                    'category': row['category'],
                    'description': row['description'],
                    'complexity': row['complexity'],
                    'components': json.loads(row['components']) if row['components'] else [],
                    'has_rtl_variant': bool(row['has_rtl_variant']),
                    'url': row['url'],
                    'snippet': row['snippet'],
                    'relevance_score': abs(row['relevance_score'])
                })

            return results

        except Exception as e:
            logger.error(f"Template search error: {e}")
            return []

    def get_template(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            Template data with full HTML content or None
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    title,
                    category,
                    description,
                    complexity,
                    html_path,
                    css_files,
                    js_files,
                    components,
                    utility_classes,
                    has_rtl_variant,
                    rtl_template_name,
                    is_rtl,
                    url
                FROM template_metadata
                WHERE name = ?
                LIMIT 1
            """, (name,))

            row = cursor.fetchone()
            if not row:
                return None

            # Read HTML content from file
            html_content = ""
            if row['html_path']:
                try:
                    with open(row['html_path'], 'r', encoding='utf-8') as f:
                        html_content = f.read()
                except Exception as e:
                    logger.error(f"Error reading HTML file {row['html_path']}: {e}")

            # Read CSS files
            css_content = {}
            if row['css_files']:
                css_files = json.loads(row['css_files'])
                for css_file in css_files:
                    try:
                        with open(css_file, 'r', encoding='utf-8') as f:
                            css_content[css_file.split('/')[-1]] = f.read()
                    except Exception as e:
                        logger.error(f"Error reading CSS file {css_file}: {e}")

            # Read JS files
            js_content = {}
            if row['js_files']:
                js_files = json.loads(row['js_files'])
                for js_file in js_files:
                    try:
                        with open(js_file, 'r', encoding='utf-8') as f:
                            js_content[js_file.split('/')[-1]] = f.read()
                    except Exception as e:
                        logger.error(f"Error reading JS file {js_file}: {e}")

            return {
                'id': row['id'],
                'name': row['name'],
                'title': row['title'],
                'category': row['category'],
                'description': row['description'],
                'complexity': row['complexity'],
                'html_content': html_content,
                'css_content': css_content,
                'js_content': js_content,
                'components': json.loads(row['components']) if row['components'] else [],
                'utility_classes': json.loads(row['utility_classes']) if row['utility_classes'] else [],
                'has_rtl_variant': bool(row['has_rtl_variant']),
                'rtl_template_name': row['rtl_template_name'],
                'is_rtl': bool(row['is_rtl']),
                'url': row['url']
            }

        except Exception as e:
            logger.error(f"Template get error: {e}")
            return None

    def get_template_preview(self, name: str, section: str = 'main') -> Optional[dict[str, Any]]:
        """
        Get a preview section of a template.

        Args:
            name: Template name
            section: Section to extract ('header', 'nav', 'main', 'footer', 'full')

        Returns:
            Template section preview or None
        """
        template = self.get_template(name)
        if not template:
            return None

        html_content = template['html_content']

        if section == 'full':
            # Return first 500 lines
            lines = html_content.split('\n')
            preview = '\n'.join(lines[:500])
        else:
            # Extract specific section
            preview = self._extract_section(html_content, section)

        return {
            'name': template['name'],
            'title': template['title'],
            'section': section,
            'preview': preview,
            'url': template['url']
        }

    def _extract_section(self, html_content: str, section: str) -> str:
        """
        Extract a specific section from HTML content.

        Args:
            html_content: Full HTML content
            section: Section to extract

        Returns:
            Extracted section or full content if not found
        """
        section_patterns = {
            'header': r'<header[^>]*>.*?</header>',
            'nav': r'<nav[^>]*>.*?</nav>',
            'main': r'<main[^>]*>.*?</main>',
            'footer': r'<footer[^>]*>.*?</footer>'
        }

        pattern = section_patterns.get(section)
        if not pattern:
            return html_content[:5000]  # Return first 5000 chars if section not found

        match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0)

        # If section not found, return first 5000 characters
        return html_content[:5000]

    def list_template_categories(self) -> dict[str, Any]:
        """
        List all template categories with counts.

        Returns:
            Dictionary of categories and counts
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    category,
                    COUNT(*) as count,
                    GROUP_CONCAT(name, ', ') as templates
                FROM template_metadata
                GROUP BY category
                ORDER BY category
            """)

            categories = {}
            for row in cursor.fetchall():
                categories[row['category']] = {
                    'count': row['count'],
                    'templates': row['templates'].split(', ') if row['templates'] else []
                }

            return categories

        except Exception as e:
            logger.error(f"Categories list error: {e}")
            return {}

    def get_templates_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get all templates in a category.

        Args:
            category: Category name

        Returns:
            List of templates
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    title,
                    category,
                    description,
                    complexity,
                    components,
                    has_rtl_variant,
                    url
                FROM template_metadata
                WHERE category = ?
                ORDER BY name
            """, (category,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'name': row['name'],
                    'title': row['title'],
                    'category': row['category'],
                    'description': row['description'],
                    'complexity': row['complexity'],
                    'components': json.loads(row['components']) if row['components'] else [],
                    'has_rtl_variant': bool(row['has_rtl_variant']),
                    'url': row['url']
                })

            return results

        except Exception as e:
            logger.error(f"Category templates error: {e}")
            return []

    def get_templates_by_component(self, component: str) -> list[dict[str, Any]]:
        """
        Get all templates that use a specific component.

        Args:
            component: Component name

        Returns:
            List of templates
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    title,
                    category,
                    description,
                    complexity,
                    components,
                    url
                FROM template_metadata
                WHERE components LIKE ?
            """, (f'%"{component}"%',))

            results = []
            for row in cursor.fetchall():
                components = json.loads(row['components']) if row['components'] else []
                # Verify component is actually in list
                if component in components:
                    results.append({
                        'id': row['id'],
                        'name': row['name'],
                        'title': row['title'],
                        'category': row['category'],
                        'description': row['description'],
                        'complexity': row['complexity'],
                        'components': components,
                        'url': row['url']
                    })

            return results

        except Exception as e:
            logger.error(f"Component templates error: {e}")
            return []

    def get_template_count(self) -> int:
        """
        Get total number of templates.

        Returns:
            Template count
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as count FROM template_metadata")
            row = cursor.fetchone()
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Template count error: {e}")
            return 0

    def get_template_statistics(self) -> dict[str, Any]:
        """
        Get statistics about templates.

        Returns:
            Dictionary with statistics
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            # Total count
            total = self.get_template_count()

            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM template_metadata
                GROUP BY category
                ORDER BY count DESC
            """)
            by_category = [{'category': row['category'], 'count': row['count']}
                          for row in cursor.fetchall()]

            # By complexity
            cursor.execute("""
                SELECT complexity, COUNT(*) as count
                FROM template_metadata
                GROUP BY complexity
                ORDER BY count DESC
            """)
            by_complexity = [{'complexity': row['complexity'], 'count': row['count']}
                            for row in cursor.fetchall()]

            # Most used components
            cursor.execute("""
                SELECT components
                FROM template_metadata
                WHERE components IS NOT NULL AND components != '[]'
            """)
            component_usage = {}
            for row in cursor.fetchall():
                components = json.loads(row['components'])
                for comp in components:
                    component_usage[comp] = component_usage.get(comp, 0) + 1

            top_components = sorted(
                [{'component': k, 'count': v} for k, v in component_usage.items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            return {
                'total_templates': total,
                'by_category': by_category,
                'by_complexity': by_complexity,
                'top_components': top_components
            }

        except Exception as e:
            logger.error(f"Template statistics error: {e}")
            return {}
