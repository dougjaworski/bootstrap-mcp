"""Search functions for Bootstrap documentation."""

import json
import logging
import sqlite3
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
        Full-text search using FTS5 with BM25 ranking.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
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

        except Exception as e:
            logger.error(f"Search error: {e}")
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
