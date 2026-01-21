"""Search functions for Bootstrap documentation."""

import json
import logging
import sqlite3
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Search query synonyms for better results
SEARCH_SYNONYMS = {
    'blog': ['article', 'post', 'content', 'typography'],
    'article': ['blog', 'post', 'content', 'typography'],
    'post': ['blog', 'article', 'content'],
    'layout': ['grid', 'container', 'columns', 'row'],
    'template': ['layout', 'pattern', 'example'],
    'pattern': ['template', 'layout', 'example'],
    'form': ['input', 'select', 'checkbox', 'validation'],
    'input': ['form', 'text', 'field'],
    'navbar': ['nav', 'navigation', 'menu', 'header'],
    'navigation': ['nav', 'navbar', 'menu'],
    'menu': ['nav', 'navbar', 'navigation', 'dropdown'],
    'header': ['navbar', 'nav', 'top'],
    'footer': ['bottom', 'copyright'],
    'sidebar': ['aside', 'column', 'offcanvas'],
    'dialog': ['modal', 'popup', 'alert'],
    'popup': ['modal', 'dialog', 'popover'],
    'image': ['img', 'picture', 'figure', 'thumbnail'],
    'picture': ['image', 'img', 'figure'],
    'photo': ['image', 'img', 'picture'],
    'caption': ['figure', 'figcaption'],
    'table': ['grid', 'data', 'rows'],
    'list': ['items', 'ul', 'ol'],
    'button': ['btn', 'action', 'submit'],
    'link': ['anchor', 'url', 'href'],
}


def expand_query_with_synonyms(query: str) -> str:
    """
    Expand search query with synonyms for better matches.
    Uses FTS5 OR syntax without parentheses.

    Args:
        query: Original search query

    Returns:
        Expanded query with OR conditions for synonyms
    """
    words = query.lower().split()
    all_terms = []

    for word in words:
        # Add the original word
        all_terms.append(word)

        # Add synonyms if available
        if word in SEARCH_SYNONYMS:
            all_terms.extend(SEARCH_SYNONYMS[word][:2])  # Limit to 2 synonyms per word

    # Join all terms with OR for FTS5
    return ' OR '.join(all_terms)


# Component relationships - components commonly used together
COMPONENT_RELATIONSHIPS = {
    'card': ['grid', 'images', 'button-group', 'list-group', 'badge'],
    'modal': ['buttons', 'forms', 'grid'],
    'navbar': ['nav', 'dropdown', 'collapse', 'forms'],
    'nav': ['navbar', 'dropdown', 'list-group'],
    'button': ['button-group', 'dropdown', 'forms', 'spinners'],
    'button-group': ['buttons', 'dropdown'],
    'dropdown': ['buttons', 'navbar', 'nav'],
    'forms': ['input-group', 'validation', 'buttons'],
    'grid': ['containers', 'columns', 'gutters'],
    'carousel': ['images', 'buttons'],
    'accordion': ['collapse', 'card'],
    'list-group': ['badge', 'buttons'],
    'offcanvas': ['navbar', 'buttons'],
    'table': ['pagination', 'forms'],
    'pagination': ['nav', 'table'],
    'breadcrumb': ['nav'],
    'alert': ['buttons', 'close-button'],
    'toast': ['buttons', 'close-button'],
    'badge': ['buttons', 'card', 'list-group'],
    'progress': ['spinners'],
    'spinners': ['buttons', 'progress'],
}

