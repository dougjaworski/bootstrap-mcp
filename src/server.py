"""FastMCP server for Bootstrap documentation."""

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .git_manager import clone_or_update_bootstrap
from .indexer import BootstrapIndexer, create_index, create_templates_index
from .search import BootstrapSearch
from .examples_search import BootstrapExampleSearch

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
DB_PATH = os.path.join(DATA_DIR, 'bootstrap_docs.db')
MCP_PORT = int(os.getenv('MCP_PORT', 8001))
MCP_HOST = os.getenv('MCP_HOST', '0.0.0.0')
MCP_ALLOWED_HOSTS = os.getenv('MCP_ALLOWED_HOSTS', 'localhost:*,127.0.0.1:*,0.0.0.0:*')
allowed_hosts_list = [host.strip() for host in MCP_ALLOWED_HOSTS.split(",")]

# Initialize FastMCP server
mcp = FastMCP(
    "Bootstrap CSS Documentation & Templates - Search Bootstrap 5.3 documentation, components, utility classes, and access 41 production-ready HTML templates (dashboard, blog, checkout, etc.) with full code examples",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts_list,
        allowed_origins=["*"]
    )
)

# Global search interface
_search: BootstrapSearch = None
_examples_search: BootstrapExampleSearch = None


def get_search() -> BootstrapSearch:
    """Get or create the search interface."""
    global _search
    if _search is None:
        _search = BootstrapSearch(DB_PATH)
    return _search


def get_examples_search() -> BootstrapExampleSearch:
    """Get or create the examples search interface."""
    global _examples_search
    if _examples_search is None:
        _examples_search = BootstrapExampleSearch(DB_PATH)
    return _examples_search


@mcp.tool()
def search_docs(query: str, limit: int = 10) -> dict:
    """
    Search Bootstrap documentation using full-text search with BM25 ranking.

    Args:
        query: Search query (supports full-text search)
        limit: Maximum number of results (default: 10)

    Returns:
        Dictionary with search results including title, description, section, and URL
    """
    logger.info(f"Searching docs for: {query} (limit: {limit})")

    search = get_search()
    results = search.search(query, limit)

    return {
        'query': query,
        'count': len(results),
        'results': results
    }


@mcp.tool()
def get_component(component_name: str) -> dict:
    """
    Find documentation for a specific Bootstrap component.

    Args:
        component_name: Name of the component (e.g., 'accordion', 'modal', 'navbar', 'button')

    Returns:
        Dictionary with component documentation, utility classes, code examples, and URL
    """
    logger.info(f"Getting component: {component_name}")

    search = get_search()
    result = search.find_component(component_name)

    if result:
        return {
            'component': component_name,
            'found': True,
            'data': result
        }
    else:
        return {
            'component': component_name,
            'found': False,
            'message': f"Component '{component_name}' not found"
        }


@mcp.tool()
def get_utility_class(class_name: str) -> dict:
    """
    Find documentation for a specific Bootstrap utility class.

    Args:
        class_name: Name of the utility class (e.g., 'mt-3', 'd-flex', 'text-primary', 'col-md-6')

    Returns:
        Dictionary with documents that use this utility class
    """
    logger.info(f"Getting utility class: {class_name}")

    search = get_search()
    results = search.find_utility_class(class_name)

    return {
        'class': class_name,
        'count': len(results),
        'results': results
    }


@mcp.tool()
def list_sections() -> dict:
    """
    List all documentation sections in Bootstrap.

    Returns:
        Dictionary with all sections and document counts
        (e.g., Components, Layout, Utilities, Forms, Content, etc.)
    """
    logger.info("Listing all sections")

    search = get_search()
    sections = search.get_sections()

    return {
        'count': len(sections),
        'sections': sections
    }


@mcp.tool()
def get_section_docs(section: str) -> dict:
    """
    Get all documentation pages in a specific section.

    Args:
        section: Section name (e.g., 'components', 'utilities', 'layout', 'forms')

    Returns:
        Dictionary with all documents in the section
    """
    logger.info(f"Getting docs for section: {section}")

    search = get_search()
    results = search.search_by_section(section)

    return {
        'section': section,
        'count': len(results),
        'results': results
    }


