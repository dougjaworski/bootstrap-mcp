# Bootstrap MCP Server

A Model Context Protocol (MCP) server for searching and exploring Bootstrap CSS documentation. Built with FastMCP, this server provides AI assistants with instant access to Bootstrap's component library, utility classes, and code examples.

## Features

- **Full-Text Search**: BM25-ranked search across all Bootstrap documentation
- **Component Lookup**: Find specific components (accordion, modal, navbar, etc.)
- **Utility Class Search**: Search for utility classes (mt-3, d-flex, text-primary, etc.)
- **Code Examples**: Extract and search HTML/CSS code examples
- **Section Navigation**: Browse documentation by section (Components, Layout, Utilities, Forms, etc.)
- **Auto-Sync**: Refresh documentation directly from the Bootstrap GitHub repository
- **SQLite FTS5**: Fast full-text search with efficient indexing
- **Docker Ready**: Easy deployment with Docker Compose

## Architecture

This server mirrors the architecture of `tailwind-mcp` but is adapted for Bootstrap's component-based framework and documentation structure.

### Key Differences from Tailwind MCP

| Setting | Tailwind MCP | Bootstrap MCP | Reason |
|---------|-------------|---------------|--------|
| **Port** | 8000 | **8001** | Avoid port conflicts |
| **Repository** | tailwindlabs/tailwindcss.com | **twbs/bootstrap** | Bootstrap source |
| **Docs Path** | `src/docs` | **`site/content/docs`** | Different structure |
| **Volume Name** | tailwind-docs | **bootstrap-docs** | Separate persistence |
| **Database Name** | tailwind_docs.db | **bootstrap_docs.db** | Separate data |

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Quick Start

1. Clone this repository:

```bash
git clone <repository-url>
cd bootstrap-mcp
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. Build and start the server:

```bash
docker-compose up -d
```

4. The server will be available at `http://localhost:8001/mcp`

On first startup, the server will:
- Clone the Bootstrap repository
- Parse all MDX documentation files
- Build a searchable FTS5 index
- Start the HTTP server

This process takes 1-2 minutes on first run, then <5 seconds on subsequent startups.

## Configuration

### Environment Variables

Configure the server using `.env`:

```bash
# Server Configuration
MCP_PORT=8001                    # Server port (8001 to avoid conflict with tailwind-mcp)
MCP_HOST=0.0.0.0                # Bind address
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,0.0.0.0:*

# Data Directory
DATA_DIR=/app/data              # Where to store repo and database

# Logging Level
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

### MCP Client Configuration

To use with Claude Code or other MCP clients, create or update your `.mcp.json`:

```json
{
  "mcpServers": {
    "bootstrap-docs": {
      "url": "http://localhost:8001/mcp",
      "description": "Bootstrap CSS documentation and component search"
    }
  }
}
```

For remote servers, replace `localhost` with your hostname:

```json
{
  "mcpServers": {
    "bootstrap-docs": {
      "url": "http://docker01:8001/mcp",
      "description": "Bootstrap CSS documentation and component search"
    }
  }
}
```

## MCP Tools

The server provides 8 MCP tools for interacting with Bootstrap documentation:

### 1. search_docs

Search documentation using full-text search with BM25 ranking.

```python
search_docs(
    query="responsive grid",
    limit=10
)
```

**Returns**: Ranked search results with title, description, section, and URL.

### 2. get_component

Find documentation for a specific Bootstrap component.

```python
get_component(component_name="modal")
```

**Supported components**:
- accordion, alert, badge, breadcrumb, button, button-group
- card, carousel, close-button, collapse, dropdown
- list-group, modal, nav, navbar, offcanvas
- pagination, placeholder, popovers, progress
- scrollspy, spinners, toasts, tooltips

**Returns**: Complete component documentation including utility classes and code examples.

### 3. get_utility_class

Find documentation for a specific utility class.

```python
get_utility_class(class_name="mt-3")
```

**Supported utility patterns**:
- **Spacing**: `m-*`, `mt-*`, `mb-*`, `ml-*`, `mr-*`, `mx-*`, `my-*`, `p-*`, `pt-*`, `pb-*`, `pl-*`, `pr-*`, `px-*`, `py-*`
- **Display**: `d-none`, `d-block`, `d-flex`, `d-grid`, `d-inline`, etc.
- **Responsive**: `d-{sm|md|lg|xl|xxl}-*`
- **Flexbox**: `flex-row`, `flex-column`, `justify-content-*`, `align-items-*`
- **Grid**: `col-*`, `col-{sm|md|lg|xl|xxl}-*`
- **Colors**: `text-*`, `bg-*`
- **Borders**: `border-*`, `rounded-*`
- **Sizing**: `w-*`, `h-*`

**Returns**: List of documents that use the utility class.

### 4. list_sections

List all documentation sections.

```python
list_sections()
```

**Returns**: All sections with document counts (Components, Layout, Utilities, Forms, Content, Customize, etc.).

### 5. get_section_docs

Get all documentation pages in a specific section.

```python
get_section_docs(section="components")
```

**Returns**: All documents in the section.

### 6. get_full_doc

Get complete documentation by slug.

```python
get_full_doc(slug="accordion")
```

**Returns**: Full document content with all metadata, utility classes, and code examples.

### 7. get_examples

Search for code examples.

```python
get_examples(
    query="button",
    limit=5
)
```

**Returns**: HTML/CSS code examples extracted from `<Example>` JSX components.

### 8. refresh_docs

Update documentation from GitHub and rebuild index.

```python
refresh_docs()
```

**Returns**: Refresh status and statistics.

## Documentation Structure

Bootstrap documentation is organized in the following sections:

```
site/content/docs/
├── components/     # UI components (accordion, modal, navbar, etc.)
├── layout/         # Grid system, containers, columns
├── utilities/      # Utility classes (spacing, display, flex, etc.)
├── forms/          # Form controls and validation
├── content/        # Typography, images, tables
├── customize/      # Customization and theming
├── getting-started/# Installation and setup
└── ...
```

## Bootstrap-Specific Features

### Component Detection

Components are automatically extracted from file paths:

```
components/accordion.mdx → component_name: "accordion"
components/modal.mdx     → component_name: "modal"
```

### Utility Class Extraction

The parser uses regex patterns to extract Bootstrap utility classes from code examples:

```html
<div class="d-flex justify-content-between mt-3">
  <!-- Extracts: d-flex, justify-content-between, mt-3 -->