# Use case patterns - common Bootstrap patterns for specific purposes
USE_CASE_PATTERNS = {
    'blog': {
        'description': 'Components for blog posts and article layouts',
        'components': ['typography', 'images', 'card', 'grid', 'figures', 'breadcrumb'],
        'templates': ['blog', 'blog-rtl', 'album', 'album-rtl'],
        'utilities': ['spacing', 'text', 'colors'],
        'sections': ['content', 'components', 'layout']
    },
    'article': {
        'description': 'Article and content-heavy page layouts',
        'components': ['typography', 'images', 'figures', 'blockquote', 'grid'],
        'templates': ['blog', 'blog-rtl'],
        'utilities': ['spacing', 'text', 'display'],
        'sections': ['content', 'layout']
    },
    'dashboard': {
        'description': 'Dashboard and admin panel layouts',
        'components': ['card', 'grid', 'navbar', 'offcanvas', 'table', 'badge', 'progress'],
        'templates': ['dashboard', 'dashboard-rtl', 'sidebars'],
        'utilities': ['flex', 'spacing', 'colors', 'sizing'],
        'sections': ['components', 'layout', 'utilities']
    },
    'landing': {
        'description': 'Landing page and marketing site patterns',
        'components': ['navbar', 'carousel', 'card', 'grid', 'buttons', 'modal'],
        'templates': ['cover', 'heroes', 'features', 'pricing', 'product'],
        'utilities': ['spacing', 'text', 'display', 'flex'],
        'sections': ['components', 'layout', 'content']
    },
    'form': {
        'description': 'Form layouts and validation patterns',
        'components': ['forms', 'input-group', 'validation', 'buttons', 'grid'],
        'templates': ['sign-in', 'checkout', 'checkout-rtl'],
        'utilities': ['spacing', 'sizing'],
        'sections': ['forms', 'components']
    },
    'navigation': {
        'description': 'Navigation patterns and menus',
        'components': ['navbar', 'nav', 'breadcrumb', 'pagination', 'dropdown'],
        'templates': ['navbars', 'navbars-offcanvas', 'navbars-static', 'offcanvas-navbar', 'sidebars', 'breadcrumbs'],
        'utilities': ['flex', 'spacing', 'text'],
        'sections': ['components']
    },
    'ecommerce': {
        'description': 'E-commerce product listings and shopping',
        'components': ['card', 'grid', 'buttons', 'badge', 'modal', 'carousel'],
        'templates': ['product', 'checkout', 'checkout-rtl', 'pricing', 'album'],
        'utilities': ['spacing', 'flex', 'colors'],
        'sections': ['components', 'layout']
    },
    'admin': {
        'description': 'Admin panel and data management interfaces',
        'components': ['table', 'card', 'navbar', 'offcanvas', 'forms', 'badge', 'dropdown'],
        'templates': ['dashboard', 'dashboard-rtl'],
        'utilities': ['flex', 'spacing', 'colors', 'sizing'],
        'sections': ['components', 'layout', 'utilities']
    },
}


