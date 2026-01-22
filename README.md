# Bootstrap MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides AI assistants with comprehensive access to Bootstrap CSS documentation **plus 41 production-ready HTML templates**. This enables Claude and other MCP-compatible AI assistants to accurately reference Bootstrap documentation, provide code examples, suggest utility classes, and deliver complete page templates for your projects.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and designed for both local and remote access via HTTP transport.

---

## Table of Contents

- [Why Use This?](#why-use-this)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Using Docker Compose (Recommended)](#using-docker-compose-recommended)
  - [Manual Docker Build](#manual-docker-build)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Configuration Examples](#configuration-examples)
- [Connecting from Claude Code](#connecting-from-claude-code)
- [Available Tools](#available-tools)
  - [Documentation Tools (11)](#documentation-tools-11)
  - [Template Tools (4)](#template-tools-4)
- [Template Library](#template-library)
- [Architecture](#architecture)
- [Development](#development)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

---

## Why Use This?

When working with Bootstrap, AI assistants often:
- ❌ Suggest outdated component patterns from Bootstrap 3 or 4
- ❌ Miss newer Bootstrap 5 features and utility classes
- ❌ Can't provide complete, production-ready page templates
- ❌ Don't reference specific examples from official documentation

This MCP server solves these problems by giving AI assistants direct access to:
- ✅ Complete, up-to-date Bootstrap 5.3 documentation
- ✅ Real code examples from official docs
- ✅ **41 production-ready HTML templates** (dashboard, blog, checkout, etc.)
- ✅ Component definitions and usage patterns
- ✅ Utility class documentation with responsive variants
- ✅ Use case recommendations (blog, dashboard, ecommerce, etc.)

---

## Features

### Documentation Features
- 🔍 **Full-text search** using SQLite FTS5 with BM25 ranking and synonym expansion
- 🎯 **Component lookup** to find specific Bootstrap components (accordion, modal, navbar, etc.)
- 📚 **Section browsing** to explore documentation by category
- 📖 **Complete documentation retrieval** by slug for in-depth understanding
- 💻 **Code example extraction** from JSX `<Example>` components
- 🔗 **Related components** discovery for commonly used combinations
- 🎨 **Use case patterns** with component recommendations for specific scenarios
- 📊 **Statistics** about documentation coverage and popular components

### Template Features ⭐ NEW
- 🎨 **41 production-ready templates** from Bootstrap's official examples
- 🔍 **Template search** with category filtering
- 📦 **Complete template code** including HTML, custom CSS, and JavaScript
- 🗂️ **8 template categories**: admin, content, forms, navigation, layouts, components, reference, other
- 📑 **Section preview** to view specific parts (header, nav, main, footer)
- 🏷️ **Complexity ratings** (simple, intermediate, complex)
- 🌍 **RTL variant detection** for right-to-left language support

### Infrastructure
- 🔄 **Auto-updating** documentation from the official Bootstrap repository
- 🐳 **Docker-based** deployment with volume persistence
- 🌐 **HTTP transport** for local and remote access
- 📈 **Synonym expansion** for better search results

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/dougjaworski/bootstrap-mcp.git
cd bootstrap-mcp

# Copy and customize the environment configuration
cp .env.example .env
# Edit .env with your preferred settings (optional)

# Build and start the server
docker-compose up -d

# View logs to monitor initialization
docker-compose logs -f

# Stop the server
docker-compose down
```

**On first run, the server will:**
1. Clone the Bootstrap documentation repository (~30 seconds)
2. Parse all MDX files and build the search index (~45 seconds)
3. Index 41 HTML templates with metadata extraction (~15 seconds)
4. Start the MCP server on the configured port (default: 8001)

**Total initialization time:** 1-2 minutes

### Manual Docker Build

```bash
# Build the image
docker build -t bootstrap-mcp .

# Run the container
docker run -d \
  -p 8001:8001 \
  -v bootstrap-docs:/app/data \
  --env-file .env \
  --name bootstrap-mcp \
  bootstrap-mcp
```

---

## Configuration

The server is configured using environment variables. Copy `.env.example` to `.env` and customize as needed:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8001` | Port the MCP server listens on |
| `MCP_HOST` | `0.0.0.0` | Host the MCP server binds to |
| `MCP_ALLOWED_HOSTS` | `localhost:*,127.0.0.1:*,0.0.0.0:*` | Comma-separated list of allowed hostnames for DNS rebinding protection |
| `DATA_DIR` | `/app/data` | Directory where documentation and database are stored |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Configuration Examples

**Local use only:**
```env
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*
```

**Remote access from specific host:**
```env
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,myserver:*,myserver.example.com:*
```

**Custom port (e.g., running alongside Tailwind MCP):**
```env
MCP_PORT=8001  # Bootstrap
# Tailwind MCP typically uses 8000
```

---

## Connecting from Claude Code

Add the following to your Claude Code MCP settings (`.mcp.json`):

**Local connection:**
```json
{
  "mcpServers": {
    "bootstrap-docs": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

**Remote connection:**
```json
{
  "mcpServers": {
    "bootstrap-docs": {
      "type": "http",
      "url": "http://your-server-hostname:8001/mcp"
    }
  }
}
```

**Running both Bootstrap and Tailwind MCP:**
```json
{
  "mcpServers": {
    "tailwind-css": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    },
    "bootstrap-docs": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

> **Note:** When connecting remotely, make sure `your-server-hostname` is included in the `MCP_ALLOWED_HOSTS` environment variable.

---

## Available Tools

The server provides **15 MCP tools** for accessing Bootstrap documentation and templates.

### Documentation Tools (11)

#### 1. `search_docs`
Search the Bootstrap documentation using full-text search with synonym expansion.

**Parameters:**
- `query` (string): Search query (supports FTS5 syntax, synonyms like "blog" → "article", "post")
- `limit` (int, optional): Maximum results to return (default: 10)

**Returns:** List of search results with snippets, URLs, and relevance scores.

#### 2. `get_component`
Find documentation for a specific Bootstrap component.

**Parameters:**
- `component_name` (string): Component name (e.g., "accordion", "modal", "navbar", "button")

**Returns:** Complete component documentation with utility classes and code examples.

**Supported components:** accordion, alert, badge, breadcrumb, button, button-group, card, carousel, close-button, collapse, dropdown, list-group, modal, nav, navbar, offcanvas, pagination, placeholder, popovers, progress, scrollspy, spinners, toasts, tooltips

#### 3. `get_utility_class`
Find documentation for a specific Bootstrap utility class.

**Parameters:**
- `class_name` (string): Utility class name (e.g., "mt-3", "d-flex", "text-primary", "col-md-6")

**Returns:** List of documentation pages that use this utility class.

**Supported utility patterns:**
- **Spacing:** `m-*`, `mt-*`, `mb-*`, `ms-*`, `me-*`, `mx-*`, `my-*`, `p-*`, `pt-*`, `pb-*`, `ps-*`, `pe-*`, `px-*`, `py-*`
- **Display:** `d-none`, `d-block`, `d-flex`, `d-grid`, `d-inline`, etc.
- **Responsive:** `d-{sm|md|lg|xl|xxl}-*`
- **Flexbox:** `flex-row`, `flex-column`, `justify-content-*`, `align-items-*`
- **Grid:** `col-*`, `col-{sm|md|lg|xl|xxl}-*`
- **Colors:** `text-*`, `bg-*`
- **Borders:** `border-*`, `rounded-*`
- **Sizing:** `w-*`, `h-*`

#### 4. `list_sections`
List all documentation sections.

**Returns:** All sections with document counts (Components, Layout, Utilities, Forms, Content, Customize, etc.).

#### 5. `get_section_docs`
Get all documentation pages in a specific section.

**Parameters:**
- `section` (string): Section name (e.g., "components", "utilities", "layout", "forms")

**Returns:** List of all documents in the section.

#### 6. `get_full_doc`
Get complete documentation by slug.

**Parameters:**
- `slug` (string): Document slug/filename without extension (e.g., "accordion", "buttons", "grid")

**Returns:** Full document content with all metadata, utility classes, and code examples.

#### 7. `get_examples`
Search for code examples in Bootstrap documentation.

**Parameters:**
- `query` (string): Search query to find relevant examples (e.g., "button", "modal", "form")
- `limit` (int, optional): Maximum number of examples to return (default: 5)

**Returns:** HTML/CSS code examples extracted from `<Example>` JSX components.

#### 8. `get_related_components`
Get components commonly used together with the specified component.

**Parameters:**
- `component_name` (string): Name of the component (e.g., "card", "modal", "navbar")

**Returns:** List of related components with their documentation URLs.

#### 9. `get_patterns`
Get recommended Bootstrap components for a specific use case or pattern.

**Parameters:**
- `use_case` (string): Use case name (e.g., "blog", "dashboard", "landing", "form", "ecommerce", "navigation", "admin")

**Returns:** Pattern description, recommended components, **suggested templates**, utilities, and sections.

**Supported use cases:** blog, article, dashboard, landing, form, navigation, ecommerce, admin

#### 10. `get_stats`
Get statistics about the Bootstrap documentation database.

**Returns:** Total document count, documents by section, top components by utility classes/examples, available use cases, and **template statistics**.

#### 11. `refresh_docs`
Update documentation from GitHub and rebuild the search index.

**Returns:** Refresh status and statistics (including templates).

### Template Tools (4)

#### 12. `search_templates`
Search Bootstrap example templates by name, description, or components.

**Parameters:**
- `query` (string): Search query (e.g., "dashboard", "blog layout", "admin panel")
- `category` (string, optional): Filter by category ("admin", "content", "forms", "navigation", "layouts", "components", "reference", "other")
- `limit` (int, optional): Maximum results (default: 10)

**Returns:** List of matching templates with metadata, components used, complexity, and URLs.

**Example:**
```json
{
  "query": "dashboard",
  "results": [
    {
      "name": "dashboard",
      "title": "Dashboard Template · Bootstrap v5.3",
      "category": "admin",
      "description": "Admin dashboard with sidebar, charts, and data tables",
      "complexity": "complex",
      "components": ["navbar", "offcanvas", "table", "card", "dropdown"],
      "has_rtl_variant": true,
      "url": "https://getbootstrap.com/docs/5.3/examples/dashboard/"
    }
  ]
}
```

#### 13. `get_template`
Get complete template code and metadata.

**Parameters:**
- `name` (string): Template name (e.g., "dashboard", "blog", "checkout")

**Returns:** Full HTML code, custom CSS, custom JavaScript, components used, utility classes, and RTL variant information.

**Available templates (41 total):**
- **Admin (2):** dashboard, dashboard-rtl
- **Content (6):** blog, blog-rtl, album, album-rtl, cover, product, pricing
- **Forms (3):** sign-in, checkout, checkout-rtl
- **Navigation (5):** navbars, navbars-offcanvas, sidebars, breadcrumbs, offcanvas-navbar
- **Layouts (10):** grid, heroes, headers, footers, sticky-footer, sticky-footer-navbar, starter-template, features, masonry, jumbotron
- **Components (9):** buttons, badges, dropdowns, modals, carousel, carousel-rtl, offcanvas, list-groups, jumbotron
- **Reference (2):** cheatsheet, cheatsheet-rtl
- **Other (4):** navbar-bottom, navbar-fixed, navbar-static, jumbotrons

#### 14. `list_template_categories`
List all template categories with template names and counts.

**Returns:** Dictionary of categories with template counts and template names.

**Example:**
```json
{
  "categories": {
    "admin": {
      "count": 2,
      "templates": ["dashboard", "dashboard-rtl"]
    },
    "content": {
      "count": 6,
      "templates": ["blog", "blog-rtl", "album", "album-rtl", "pricing", "product"]
    }
  }
}
```

#### 15. `get_template_preview`
Get a preview of a specific section of a template.

**Parameters:**
- `name` (string): Template name
- `section` (string): Section to extract ("header", "nav", "main", "footer", "full")

**Returns:** Code snippet for the specified section (first 500 lines for "full").

---

## Template Library

### What's Included

The server includes **41 production-ready HTML templates** from Bootstrap's official examples. These templates show complete page patterns that complement the component documentation.

| **Documentation** | **Templates** |
|-------------------|---------------|
| "How to use a button component" | "Complete dashboard with sidebar and tables" |
| Component reference | Full page patterns |
| 5-50 line snippets | 500-1000+ line templates |

### Template Categories

- **Admin (2):** Dashboard layouts with sidebars, charts, and data tables
- **Content (6):** Blog layouts, photo albums, product pages, pricing tables
- **Forms (3):** Sign-in forms, multi-step checkout flows with validation
- **Navigation (5):** Various navbar patterns, offcanvas menus, sidebars
- **Layouts (10):** Grid systems, hero sections, headers, footers, sticky layouts
- **Components (9):** Individual component showcases (buttons, badges, modals, etc.)
- **Reference (2):** Complete cheatsheets of all Bootstrap components
- **Other (4):** Additional navbar variations

### Complexity Levels

- **Simple (20):** Single-purpose templates, quick to implement
- **Intermediate (14):** Multi-section layouts with moderate complexity
- **Complex (7):** Full-featured applications (dashboard, checkout, product pages)

### What You Get

Each template includes:
- ✅ Complete HTML structure
- ✅ Custom CSS (when applicable)
- ✅ Custom JavaScript (when applicable)
- ✅ Component list (navbar, card, forms, etc.)
- ✅ Utility class extraction
- ✅ RTL variant detection
- ✅ Official Bootstrap documentation URL

---

## Architecture

### Components

- **FastMCP**: Server framework with HTTP transport
- **SQLite FTS5**: Full-text search engine with BM25 ranking
- **python-frontmatter**: YAML metadata extraction from MDX files
- **Git**: Repository management for documentation updates

### Data Flow

1. **Initialization:**
   - Clone Bootstrap docs repo
   - Parse MDX files
   - Extract template metadata from 41 HTML files
   - Build SQLite indexes

2. **Search:**
   - Client query
   - FTS5 search with synonym expansion
   - Format results
   - Return to client

3. **Template Retrieval:**
   - Template query
   - Load HTML/CSS/JS from filesystem
   - Extract components and utilities
   - Return complete template

4. **Refresh:**
   - Git pull
   - Re-parse files
   - Rebuild indexes (docs + templates)

### Database Schema

**Documentation Tables:**
```sql
-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE docs_fts USING fts5(
    title, description, content, section, component_name,
    tokenize = 'porter unicode61'
);

-- Metadata table with Bootstrap-specific fields
CREATE TABLE doc_metadata (
    id INTEGER PRIMARY KEY,
    filepath TEXT UNIQUE,
    title TEXT,
    section TEXT,
    component_name TEXT,
    utility_classes TEXT,  -- JSON array
    code_examples TEXT,    -- JSON array
    aliases TEXT,          -- JSON array
    url TEXT
);
```

**Template Tables:**
```sql
-- Template metadata
CREATE TABLE template_metadata (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    title TEXT,
    category TEXT,           -- admin, content, forms, etc.
    description TEXT,
    complexity TEXT,         -- simple, intermediate, complex
    html_path TEXT,
    css_files TEXT,         -- JSON array
    js_files TEXT,          -- JSON array
    components TEXT,        -- JSON array
    utility_classes TEXT,   -- JSON array
    has_rtl_variant BOOLEAN,
    rtl_template_name TEXT,
    url TEXT
);

-- FTS5 virtual table for template search
CREATE VIRTUAL TABLE templates_fts USING fts5(
    name, title, category, description, components,
    tokenize = 'porter unicode61'
);
```

---

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATA_DIR=./data
export MCP_PORT=8001

# Run server
python run_server.py
```

### Project Structure

```
bootstrap-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # FastMCP server with 15 tools
│   ├── indexer.py             # SQLite FTS5 indexing (docs + templates)
│   ├── search.py              # Documentation search functionality
│   ├── examples_parser.py     # HTML template parser
│   ├── examples_search.py     # Template search functionality
│   ├── git_manager.py         # Bootstrap repo management
│   └── parser.py              # MDX parsing for Bootstrap docs
├── bootstrap-5.3.8-examples/  # 41 HTML example templates
├── run_server.py              # Server entry point
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Service orchestration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## Performance

| Metric | Time/Size |
|--------|-----------|
| **First startup** | 1-2 minutes (clone + index docs + templates) |
| **Subsequent startups** | <5 seconds (uses cached data) |
| **Search queries** | <100ms for typical queries |
| **Database size** | ~20-30 MB (docs + templates) |
| **Documents indexed** | ~250-300 Bootstrap documentation pages |
| **Templates indexed** | 41 production-ready HTML templates |
| **Memory usage** | ~50-100 MB |

---

## Troubleshooting

### Server won't start

Check logs for errors:
```bash
docker-compose logs -f
```

**Common issues:**
- Port 8001 already in use: Change `MCP_PORT` in `.env`
- Git clone failed: Check network connectivity
- Permission issues: Ensure volume is writable

### Search returns no results

1. Verify index was built:
   ```bash
   docker-compose exec bootstrap-mcp ls -la /app/data
   ```

2. Check if templates were indexed:
   ```bash
   docker-compose exec bootstrap-mcp python -c "import sqlite3; conn = sqlite3.connect('/app/data/bootstrap_docs.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM template_metadata'); print(f'Templates: {cursor.fetchone()[0]}')"
   ```

3. Rebuild index using the `refresh_docs` tool from Claude Code

### Connection refused from Claude Code

1. Verify server is running: `docker-compose ps`
2. Check your hostname is in `MCP_ALLOWED_HOSTS`
3. Verify firewall rules allow port 8001

### Templates not showing up

1. Check if `bootstrap-5.3.8-examples/` folder exists:
   ```bash
   docker-compose exec bootstrap-mcp ls -la /app/bootstrap-5.3.8-examples/ | head -10
   ```

2. If missing, rebuild container:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### Update to latest Bootstrap documentation

```bash
# Option 1: Use the refresh_docs tool from Claude Code
# (This will update both docs and templates)

# Option 2: Delete the volume and restart
docker-compose down -v
docker-compose up -d
```

---

## Security Considerations

### Intended Deployment Model

This MCP server is designed for **local and trusted network environments**:

- ✅ Local Docker containers on your development machine
- ✅ Internal network servers without internet exposure
- ✅ Personal or team development environments
- ✅ Trusted internal infrastructure

**This server is NOT designed to be exposed directly to the internet** without additional security hardening.

### Current Security Posture

The default configuration prioritizes ease of use for local development:

- **No Authentication**: All MCP tools are accessible without authentication
- **No Rate Limiting**: No built-in protection against resource exhaustion
- **HTTP Only**: No TLS/HTTPS encryption by default
- **Host Network Mode**: Container runs in host network mode for MCP compatibility
- **Read-Only Operations**: Server only reads documentation and templates (no user data storage)

### Hardening for Production/Internet Exposure

If you plan to expose this MCP server beyond a trusted local network, consider implementing these security measures:

#### 1. Add Authentication

Implement an authentication layer:
- API key authentication via reverse proxy (nginx, Traefik)
- OAuth2/OIDC integration for user authentication
- Firewall rules limiting access to specific IP addresses

#### 2. Enable TLS/HTTPS

Add a reverse proxy with TLS termination:
```yaml
# Example: nginx with Let's Encrypt
# Place nginx in front of the MCP server
# Configure TLS certificates
# Proxy requests to http://localhost:8001
```

#### 3. Implement Rate Limiting

Protect against resource exhaustion:
- Configure rate limiting in your reverse proxy
- Suggested: 100 requests/minute per IP address
- Monitor for unusual query patterns

#### 4. Network Isolation

Improve container network security:
```yaml
# docker-compose.yml
services:
  bootstrap-mcp:
    # Change from host to bridge mode
    # network_mode: host  # Remove this
    ports:
      - "127.0.0.1:8001:8001"  # Bind to localhost only
    networks:
      - internal  # Use isolated network

networks:
  internal:
    driver: bridge
```

#### 5. Input Validation

Add additional validation layers:
- Limit query string lengths (e.g., max 500 characters)
- Validate template names against whitelist
- Sanitize all user inputs before logging

#### 6. Monitoring and Logging

Implement security monitoring:
- Monitor access logs for unusual patterns
- Set up alerts for high request volumes
- Regularly audit who is accessing the server
- Store logs in a secure, access-controlled location

#### 7. Restrict Dangerous Operations

For internet-exposed deployments:
- Disable or restrict the `refresh_docs` tool (triggers git clone operations)
- Consider making it admin-only via proxy authentication

#### 8. Regular Updates

Maintain security over time:
- Run `pip audit` regularly to check for vulnerable dependencies
- Subscribe to security advisories for FastMCP and dependencies
- Rebuild Docker images monthly to get latest security patches
- Monitor the [FastMCP security advisories](https://github.com/jlowin/fastmcp/security)

### Security Best Practices

Even for local deployments:

1. **Principle of Least Privilege**: Run container as non-root user (already configured)
2. **Network Segmentation**: Keep the Docker host on a separate network segment if possible
3. **Regular Backups**: Although this is a read-only service, backup your database volume
4. **Audit Trail**: Review logs periodically for unusual activity
5. **Update Dependencies**: Keep FastMCP and Python dependencies up to date

### Reporting Security Issues

If you discover a security vulnerability in this project, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email security concerns to the repository maintainer
3. Include details: vulnerability description, reproduction steps, potential impact
4. Allow reasonable time for a fix before public disclosure

### Compliance and Regulatory Considerations

If you're subject to compliance requirements (HIPAA, SOC 2, PCI-DSS, etc.):

- This server stores no user data or PII
- All data comes from public Bootstrap documentation
- Implement additional controls based on your compliance framework
- Conduct a security assessment before production use
- Document your deployment architecture and security controls

---

## Contributing

Contributions are welcome! Please feel free to:

- 🐛 Report bugs or issues
- 💡 Suggest new features or improvements
- 📝 Improve documentation
- 🔧 Submit pull requests
- 🎨 Add new template features

### Development Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly (docs + templates)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

The Bootstrap documentation and examples accessed by this server are © Bootstrap Core Team. This project is not affiliated with or endorsed by Bootstrap or the Bootstrap Core Team.

---

## Credits

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Documentation from [Bootstrap](https://getbootstrap.com)
- 41 example templates from [Bootstrap Examples](https://getbootstrap.com/docs/5.3/examples/)
- Powered by [Model Context Protocol](https://modelcontextprotocol.io)

---

<div align="center">

**Made with ❤️ for the Bootstrap community**

[Report Bug](https://github.com/dougjaworski/bootstrap-mcp/issues) · [Request Feature](https://github.com/dougjaworski/bootstrap-mcp/issues) · [Documentation](https://github.com/dougjaworski/bootstrap-mcp#readme)

</div>
