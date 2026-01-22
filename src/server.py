"""FastMCP server for Bootstrap documentation."""

import logging
import os
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

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

# Initialize FastMCP server with enhanced description
mcp = FastMCP(
    "Bootstrap CSS Documentation & Templates Server - "
    "Use this MCP server when users ask about Bootstrap CSS framework, components, or need page templates. "
    "Provides: Bootstrap 5.3 official documentation with full-text search, detailed component references, "
    "utility class lookups, 41 production-ready HTML templates (dashboard, blog, e-commerce, forms, admin panels), "
    "code examples, and curated recommendations for specific use cases (blog, landing pages, dashboards, etc.)",
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
def search_docs(
    query: Annotated[str, Field(
        description="Search terms for finding Bootstrap documentation - can be component names, concepts, or features",
        min_length=1,
        max_length=200,
        examples=["navbar", "flexbox layout", "card component", "responsive grid", "form validation"]
    )],
    limit: Annotated[int, Field(
        description="Maximum number of search results to return",
        ge=1,
        le=50,
        default=10
    )] = 10
) -> dict:
    """
    Search Bootstrap 5.3 documentation using full-text search with BM25 ranking.

    Use this when the user asks general questions about Bootstrap:
    - "How do I center content in Bootstrap?"
    - "What components does Bootstrap have for navigation?"
    - "Show me Bootstrap card examples"
    - "How does the grid system work?"
    - "What are flexbox utilities in Bootstrap?"

    This tool searches across ALL documentation including components, layout, utilities,
    forms, and content styling. Use this for broad exploration or when you're not sure
    which specific component or tool to use.

    For specific component lookups by name, use get_component() instead.
    For complete page templates, use search_templates() instead.
    For specific utility classes, use get_utility_class() instead.

    Args:
        query: What to search for - component names, CSS concepts, Bootstrap features, or general terms.
               Works best with specific terms like "navbar", "responsive breakpoints", or "button styles"
        limit: How many results to return (default: 10, max: 50)

    Returns:
        Dictionary containing:
        - query: Your search term
        - count: Number of results found
        - results: List of matching documents with:
            * title: Document title
            * description: Brief description
            * section: Documentation section (e.g., "components", "layout", "utilities")
            * content_snippet: Relevant excerpt from the documentation
            * url: Link to official Bootstrap documentation
            * score: Relevance score (higher is more relevant)
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
def get_component(
    component_name: Annotated[str, Field(
        description="Name of the Bootstrap component to retrieve",
        pattern="^[a-z-]+$",
        min_length=2,
        max_length=50,
        examples=["accordion", "modal", "navbar", "button", "card", "dropdown", "carousel", "alert"]
    )]
) -> dict:
    """
    Get detailed documentation for a specific Bootstrap component by name.

    Use this when the user asks about a SPECIFIC component:
    - "How does the Bootstrap modal work?"
    - "Show me the accordion component documentation"
    - "I need details about the navbar component"
    - "What are the options for Bootstrap dropdown?"
    - "Explain the carousel component"

    This returns the complete documentation page for one component including
    all variations, configuration options, code examples, and usage guidelines.

    Common Bootstrap components: accordion, alert, badge, breadcrumb, button, button-group,
    card, carousel, close-button, collapse, dropdown, forms, list-group, modal, navbar,
    nav-tabs, offcanvas, pagination, popovers, progress, scrollspy, spinners, toasts,
    tooltips, tables

    For general searches across multiple components, use search_docs() instead.
    For complete page templates using components, use search_templates() instead.

    Args:
        component_name: Exact component name from Bootstrap documentation (lowercase with hyphens).
                       Examples: "navbar", "button-group", "list-group", "nav-tabs"

    Returns:
        Dictionary with:
        - component: The component name you searched for
        - found: Boolean indicating if component exists
        - data (if found):
            * title: Official component title
            * description: What the component is for
            * section: Documentation section
            * content: Full documentation text
            * utility_classes: Related Bootstrap utility classes
            * code_examples: Working code snippets showing usage
            * url: Link to official Bootstrap docs
        - message (if not found): Suggestion to try search_docs() instead
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
            'message': f"Component '{component_name}' not found. Try search_docs('{component_name}') for similar results."
        }