class BootstrapSearch:
    """Search interface for Bootstrap documentation."""

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

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Full-text search using FTS5 with BM25 ranking and synonym expansion.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            # Expand query with synonyms for better matches
            expanded_query = expand_query_with_synonyms(query)
            logger.debug(f"Expanded query '{query}' to '{expanded_query}'")

            # Use FTS5 MATCH for full-text search with BM25 ranking and snippet extraction
            cursor.execute("""
                SELECT
                    m.id,
                    m.filepath,
                    m.title,
                    m.description,
                    m.section,
                    m.component_name,
                    m.url,
                    snippet(docs_fts, 2, '<mark>', '</mark>', '...', 64) as snippet,
                    bm25(docs_fts) as relevance_score
                FROM docs_fts fts
                JOIN doc_metadata m ON m.id = fts.rowid
                WHERE docs_fts MATCH ?
                ORDER BY bm25(docs_fts)
                LIMIT ?
            """, (expanded_query, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'filepath': row['filepath'],
                    'title': row['title'],
                    'description': row['description'],
                    'section': row['section'],
                    'component_name': row['component_name'],
                    'url': row['url'],
                    'snippet': row['snippet'],
                    'relevance_score': abs(row['relevance_score'])
                })

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            # Try fallback without synonym expansion if FTS5 syntax error
            try:
                cursor.execute("""
                    SELECT
                        m.id,
                        m.filepath,
                        m.title,
                        m.description,
                        m.section,
                        m.component_name,
                        m.url,
                        snippet(docs_fts, 2, '<mark>', '</mark>', '...', 64) as snippet,
                        bm25(docs_fts) as relevance_score
                    FROM docs_fts fts
                    JOIN doc_metadata m ON m.id = fts.rowid
                    WHERE docs_fts MATCH ?
                    ORDER BY bm25(docs_fts)
                    LIMIT ?
                """, (query, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row['id'],
                        'filepath': row['filepath'],
                        'title': row['title'],
                        'description': row['description'],
                        'section': row['section'],
                        'component_name': row['component_name'],
                        'url': row['url'],
                        'snippet': row['snippet'],
                        'relevance_score': abs(row['relevance_score'])
                    })

                return results
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
                return []

    def find_component(self, component_name: str) -> Optional[dict[str, Any]]:
        """
        Find a specific component by name.

        Args:
            component_name: Name of the component

        Returns:
            Component documentation or None
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    filepath,
                    title,
                    description,
                    section,
                    component_name,
                    utility_classes,
                    code_examples,
                    url
                FROM doc_metadata
                WHERE component_name = ?
                LIMIT 1
            """, (component_name,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'filepath': row['filepath'],
                    'title': row['title'],
                    'description': row['description'],
                    'section': row['section'],
                    'component_name': row['component_name'],
                    'utility_classes': json.loads(row['utility_classes']) if row['utility_classes'] else [],
                    'code_examples': json.loads(row['code_examples']) if row['code_examples'] else [],
                    'url': row['url']
                }
            return None

        except Exception as e:
            logger.error(f"Component search error: {e}")
            return None

    def find_utility_class(self, class_name: str) -> list[dict[str, Any]]:
        """
        Find documentation for a specific utility class.

        Args:
            class_name: Name of the utility class

        Returns:
            List of documents that use this class
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    filepath,
                    title,
                    description,
                    section,
                    utility_classes,
                    url
                FROM doc_metadata
                WHERE utility_classes LIKE ?
            """, (f'%"{class_name}"%',))

            results = []
            for row in cursor.fetchall():
                utility_classes = json.loads(row['utility_classes']) if row['utility_classes'] else []

                # Verify the class is actually in the list
                if class_name in utility_classes:
                    results.append({
                        'id': row['id'],
                        'filepath': row['filepath'],
                        'title': row['title'],
                        'description': row['description'],
                        'section': row['section'],
                        'utility_classes': utility_classes,
                        'url': row['url']
                    })

            return results

        except Exception as e:
            logger.error(f"Utility class search error: {e}")
            return []

    def get_sections(self) -> list[dict[str, Any]]:
        """
        List all documentation sections.

        Returns:
            List of sections with document counts
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    section,
                    COUNT(*) as count
                FROM doc_metadata
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section
                ORDER BY section
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'section': row['section'],
                    'count': row['count']
                })

            return results

        except Exception as e:
            logger.error(f"Section list error: {e}")
            return []

    def search_by_section(self, section: str) -> list[dict[str, Any]]:
        """
        Get all documents in a specific section.

        Args:
            section: Section name

        Returns:
            List of documents in the section
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id,
                    filepath,
                    title,
                    description,
                    section,
                    component_name,
                    url
                FROM doc_metadata
                WHERE section = ?
                ORDER BY title
            """, (section,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'filepath': row['filepath'],
                    'title': row['title'],
                    'description': row['description'],
                    'section': row['section'],
                    'component_name': row['component_name'],
                    'url': row['url']
                })

            return results

        except Exception as e:
            logger.error(f"Section search error: {e}")
            return []

    def get_doc_by_slug(self, slug: str) -> Optional[dict[str, Any]]:
        """
        Get a document by its slug (filename without extension).

        Args:
            slug: Document slug

        Returns:
            Complete document or None
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    m.id,
                    m.filepath,
                    m.title,
                    m.description,
                    m.section,
                    m.component_name,
                    m.utility_classes,
                    m.code_examples,
                    m.aliases,
                    m.toc,
                    m.url,
                    fts.content
                FROM doc_metadata m
                JOIN docs_fts fts ON m.id = fts.rowid
                WHERE m.filepath LIKE ?
                LIMIT 1
            """, (f'%/{slug}.mdx',))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'filepath': row['filepath'],
                    'title': row['title'],
                    'description': row['description'],
                    'section': row['section'],
                    'component_name': row['component_name'],
                    'utility_classes': json.loads(row['utility_classes']) if row['utility_classes'] else [],
                    'code_examples': json.loads(row['code_examples']) if row['code_examples'] else [],
                    'aliases': json.loads(row['aliases']) if row['aliases'] else [],
                    'toc': bool(row['toc']),
                    'url': row['url'],
                    'content': row['content']
                }
            return None

        except Exception as e:
            logger.error(f"Document lookup error: {e}")
            return None

    def get_code_examples(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Search for code examples matching a query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of code examples
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    m.id,
                    m.filepath,
                    m.title,
                    m.section,
                    m.component_name,
                    m.code_examples,
                    m.url
                FROM doc_metadata m
                WHERE m.code_examples != '[]'
                AND (
                    m.title LIKE ?
                    OR m.component_name LIKE ?
                    OR m.code_examples LIKE ?
                )
                LIMIT ?
            """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))

            results = []
            for row in cursor.fetchall():
                code_examples = json.loads(row['code_examples']) if row['code_examples'] else []

                if code_examples:
                    results.append({
                        'id': row['id'],
                        'filepath': row['filepath'],
                        'title': row['title'],
                        'section': row['section'],
                        'component_name': row['component_name'],
                        'code_examples': code_examples,
                        'url': row['url']
                    })

            return results

        except Exception as e:
            logger.error(f"Code examples search error: {e}")
            return []

    def get_related_components(self, component_name: str) -> list[dict[str, Any]]:
        """
        Get components commonly used with the specified component.

        Args:
            component_name: Name of the component

        Returns:
            List of related components with their documentation
        """
        # Get related component names from the relationships map
        related_names = COMPONENT_RELATIONSHIPS.get(component_name, [])

        if not related_names:
            return []

        self.connect()
        cursor = self.conn.cursor()

        try:
            # Build query for related components
            placeholders = ','.join('?' * len(related_names))
            cursor.execute(f"""
                SELECT
                    id,
                    filepath,
                    title,
                    description,
                    section,
                    component_name,
                    url
                FROM doc_metadata
                WHERE component_name IN ({placeholders})
                ORDER BY title
            """, related_names)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'filepath': row['filepath'],
                    'title': row['title'],
                    'description': row['description'],
                    'section': row['section'],
                    'component_name': row['component_name'],
                    'url': row['url']
                })

            return results

        except Exception as e:
            logger.error(f"Related components error: {e}")
            return []

    def get_use_case_pattern(self, use_case: str) -> Optional[dict[str, Any]]:
        """
        Get component recommendations for a specific use case.

        Args:
            use_case: Use case name (e.g., 'blog', 'dashboard', 'landing')

        Returns:
            Pattern information with recommended components
        """
        pattern = USE_CASE_PATTERNS.get(use_case.lower())

        if not pattern:
            return None

        # Fetch actual component details
        self.connect()
        cursor = self.conn.cursor()

        try:
            component_details = []
            if pattern['components']:
                placeholders = ','.join('?' * len(pattern['components']))
                cursor.execute(f"""
                    SELECT
                        title,
                        description,
                        component_name,
                        url
                    FROM doc_metadata
                    WHERE component_name IN ({placeholders})
                    ORDER BY title
                """, pattern['components'])

                for row in cursor.fetchall():
                    component_details.append({
                        'title': row['title'],
                        'description': row['description'],
                        'component_name': row['component_name'],
                        'url': row['url']
                    })

            return {
                'use_case': use_case,
                'description': pattern['description'],
                'components': component_details,
                'templates': pattern.get('templates', []),
                'utilities': pattern['utilities'],
                'sections': pattern['sections']
            }

        except Exception as e:
            logger.error(f"Use case pattern error: {e}")
            return None

    def get_statistics(self) -> dict[str, Any]:
        """
        Get database statistics and popular items.

        Returns:
            Dictionary with various statistics
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            # Total document count
            cursor.execute("SELECT COUNT(*) as total FROM doc_metadata")
            total_docs = cursor.fetchone()['total']

            # Documents by section
            cursor.execute("""
                SELECT section, COUNT(*) as count
                FROM doc_metadata
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section
                ORDER BY count DESC
            """)
            sections = [{'section': row['section'], 'count': row['count']} for row in cursor.fetchall()]

            # Components with most utility classes
            cursor.execute("""
                SELECT
                    title,
                    component_name,
                    utility_classes,
                    url
                FROM doc_metadata
                WHERE utility_classes IS NOT NULL AND utility_classes != '[]'
            """)
            top_components = []
            for row in cursor.fetchall():
                try:
                    classes = json.loads(row['utility_classes'])
                    top_components.append({
                        'title': row['title'],
                        'component_name': row['component_name'],
                        'utility_class_count': len(classes),
                        'url': row['url']
                    })
                except:
                    pass
            # Sort by count and limit to top 10
            top_components.sort(key=lambda x: x['utility_class_count'], reverse=True)
            top_components = top_components[:10]

            # Components with most code examples
            cursor.execute("""
                SELECT
                    title,
                    component_name,
                    code_examples,
                    url
                FROM doc_metadata
                WHERE code_examples IS NOT NULL AND code_examples != '[]'
            """)
            top_examples = []
            for row in cursor.fetchall():
                try:
                    examples = json.loads(row['code_examples'])
                    top_examples.append({
                        'title': row['title'],
                        'component_name': row['component_name'],
                        'example_count': len(examples),
                        'url': row['url']
                    })
                except:
                    pass
            # Sort by count and limit to top 10
            top_examples.sort(key=lambda x: x['example_count'], reverse=True)
            top_examples = top_examples[:10]

            # Available use cases
            use_cases = [
                {'use_case': uc, 'description': pattern['description']}
                for uc, pattern in USE_CASE_PATTERNS.items()
            ]

            return {
                'total_documents': total_docs,
                'sections': sections,
                'top_components_by_utilities': top_components,
                'top_components_by_examples': top_examples,
                'available_use_cases': use_cases
            }

        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {}