</div>
```

### Code Example Extraction

Code examples are extracted from JSX `<Example>` components:

```jsx
<Example>
  <button class="btn btn-primary">Primary</button>
  <button class="btn btn-secondary">Secondary</button>
</Example>
```

### URL Generation

Documentation URLs are automatically generated:

```
components/accordion.mdx → https://getbootstrap.com/docs/5.3/components/accordion/
utilities/spacing.mdx    → https://getbootstrap.com/docs/5.3/utilities/spacing/
```

## Database Schema

### doc_metadata Table

```sql
CREATE TABLE doc_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    section TEXT,
    component_name TEXT,      -- Bootstrap component name
    utility_classes TEXT,     -- JSON array of utility classes
    code_examples TEXT,       -- JSON array of code examples
    aliases TEXT,             -- JSON array of URL aliases
    toc BOOLEAN,              -- Table of contents flag
    url TEXT,                 -- Bootstrap docs URL
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### docs_fts Virtual Table (FTS5)

```sql
CREATE VIRTUAL TABLE docs_fts USING fts5(
    title,
    description,
    content,
    section,
    component_name,
    tokenize = 'porter unicode61'
);
```

## Development

### Local Development

1. Install Python 3.11+

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables:

```bash
export DATA_DIR=./data
export MCP_PORT=8001
export LOG_LEVEL=DEBUG
```

5. Run the server:

```bash
python run_server.py
fastmcp run run_server.py:mcp --transport http --host 0.0.0.0 --port 8001
```

### Project Structure

```
bootstrap-mcp/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── server.py             # FastMCP server with 8 tools
│   ├── indexer.py            # SQLite FTS5 indexing
│   ├── search.py             # Search functionality
│   ├── git_manager.py        # Bootstrap repo management
│   └── parser.py             # MDX parsing for Bootstrap docs
├── run_server.py             # Server entry point
├── Dockerfile                # Container configuration
├── docker-compose.yml        # Service orchestration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker ignore rules
├── .mcp.json                # MCP client configuration
├── LICENSE                  # MIT License
└── README.md                # This file
```

## Performance

- **First startup**: 1-2 minutes (clone + index ~250-300 docs)
- **Subsequent startups**: <5 seconds (cached data)
- **Search queries**: <100ms
- **Database size**: ~8-12 MB
- **Memory usage**: ~50-100 MB

## Troubleshooting

### Server won't start

Check Docker logs:

```bash
docker-compose logs -f bootstrap-mcp
```

### Port conflict

If port 8001 is already in use, update `.env`:

```bash
MCP_PORT=8002
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

### Database issues

Clear the database and rebuild:

```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Rebuild index
```

### Repository update issues

If the Bootstrap repository fails to update, try refreshing:

```python
# Use the refresh_docs tool
refresh_docs()
```

Or manually:

```bash
docker-compose exec bootstrap-mcp rm -rf /app/data/bootstrap-repo
docker-compose restart bootstrap-mcp
```

## Compatibility

- **Python**: 3.11+
- **Bootstrap**: 5.3 (main branch)
- **FastMCP**: 0.2.0+
- **SQLite**: 3.x with FTS5 support

## Runs Alongside Tailwind MCP

This server is designed to run alongside `tailwind-mcp`:

- **Tailwind MCP**: `http://localhost:8000/mcp`
- **Bootstrap MCP**: `http://localhost:8001/mcp`

Both can be configured in your `.mcp.json`:

```json
{
  "mcpServers": {
    "tailwind-docs": {
      "url": "http://docker01:8000/mcp",
      "description": "Tailwind CSS documentation"
    },
    "bootstrap-docs": {
      "url": "http://docker01:8001/mcp",
      "description": "Bootstrap CSS documentation"
    }
  }
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- Architecture inspired by [tailwind-mcp](https://github.com/example/tailwind-mcp)
- Documentation from [Bootstrap](https://github.com/twbs/bootstrap)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review Docker logs for error messages