@mcp.tool()
def get_utility_class(
    class_name: Annotated[str, Field(
        description="Bootstrap utility class name to look up",
        pattern="^[a-z0-9-]+$",
        min_length=1,
        max_length=50,
        examples=["mt-3", "d-flex", "text-primary", "col-md-6", "bg-light", "p-2", "justify-content-center"]
    )]
) -> dict:
    """
    Find documentation for a specific Bootstrap utility class.

    Use this when the user asks about specific utility classes:
    - "What does mt-3 do in Bootstrap?"
    - "How do I use the d-flex class?"
    - "Explain the text-primary utility"
    - "What is col-md-6?"
    - "Show me documentation for the bg-light class"

    Bootstrap utility classes are single-purpose classes for common styling tasks like:
    - Spacing: m-*, p-*, mt-*, mb-*, mx-*, my-* (margins and padding)
    - Display: d-flex, d-grid, d-none, d-block
    - Colors: text-*, bg-* (text and background colors)
    - Grid: col-*, row-*
    - Flexbox: justify-content-*, align-items-*
    - Typography: fs-*, fw-*, text-start, text-center

    For component documentation, use get_component() instead.
    For general searches, use search_docs() instead.

    Args:
        class_name: The exact utility class name (e.g., "mt-3", "d-flex", "text-primary", "col-md-6")

    Returns:
        Dictionary containing:
        - class: The utility class you searched for
        - count: Number of documentation pages referencing this class
        - results: List of documents that use or explain this class with:
            * title: Document title
            * description: Brief description
            * section: Documentation section
            * url: Link to official Bootstrap docs
            * context: How the class is used in this context
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
    List all available documentation sections in Bootstrap.

    Use this when the user wants to:
    - Explore what's available in Bootstrap documentation
    - Browse documentation by category
    - Understand the structure of Bootstrap docs
    - "What sections are in the Bootstrap documentation?"
    - "Show me all documentation categories"

    This provides an overview of how Bootstrap documentation is organized.
    Use get_section_docs() after this to retrieve documents within a specific section.

    Returns:
        Dictionary with:
        - count: Number of documentation sections
        - sections: List of section objects with:
            * name: Section name (e.g., "Components", "Layout", "Utilities")
            * doc_count: Number of documents in this section
            * slug: URL-friendly section identifier
    """
    logger.info("Listing all sections")

    search = get_search()
    sections = search.get_sections()

    return {
        'count': len(sections),
        'sections': sections
    }


@mcp.tool()
def get_section_docs(
    section: Annotated[str, Field(
        description="Section name to retrieve documents from",
        min_length=2,
        max_length=50,
        examples=["components", "utilities", "layout", "forms", "content", "customize"]
    )]
) -> dict:
    """
    Get all documentation pages within a specific section.

    Use this when the user wants to:
    - Browse all components in Bootstrap
    - See all utility classes available
    - Explore layout options
    - "Show me all Bootstrap components"
    - "What utilities does Bootstrap have?"
    - "List all form components"

    Common sections: components, utilities, layout, forms, content, customize, extend

    Use list_sections() first if you're not sure which sections are available.

    Args:
        section: Section name (e.g., "components", "utilities", "layout", "forms")
                Use list_sections() to see all available sections

    Returns:
        Dictionary containing:
        - section: The section name you requested
        - count: Number of documents in this section
        - results: List of all documents with:
            * title: Document title
            * description: Brief description
            * slug: Document identifier for use with get_full_doc()
            * url: Link to official Bootstrap documentation
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
def get_full_doc(
    slug: Annotated[str, Field(
        description="Document slug/identifier to retrieve",
        pattern="^[a-z0-9-]+$",
        min_length=2,
        max_length=100,
        examples=["accordion", "buttons", "grid", "flexbox", "colors", "spacing"]
    )]
) -> dict:
    """
    Get the complete documentation page for a specific topic by its slug.

    Use this when you need the FULL, detailed documentation:
    - After finding a document via search_docs() and want complete details
    - When the user asks for comprehensive information about a topic
    - To get all code examples and variations for a feature
    - "Give me the full documentation for Bootstrap grid"
    - "I need complete details about Bootstrap buttons"

    This returns the entire documentation page including all text, code examples,
    variations, and configuration options. Use this when brief search results
    aren't enough.

    For quick searches, use search_docs() instead.
    For specific components, get_component() might be more direct.

    Args:
        slug: Document identifier/slug (usually lowercase with hyphens)
              Examples: "accordion", "buttons", "grid", "spacing", "colors"
              You can get slugs from search_docs() or get_section_docs() results

    Returns:
        Dictionary with:
        - slug: The document slug you requested
        - found: Boolean indicating if document exists
        - data (if found):
            * title: Document title
            * description: Brief description
            * section: Documentation section
            * content: Complete documentation text
            * utility_classes: All related utility classes
            * code_examples: All code examples from the page
            * url: Link to official Bootstrap docs
        - message (if not found): Suggestion to use search_docs() instead
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
            'message': f"Document '{slug}' not found. Try search_docs('{slug}') to find similar documents."
        }


