"""SQLite FTS5 indexer for Bootstrap documentation."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .parser import BootstrapDocParser

logger = logging.getLogger(__name__)


class BootstrapIndexer:
    """Indexes Bootstrap documentation using SQLite FTS5."""

    def __init__(self, db_path: str):
        """
        Initialize the indexer.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_database(self) -> None:
        """Create database tables and indexes."""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        # Create FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                title,
                description,
                content,
                section,
                component_name,
                tokenize = 'porter unicode61'
            )
        """)

        # Create metadata table with Bootstrap-specific fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                section TEXT,
                component_name TEXT,
                utility_classes TEXT,
                code_examples TEXT,
                aliases TEXT,
                toc BOOLEAN,
                url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filepath
            ON doc_metadata(filepath)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_component
            ON doc_metadata(component_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_section
            ON doc_metadata(section)
        """)

        self.conn.commit()
        logger.info("Database initialized successfully")

    def clear_index(self) -> None:
        """Clear all indexed documents."""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM docs_fts")
        cursor.execute("DELETE FROM doc_metadata")
        self.conn.commit()
        logger.info("Index cleared")

    def index_document(self, doc: dict[str, Any]) -> bool:
        """
        Index a single document.

        Args:
            doc: Parsed document dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            # Insert into metadata table
            cursor.execute("""
                INSERT OR REPLACE INTO doc_metadata
                (filepath, title, description, section, component_name,
                 utility_classes, code_examples, aliases, toc, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc['filepath'],
                doc['title'],
                doc['description'],
                doc['section'],
                doc['component_name'],
                json.dumps(doc['utility_classes']),
                json.dumps(doc['code_examples']),
                json.dumps(doc['aliases']),
                doc['toc'],
                doc['url']
            ))

            # Get the row id
            metadata_id = cursor.lastrowid

            # Insert into FTS5 table
            cursor.execute("""
                INSERT OR REPLACE INTO docs_fts
                (rowid, title, description, content, section, component_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metadata_id,
                doc['title'],
                doc['description'],
                doc['content'],
                doc['section'],
                doc['component_name']
            ))

            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error indexing document {doc.get('filepath', 'unknown')}: {e}")
            return False

    def build_index(self, docs_path: Path) -> tuple[int, int]:
        """
        Build the complete index from the documentation directory.

        Args:
            docs_path: Path to the Bootstrap documentation directory

        Returns:
            Tuple of (successful_count, failed_count)
        """
        logger.info(f"Building index from {docs_path}")

        # Initialize database
        self.initialize_database()

        # Clear existing index
        self.clear_index()

        # Parse all documents
        parser = BootstrapDocParser(docs_path)
        documents = parser.parse_directory(recursive=True)

        # Index each document
        successful = 0
        failed = 0

        for doc in documents:
            if self.index_document(doc):
                successful += 1
            else:
                failed += 1

        logger.info(f"Indexing complete: {successful} successful, {failed} failed")
        return successful, failed

    def get_document_count(self) -> int:
        """
        Get the total number of indexed documents.

        Returns:
            Document count
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM doc_metadata")
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_sections(self) -> list[str]:
        """
        Get all unique sections in the documentation.

        Returns:
            List of section names
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT section
            FROM doc_metadata
            WHERE section IS NOT NULL AND section != ''
            ORDER BY section
        """)

        return [row[0] for row in cursor.fetchall()]

    def get_components(self) -> list[str]:
        """
        Get all unique components in the documentation.

        Returns:
            List of component names
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT component_name
            FROM doc_metadata
            WHERE component_name IS NOT NULL AND component_name != ''
            ORDER BY component_name
        """)

        return [row[0] for row in cursor.fetchall()]


def create_index(docs_path: Path, db_path: str) -> tuple[int, int]:
    """
    Convenience function to create a new index.

    Args:
        docs_path: Path to the documentation directory
        db_path: Path to the database file

    Returns:
        Tuple of (successful_count, failed_count)
    """
    indexer = BootstrapIndexer(db_path)
    try:
        return indexer.build_index(docs_path)
    finally:
        indexer.close()