@mcp.tool()
def get_full_doc(slug: str) -> dict:
    """
    Get complete documentation for a specific page by its slug.

    Args:
        slug: Document slug/filename without extension (e.g., 'accordion', 'buttons', 'grid')

    Returns:
        Dictionary with full document content including all metadata
    """
    logger.info(f"Getting full doc: {slug}")

    search = get_search()
    result = search.get_doc_by_slug(slug)

    if result:
        return {
            'slug': slug,
            'found': True,
            'data': result
        }
    else:
        return {
            'slug': slug,
            'found': False,
            'message': f"Document '{slug}' not found"
        }


@mcp.tool()
def get_examples(query: str, limit: int = 5) -> dict:
    """
    Search for code examples in Bootstrap documentation.

    Args:
        query: Search query to find relevant examples (e.g., 'button', 'modal', 'form')
        limit: Maximum number of examples to return (default: 5)

    Returns:
        Dictionary with code examples from documentation
    """
    logger.info(f"Getting examples for: {query} (limit: {limit})")

    search = get_search()
    results = search.get_code_examples(query, limit)

    return {
        'query': query,
        'count': len(results),
        'results': results
    }


@mcp.tool()
def get_related_components(component_name: str) -> dict:
    """
    Get components commonly used together with the specified component.

    Args:
        component_name: Name of the component (e.g., 'card', 'modal', 'navbar')

    Returns:
        Dictionary with related components and their documentation
    """
    logger.info(f"Getting related components for: {component_name}")

    search = get_search()
    results = search.get_related_components(component_name)

    return {
        'component': component_name,
        'count': len(results),
        'related_components': results
    }


@mcp.tool()
def get_patterns(use_case: str) -> dict:
    """
    Get recommended Bootstrap components for a specific use case or pattern.

    Args:
        use_case: Use case name (e.g., 'blog', 'dashboard', 'landing', 'form', 'ecommerce', 'navigation')

    Returns:
        Dictionary with pattern description, recommended components, utilities, and sections
    """
    logger.info(f"Getting pattern for use case: {use_case}")

    search = get_search()
    result = search.get_use_case_pattern(use_case)

    if result:
        return {
            'found': True,
            'pattern': result
        }
    else:
        # Return available use cases if not found
        stats = search.get_statistics()
        return {
            'found': False,
            'message': f"Use case '{use_case}' not found",
            'available_use_cases': stats.get('available_use_cases', [])
        }


@mcp.tool()
def get_stats() -> dict:
    """
    Get statistics about the Bootstrap documentation database.

    Returns:
        Dictionary with statistics including:
        - Total document count
        - Documents by section
        - Top components by utility classes
        - Top components by code examples
        - Available use case patterns
        - Template statistics (count, categories, complexity)
    """
    logger.info("Getting documentation statistics")

    search = get_search()
    stats = search.get_statistics()

    # Add template statistics
    examples_search = get_examples_search()
    template_stats = examples_search.get_template_statistics()

    return {
        'success': True,
        'statistics': stats,
        'templates': template_stats
    }


@mcp.tool()
def search_templates(query: str, category: str = None, limit: int = 10) -> dict:
    """
    Search Bootstrap example templates by name, description, or components.

    Args:
        query: Search query (e.g., 'dashboard', 'blog layout', 'admin panel')
        category: Optional filter ('admin', 'content', 'forms', 'navigation', 'layouts', 'components', 'reference', 'other')
        limit: Maximum results (default: 10)

    Returns:
        List of matching templates with metadata
    """
    logger.info(f"Searching templates for: {query} (category: {category}, limit: {limit})")

    examples_search = get_examples_search()
    results = examples_search.search_templates(query, category, limit)

    return {
        'query': query,
        'category': category,
        'count': len(results),
        'results': results
    }


@mcp.tool()
def get_template(name: str) -> dict:
    """
    Get complete template code and metadata.

    Args:
        name: Template name (e.g., 'dashboard', 'blog', 'checkout')

    Returns:
        Template metadata, HTML code, custom CSS, custom JavaScript
    """
    logger.info(f"Getting template: {name}")

    examples_search = get_examples_search()
    result = examples_search.get_template(name)

    if result:
        return {
            'name': name,
            'found': True,
            'data': result
        }
    else:
        return {
            'name': name,
            'found': False,
            'message': f"Template '{name}' not found"
        }