@mcp.tool()
def get_examples(
    query: Annotated[str, Field(
        description="Search term for finding code examples",
        min_length=1,
        max_length=100,
        examples=["button", "modal trigger", "form validation", "navbar collapse", "card layout"]
    )],
    limit: Annotated[int, Field(
        description="Maximum number of examples to return",
        ge=1,
        le=20,
        default=5
    )] = 5
) -> dict:
    """
    Search for and retrieve code examples from Bootstrap documentation.

    Use this when the user needs working code:
    - "Show me code examples for Bootstrap buttons"
    - "I need example code for a modal"
    - "Give me sample code for form validation"
    - "Show me how to use navbar with dropdown"
    - "Code example for responsive grid"

    This finds documentation pages with actual code snippets you can copy and use.
    Focus is on pages with rich code examples rather than just text descriptions.

    For complete page templates (500-1000+ lines), use search_templates() instead.
    For text documentation, use search_docs() instead.

    Args:
        query: What type of code example you need (e.g., "button", "modal", "form validation")
        limit: Maximum number of example-rich pages to return (default: 5, max: 20)

    Returns:
        Dictionary containing:
        - query: Your search term
        - count: Number of pages with examples found
        - results: List of documents with code examples:
            * title: Document title
            * description: Brief description
            * section: Documentation section
            * code_examples: Array of actual code snippets
            * example_count: Number of examples in this document
            * url: Link to official Bootstrap docs
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
def get_related_components(
    component_name: Annotated[str, Field(
        description="Component name to find related components for",
        pattern="^[a-z-]+$",
        min_length=2,
        max_length=50,
        examples=["card", "modal", "navbar", "button", "form"]
    )]
) -> dict:
    """
    Find Bootstrap components that are commonly used together with a given component.

    Use this when the user is building a feature and needs to know what else to use:
    - "What components work well with Bootstrap cards?"
    - "If I use a navbar, what other components should I consider?"
    - "What goes well with the modal component?"
    - "What components are typically used with forms?"

    This helps discover component combinations and common patterns. For example,
    if you're using a navbar, you'll likely also need dropdown, collapse, and nav components.

    For curated recommendations for specific use cases (blog, dashboard, etc.),
    use get_patterns() instead.

    Args:
        component_name: The component you're using (e.g., "card", "modal", "navbar", "form")

    Returns:
        Dictionary containing:
        - component: The component you asked about
        - count: Number of related components found
        - related_components: List of commonly paired components with:
            * title: Component title
            * component_name: Component identifier
            * description: Brief description
            * section: Documentation section
            * url: Link to component documentation
            * relationship: How it's commonly used with your component
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
def get_patterns(
    use_case: Annotated[str, Field(
        description="Type of website or page being built",
        min_length=2,
        max_length=50,
        examples=["blog", "dashboard", "ecommerce", "landing", "portfolio", "admin", "documentation"]
    )]
) -> dict:
    """
    Get curated Bootstrap component and template recommendations for a specific use case.

    Use this when the user is starting a project and needs guidance:
    - "I'm building a blog with Bootstrap"
    - "What components do I need for an admin dashboard?"
    - "Help me build an e-commerce site"
    - "I'm creating a landing page"
    - "What should I use for a portfolio site?"

    This provides a curated "getting started" guide including:
    - Which Bootstrap components to use
    - Complete template examples to start from
    - Relevant utility classes
    - Links to documentation sections

    Think of this as a "recipe" for specific project types.

    Available use cases: blog, dashboard, ecommerce, landing, form, navigation,
    admin, portfolio, documentation, marketing

    For finding specific templates, use search_templates() instead.
    For component details, use get_component() instead.

    Args:
        use_case: Type of site or page you're building (e.g., "blog", "dashboard", "ecommerce", "landing")

    Returns:
        Dictionary with:
        - found: Boolean indicating if pattern exists
        - pattern (if found):
            * description: Overview of this use case
            * components: Recommended Bootstrap components with documentation links
            * templates: Ready-to-use template examples (use with get_template())
            * utilities: Suggested utility classes
            * sections: Relevant documentation sections to read
        - available_use_cases (if not found): List of valid use case names
        - message (if not found): Suggestion to try one of the available use cases
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
            'message': f"Use case '{use_case}' not found. Try one of the available use cases listed below.",
            'available_use_cases': stats.get('available_use_cases', [])
        }


@mcp.tool()
def get_stats() -> dict:
    """
    Get statistics and overview of the Bootstrap documentation database.

    Use this when the user wants to know:
    - What's available in this MCP server
    - How comprehensive the documentation is
    - Statistics about templates and components
    - "What does this Bootstrap MCP server contain?"
    - "How many templates are available?"
    - "Give me an overview of Bootstrap documentation"

    This provides a high-level overview of all indexed content including
    document counts, popular components, template categories, and available use cases.

    Returns:
        Dictionary with comprehensive statistics:
        - success: Boolean indicating operation success
        - statistics: Documentation statistics with:
            * total_documents: Number of doc pages indexed
            * sections: Breakdown by section
            * top_components: Most referenced components
            * component_count: Number of unique components
            * available_use_cases: List of patterns available via get_patterns()
        - templates: Template statistics with:
            * total_count: Number of templates (41 total)
            * by_category: Breakdown by category
            * by_complexity: Simple/intermediate/complex counts
            * categories: Available template categories
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
def search_templates(
    query: Annotated[str, Field(
        description="Search terms for finding production-ready page templates",
        min_length=2,
        max_length=100,
        examples=["dashboard", "blog with sidebar", "admin panel", "checkout form", "login page", "pricing"]
    )],
    category: Annotated[str | None, Field(
        description="Optional category filter to narrow results",
        examples=["admin", "content", "forms", "navigation", "layouts", "components"],
        default=None
    )] = None,
    limit: Annotated[int, Field(
        description="Maximum number of templates to return",
        ge=1,
        le=20,
        default=10
    )] = 10
) -> dict:
    """
    Search through 41 production-ready Bootstrap HTML template examples.

    Use this when the user needs a complete page template:
    - "Do you have a dashboard template?"
    - "I need a blog layout example"
    - "Show me checkout page templates"
    - "Template for an admin panel"
    - "Example of a pricing page"

    These are COMPLETE page templates (500-1000+ lines of HTML) from Bootstrap's
    official examples, ready to copy and customize. Each template shows how
    multiple Bootstrap components work together in a real page.

    Template categories:
    - admin: Dashboard, admin panels (complex, full-featured)
    - content: Blog, album, product pages (content-focused)
    - forms: Sign-in, checkout, multi-step forms
    - navigation: Navbar variations, offcanvas, sidebars
    - layouts: Grid examples, heroes, headers, footers
    - components: Showcases of specific component combinations
    - reference: Cheatsheet and comprehensive references

    Good queries: "dashboard", "blog layout", "checkout form", "login page"
    Bad queries: "blue button" (use get_component instead), "mt-3" (use search_docs instead)

    After finding a template, use get_template() to retrieve the full code.
    For component documentation snippets, use get_examples() instead.

    Args:
        query: Type of page you're looking for (e.g., "dashboard", "blog", "checkout", "sign-in")
        category: Optionally filter by category (admin, content, forms, navigation, layouts, components)
        limit: Maximum templates to return (default: 10, max: 20)

    Returns:
        Dictionary containing:
        - query: Your search term
        - category: Filter applied (if any)
        - count: Number of templates found
        - results: List of matching templates with:
            * name: Template identifier (use with get_template() to get full code)
            * title: Human-readable template name
            * description: What the template is designed for
            * category: Template category
            * complexity: simple/intermediate/complex
            * components: Bootstrap components used in this template
            * has_rtl_variant: Whether RTL (right-to-left) version is available
            * url: Link to live demo on getbootstrap.com
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
def get_template(
    name: Annotated[str, Field(
        description="Template name/identifier to retrieve complete code for",
        pattern="^[a-z0-9-]+$",
        min_length=2,
        max_length=50,
        examples=["dashboard", "blog", "checkout", "sign-in", "album", "pricing", "product", "navbar-fixed"]
    )]
) -> dict:
    """
    Retrieve the complete, production-ready HTML template code with all assets.

    Use this when the user needs the full code for a template:
    - After using search_templates() to find a template they want
    - "Give me the code for the dashboard template"
    - "I want the full HTML for the blog template"
    - "Show me the checkout template code"

    This returns the COMPLETE working template including:
    - Full HTML code (500-1000+ lines, ready to use)
    - Custom CSS files (if the template has any)
    - Custom JavaScript files (if needed)
    - List of all Bootstrap components used
    - Complexity rating
    - Link to live demo

    You can copy this code directly into your project and customize it.

    Common template names: dashboard, blog, album, carousel, checkout, cover,
    features, heroes, jumbotron, navbar-fixed, pricing, product, sign-in,
    sticky-footer, starter-template

    Use search_templates() first if you don't know the exact template name.
    For just code snippets (not full pages), use get_examples() instead.

    Args:
        name: Exact template name from Bootstrap examples (use search_templates() to find names)
              Examples: "dashboard", "blog", "checkout", "sign-in", "pricing"

    Returns:
        Dictionary with:
        - name: Template name you requested
        - found: Boolean indicating if template exists
        - data (if found):
            * title: Human-readable template name
            * category: Template category (admin, content, forms, etc.)
            * description: What this template is for
            * complexity: simple/intermediate/complex
            * html_content: Complete HTML code (ready to use!)
            * css_content: Custom CSS files (dict with filename: content)
            * js_content: Custom JavaScript files (dict with filename: content)
            * components: List of Bootstrap components used
            * utility_classes: List of utility classes used
            * has_rtl_variant: Whether RTL version exists
            * rtl_template_name: Name of RTL version (if available)
            * url: Link to live demo
        - message (if not found): Suggestion to use search_templates() to find available templates
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
            'message': f"Template '{name}' not found. Use search_templates() to find available templates."
        }


