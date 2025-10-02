# Changelog

## [Unreleased]

## [0.2.0] - 2025-10-02

### Major Refactoring & Architecture Improvements

* **Code Organization & Architecture**
  * Extracted `LarkDocument` functionality into its own dedicated module
  (`document.py`)
  * Separated concerns between server handling and document processing
  * Introduced proper symbol table architecture with `SymbolTable`, `Symbol`,
  and related classes
  * Simplified feature registration in the language server

### Enhanced Symbol Management

* **Symbol Table System**
  * Complete rewrite of symbol collection and management
  * Added comprehensive `SymbolTable` class with proper symbol tracking
  * Implemented `Symbol` class with full metadata (position, range, modifiers,
  documentation)
  * Added support for symbol modifiers (inline, conditionally inline, pinned)
  * Proper handling of symbol aliases and directives

* **Symbol Provider Improvements**
  * Correct symbol provider handling for rule definitions
  * Enhanced terminal symbol definitions
  * Improved import statement processing
  * Fixed reference collection and validation
  * Better symbol-at-position detection with word boundary support

### Language Server Features

* **Diagnostics & Error Handling**
  * Added parsing errors to diagnostic list
  * Improved error reporting with proper line/column information
  * Enhanced diagnostic boundary checking

* **Code Completion**
  * Refactored completion system to use symbol table
  * More accurate completion suggestions based on available symbols
  * Better context-aware completions

* **Hover Information**
  * Simplified hover info implementation using new `Symbol.documentation`
  property
  * Rich markdown documentation for symbols
  * Better symbol information display

* **Navigation Features**
  * Improved "Go to Definition" using symbol table
  * Enhanced reference finding with proper validation
  * Better symbol location accuracy

### Testing & Quality Improvements

* **Test Suite Reorganization**
  * Complete restructuring of test files following clear naming conventions:
    * `test_document.py` - Tests for `LarkDocument` class (50 tests)
    * `test_server.py` - Tests for `LarkLanguageServer` class (35 tests)
    * `test_symbol_table.py` - Tests for symbol table classes (35 tests)
    * `test_main.py` - Tests for main module functions (14 tests)
    * `test_integration.py` - Integration tests (9 tests)
  * Consolidated and removed redundant test files
  * Added comprehensive edge case testing

### Development & Documentation

* **Development Environment**
  * Added `debugpy` for debugging support
  * Added `jupyter-lsp` and `jupyterlab-lsp` for live testing in Jupyter environments
  * Updated Python version classifiers in PyPI metadata
  * Fixed markdownlint configuration for consistency with editorconfig

* **Documentation & Project Health**
  * Added code coverage badge to README
  * Fixed documentation links
  * Updated project metadata and classifiers
  * Improved code organization and maintainability

### Internal Improvements

* **API Enhancements**
  * Updated `LarkDocument.get_symbol_at_position` signature for better usability
  * Made imports explicit in server module
  * Removed unused properties and cleaned up code
  * Better error handling and edge case management

* **Code Quality**
  * Simplified and streamlined codebase
  * Better separation of concerns
  * Improved code readability and maintainability
  * Enhanced type safety and documentation

## [0.1.0] - 2025-09-30

* Base boilerplage features
  * Diagnostics
  * Code completion
  * Hover information
  * Go to definition
  * Find references
  * Document symbols
  * Semantic analysis
  * Formatting