@mcp.tool()
def list_template_categories() -> dict:
    """
    List all template categories with counts.

    Returns:
        Categories with template counts:
        - admin (dashboard, dashboard-rtl)
        - content (blog, album, cover, product)
        - forms (sign-in, checkout)
        - navigation (navbars, offcanvas, sidebars)
        - layouts (grid, heroes, sticky-footer, headers, footers)
        - components (buttons, badges, dropdowns, modals, carousel)
        - reference (cheatsheet)
    """
    logger.info("Listing template categories")

    examples_search = get_examples_search()
    categories = examples_search.list_template_categories()

    return {
        'count': len(categories),
        'categories': categories
    }


@mcp.tool()
def get_template_preview(name: str, section: str = 'main') -> dict:
    """
    Get code preview for a specific section of the template.

    Args:
        name: Template name
        section: Section to extract ('header', 'nav', 'main', 'footer', 'full')

    Returns:
        Code snippet for the specified section (max 500 lines for 'full')
    """
    logger.info(f"Getting template preview: {name} (section: {section})")

    examples_search = get_examples_search()
    result = examples_search.get_template_preview(name, section)

    if result:
        return {
            'name': name,
            'section': section,
            'found': True,
            'data': result
        }
    else:
        return {
            'name': name,
            'section': section,
            'found': False,
            'message': f"Template '{name}' not found"
        }


@mcp.tool()
def refresh_docs() -> dict:
    """
    Update documentation from GitHub and rebuild the search index.

    This will pull the latest changes from the Bootstrap repository
    and reindex all documentation.

    Returns:
        Dictionary with refresh status and statistics
    """
    logger.info("Refreshing documentation from GitHub")

    try:
        # Clone or update repository
        success, docs_path = clone_or_update_bootstrap(DATA_DIR)

        if not success:
            return {
                'success': False,
                'message': 'Failed to update repository from GitHub'
            }

        # Rebuild index
        indexer = BootstrapIndexer(DB_PATH)
        successful, failed = indexer.build_index(docs_path)

        # Index examples if folder exists
        examples_path = os.path.join(DATA_DIR, 'bootstrap-5.3.8-examples')
        successful_templates = 0
        failed_templates = 0
        if os.path.exists(examples_path):
            logger.info(f"Indexing examples from {examples_path}")
            successful_templates, failed_templates = indexer.build_templates_index(Path(examples_path))

        indexer.close()

        # Reconnect search interfaces
        global _search, _examples_search
        if _search:
            _search.close()
            _search = None
        if _examples_search:
            _examples_search.close()
            _examples_search = None

        return {
            'success': True,
            'message': 'Documentation refreshed successfully',
            'stats': {
                'docs_indexed': successful,
                'docs_failed': failed,
                'docs_total': successful + failed,
                'templates_indexed': successful_templates,
                'templates_failed': failed_templates,
                'templates_total': successful_templates + failed_templates
            }
        }

    except Exception as e:
        logger.error(f"Error refreshing docs: {e}")
        return {
            'success': False,
            'message': f'Error refreshing documentation: {str(e)}'
        }


def initialize_server() -> bool:
    """
    Initialize the server by cloning/updating the repository and building the index.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Initializing Bootstrap MCP Server")

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if database already exists
    db_exists = os.path.exists(DB_PATH)

    if db_exists:
        logger.info(f"Database found at {DB_PATH}")
        # Verify it has data
        indexer = BootstrapIndexer(DB_PATH)
        indexer.connect()
        doc_count = indexer.get_document_count()
        indexer.close()

        if doc_count > 0:
            logger.info(f"Database contains {doc_count} documents, skipping initialization")
            return True

    # Clone or update repository
    logger.info("Cloning/updating Bootstrap repository")
    success, docs_path = clone_or_update_bootstrap(DATA_DIR)

    if not success:
        logger.error("Failed to clone/update repository")
        return False

    # Build index
    logger.info(f"Building search index from {docs_path}")
    successful, failed = create_index(docs_path, DB_PATH)

    if successful > 0:
        logger.info(f"Initialization complete: {successful} documents indexed, {failed} failed")
    else:
        logger.error("Failed to index any documents")
        return False

    # Index examples if folder exists
    examples_path = os.path.join(DATA_DIR, 'bootstrap-5.3.8-examples')
    if os.path.exists(examples_path):
        logger.info(f"Indexing examples from {examples_path}")
        successful_templates, failed_templates = create_templates_index(Path(examples_path), DB_PATH)
        logger.info(f"Templates indexed: {successful_templates} successful, {failed_templates} failed")

    return True


# Initialize on module load
if __name__ != "__main__":
    logger.info("Bootstrap MCP Server module loaded")
    # Don't auto-initialize, let the server startup handle it