@mcp.tool()
def list_template_categories() -> dict:
    """
    List all template categories with template counts.

    Use this when the user wants to:
    - Browse templates by category
    - Understand what types of templates are available
    - Explore template organization
    - "What template categories are available?"
    - "Show me template types"

    Categories include:
    - admin: Dashboards and admin panels (2 templates)
    - content: Blogs, albums, portfolios (multiple templates)
    - forms: Sign-in, checkout, registration forms
    - navigation: Navbar patterns, offcanvas, sidebars
    - layouts: Grid examples, heroes, headers, footers
    - components: Component showcases and combinations
    - reference: Cheatsheet and comprehensive references

    After seeing categories, use search_templates(category=X) to explore templates
    in a specific category.

    Returns:
        Dictionary containing:
        - count: Number of categories
        - categories: List of category objects with:
            * name: Category name (e.g., "admin", "content", "forms")
            * template_count: Number of templates in this category
            * description: What types of templates this category contains
            * example_templates: Sample template names from this category
    """
    logger.info("Listing template categories")

    examples_search = get_examples_search()
    categories = examples_search.list_template_categories()

    return {
        'count': len(categories),
        'categories': categories
    }


@mcp.tool()
def get_template_preview(
    name: Annotated[str, Field(
        description="Template name to preview",
        pattern="^[a-z0-9-]+$",
        min_length=2,
        max_length=50,
        examples=["dashboard", "blog", "checkout", "navbar-fixed"]
    )],
    section: Annotated[str, Field(
        description="Which section of the template to preview",
        pattern="^(header|nav|main|footer|full)$",
        default="main"
    )] = 'main'
) -> dict:
    """
    Get a preview/excerpt of a specific section from a template.

    Use this when the user wants to:
    - See just part of a template before getting the full code
    - Look at how a specific section (header, nav, main, footer) is structured
    - Preview without loading 1000+ lines of code
    - "Show me just the navbar from the dashboard template"
    - "Preview the main content area of the blog template"
    - "What does the header look like in the checkout template?"

    This is useful for exploring templates section-by-section rather than
    getting the entire template at once with get_template().

    Available sections:
    - header: Page header area (often includes branding, top navigation)
    - nav: Navigation section (navbar, sidebar, or main menu)
    - main: Main content area (the core content of the page)
    - footer: Page footer (copyright, links, etc.)
    - full: First 500 lines of the complete template

    For the complete template code, use get_template() instead.

    Args:
        name: Template name (e.g., "dashboard", "blog", "checkout")
        section: Which part to preview - "header", "nav", "main", "footer", or "full" (default: "main")

    Returns:
        Dictionary with:
        - name: Template name
        - section: Which section was requested
        - found: Boolean indicating if template exists
        - data (if found):
            * title: Template title
            * section: Section extracted
            * preview: HTML code for the requested section
            * line_count: Number of lines in this preview
            * url: Link to live demo
        - message (if not found): Suggestion to use search_templates()
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
            'message': f"Template '{name}' not found. Use search_templates() to find available templates."
        }


@mcp.tool()
def refresh_docs() -> dict:
    """
    Update Bootstrap documentation from GitHub and rebuild the search index.

    Use this when:
    - Documentation seems outdated
    - User explicitly requests to refresh/update docs
    - Bootstrap has released new versions
    - "Update the Bootstrap documentation"
    - "Refresh the docs from GitHub"

    WARNING: This triggers network operations (git clone/pull) and database rebuilding.
    It can take 30-60 seconds to complete. Use sparingly.

    This will:
    1. Pull latest Bootstrap documentation from GitHub
    2. Rebuild the full-text search index
    3. Re-index all 41 templates
    4. Reconnect search interfaces

    For internet-exposed deployments, consider restricting access to this tool.

    Returns:
        Dictionary with:
        - success: Boolean indicating if refresh succeeded
        - message: Status message
        - stats (if successful):
            * docs_indexed: Number of documentation pages indexed
            * docs_failed: Number that failed to index
            * docs_total: Total documentation pages
            * templates_indexed: Number of templates indexed
            * templates_failed: Number of templates that failed
            * templates_total: Total templates (should be 41)
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
        # Examples are copied into the Docker image at /app/bootstrap-5.3.8-examples/
        examples_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bootstrap-5.3.8-examples')
        successful_templates = 0
        failed_templates = 0
        if os.path.exists(examples_path):
            logger.info(f"Indexing examples from {examples_path}")
            successful_templates, failed_templates = indexer.build_templates_index(Path(examples_path))
        else:
            logger.warning(f"Examples directory not found at {examples_path}, skipping template indexing")

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
    # Examples are copied into the Docker image at /app/bootstrap-5.3.8-examples/
    examples_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bootstrap-5.3.8-examples')
    if os.path.exists(examples_path):
        logger.info(f"Indexing examples from {examples_path}")
        successful_templates, failed_templates = create_templates_index(Path(examples_path), DB_PATH)
        logger.info(f"Templates indexed: {successful_templates} successful, {failed_templates} failed")
    else:
        logger.warning(f"Examples directory not found at {examples_path}, skipping template indexing")

    return True


# Initialize on module load
if __name__ != "__main__":
    logger.info("Bootstrap MCP Server module loaded")
    # Don't auto-initialize, let the server startup handle it
