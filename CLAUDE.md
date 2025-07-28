# Claude Code Guidelines

## Python Code Style Requirements

### PEP 8 Compliance
- All Python code must be PEP 8 compliant
- **Line length: Maximum 79 characters** (strict enforcement)
- Use 4 spaces for indentation (no tabs)
- Follow naming conventions:
  - Functions and variables: `snake_case`
  - Classes: `PascalCase`  
  - Constants: `UPPER_CASE`

### Code Quality Standards
- Remove trailing whitespace from all lines
- End files with a single newline
- Use meaningful variable names
- Add type hints where appropriate
- Follow existing import organization patterns

### Line Length Management
When lines exceed 79 characters, use these strategies:
1. **Function calls**: Break at commas, align arguments
```python
# Good
result = some_function(
    argument_one,
    argument_two,
    argument_three
)
```

2. **Long strings**: Use parentheses for implicit concatenation
```python
# Good
message = (
    "This is a very long message that needs to be "
    "split across multiple lines"
)
```

3. **Import statements**: Use parentheses for multiple imports
```python
# Good
from src.bold.id_engine import (
    BoldSearch,
    BOLDIGGER_NO_MATCH_STR,
    BOLDIGGER_OUTPUT_DIRNAME,
)
```

4. **Method chaining**: Break at dots
```python
# Good
result = (
    some_object
    .method_one()
    .method_two()
    .method_three()
)
```

### Testing Standards
- Test files must also follow PEP 8 guidelines
- Test method names should be descriptive
- Use setUp/tearDown methods appropriately
- Mock external dependencies in tests

### Tools
- Use `flake8` or `black` for automatic formatting
- Configure your editor to show line length indicators at 79 characters
- Run linting before committing code

### Example of Well-Formatted Code

```python
def parse_bold_xlsx(
    self,
    path: Path,
    results: dict = None,
) -> dict[str, list]:
    """Parse BOLDigger3 XLSX output with proper formatting."""
    if results is None:
        results = {}
    
    df = pd.read_excel(path)
    
    for _, row in df.iterrows():
        query_id = row['id']
        
        # Handle long conditional statements
        if (
            row.get('phylum') == BOLDIGGER_NO_MATCH_STR
            or pd.isna(row.get('processid'))
        ):
            continue
            
        # Handle long dictionary definitions
        hit = {
            "hit_id": process_id,
            "taxonomic_identification": taxonomic_identification,
            "identity": row.get('pct_identity'),
            "url": BOLD_RECORD_BASE_URL + process_id,
        }
        
    return results
```

### Example of poor line-wrapping

```python
# This is ugly
def parse_bold_xlsx(self, path: Path,
                    results: dict = None) -> dict[str, list]:
```


### Whitespace

Make sure that no trailing whitespace remains, including lines which contain nothing but whitespace.

### Use of constants

Where appropriate, declare string, int and float values as constants at the top of the script, below imports. This should only be done where it improves the readability of code. Paths, URLs and "magic numbers" should always be declared in this way, but not dictionary keys.

## Enforcement
Claude will automatically ensure all code follows these guidelines before writing or modifying any Python files.
