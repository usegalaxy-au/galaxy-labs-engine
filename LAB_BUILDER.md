# Galaxy Lab Builder

## Overview

The Galaxy Lab Builder is a visual web interface for creating and editing Galaxy Lab YAML configurations. It provides an intuitive way to build Lab content without manually writing YAML files.

## Features

### Core Functionality
- **Visual Lab Configuration**: Create lab settings including site name, Galaxy URLs, and metadata
- **Section Management**: Add, edit, and remove lab sections with tabs and content items
- **YAML Validation**: Real-time validation against the LabSectionSchema
- **YAML Export**: Generate properly formatted YAML files for download

### Advanced Features
- **GitHub Import**: Import existing Lab content from GitHub repositories
- **PR Instructions**: Generate step-by-step instructions for creating pull requests
- **Example Loading**: Pre-populate with example Lab content
- **Nested Content Structure**: Support for sections → tabs → content items → buttons

## Usage

### Accessing the Builder
Navigate to `/builder` on your Galaxy Labs Engine instance.

### Basic Workflow
1. **Configure Lab Settings**: Fill in basic information like site name, lab name, Galaxy URL, etc.
2. **Add Sections**: Create sections that will become the main navigation elements
3. **Add Tabs**: Within each section, add tabs for different categories of content
4. **Add Content Items**: Within each tab, add individual tools, workflows, or help items
5. **Add Buttons**: For each content item, add action buttons (run, view, help, etc.)
6. **Validate**: Use the validation feature to check your configuration
7. **Export**: Download the generated YAML files

### GitHub Integration
- **Import**: Paste a GitHub URL to import existing Lab content
  - Supports URLs to folders containing `base.yml` or direct links to `base.yml`
  - Automatically fetches and loads all section files
- **PR Creation**: Generate instructions and downloadable files for creating pull requests

## Technical Details

### Schema Compliance
The builder enforces the `LabSectionSchema` and `LabSchema` defined in `app/labs/lab_schema.py`:
- Validates required fields
- Enforces proper data types
- Checks markdown/HTML content
- Validates icon enums and button structures

### API Endpoints
- `POST /builder/api` with `action: 'validate_section'` - Validate a single section
- `POST /builder/api` with `action: 'validate_lab'` - Validate complete lab configuration
- `POST /builder/api` with `action: 'export_yaml'` - Export YAML files
- `POST /builder/api` with `action: 'import_github'` - Import from GitHub
- `POST /builder/api` with `action: 'create_pr'` - Generate PR instructions

### Generated Files
The builder generates standard Galaxy Lab files:
- `base.yml` - Main lab configuration
- `section_1.yml`, `section_2.yml`, etc. - Individual section configurations

## Supported Content Types

### Icons
- `run` - For executable tools/workflows
- `view` - For viewing/browsing content
- `tutorial` - For educational content
- `help` - For help/documentation
- `social` - For community content

### Button Properties
- `link` - URL for the button action (required)
- `label_md` - Markdown text for button label
- `icon` - Icon type (see above)
- `tip` - Tooltip text

### Content Structure
```
Lab
├── Site Configuration (name, URLs, branding)
└── Sections (navigation elements)
    └── Tabs (content categories)
        └── Content Items (individual tools/workflows)
            └── Buttons (action buttons)
```

## Development Notes

### Code Quality
- Follows PEP 8 standards with 79-character line limit
- Uses Django best practices
- Includes comprehensive error handling
- Implements proper validation and sanitization

### Security Considerations
- CSRF exempt for API endpoints (uses JSON POST)
- Input validation through Pydantic schemas
- No direct file system access from user input
- Safe YAML parsing with `yaml.safe_load()`

## Future Enhancements

Potential improvements for the Lab Builder:
- Full GitHub API integration for automated PR creation
- Real-time preview of generated Lab pages
- Drag-and-drop interface for reordering elements
- Import from other YAML sources
- Collaborative editing features
- Template system for common Lab patterns