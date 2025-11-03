# Changelog

## [Unreleased]

## [0.4.0] - 2025-11-03

### Enhanced LSP Features

* **Improved Hover Documentation**
  * Added rich markdown documentation for grammar rules and terminals
  * Enhanced symbol details with import paths, modifiers, and declaration status
  * Added syntax-highlighted grammar rule definitions in hover tooltips
  * Better formatting and organization of hover information
  * Enhanced container and parent-child relationship display

* **Document Formatting**
  * Fixed formatting issues with string ranges and case-insensitive modifiers
  * Enhanced formatting of grammar nodes with better type handling
  * Fixed range formatting edge cases
  * Relaxed type annotations for improved flexibility

### Quality Improvements

* **Test Suite Enhancements**
  * Fixed and optimized syntax tree tests
  * Enhanced symbol table tests with better coverage
  * Improved test organization and readability
  * Added more edge case testing
  * Fixed lint errors across test suite:
    * Integration tests cleanup
    * Parser test improvements
    * Server test refinements
    * Symbol table test enhancements

* **Code Quality**
  * Enhanced type safety with better annotations
  * Improved error handling and edge cases
  * Cleaner code organization

### Bug Fixes

* Fixed formatting issues with LString ranges
* Fixed string case-insensitive modifier handling
* Fixed formatting edge cases in various grammar constructs
* Improved boundary condition handling

## [0.3.0] - 2025-10-24

### Major Architecture & Infrastructure Improvements

* **Complete Symbol Table Reorganization**
  * Refactored monolithic `symbol_table.py` into organized module structure:
    * `symbol_table/__init__.py` - Main symbol table coordination
    * `symbol_table/symbol.py` - Enhanced Symbol class with LSP location support
    * `symbol_table/syntax_tree.py` - Syntax tree processing and symbol extraction
    * `symbol_table/flags.py` - Symbol modifier flags and attributes
    * `symbol_table/errors.py` - Comprehensive error handling classes
    * `symbol_table/validators.py` - Symbol validation and error detection
  * Added validation and error collection mechanisms for robust parsing
  * Enhanced Range class with inclusion tests and better boundary handling
  * Improved symbol aliasing support for imported symbols

* **New Syntax Tree Implementation**
  * Added complete `syntax_tree` module with AST node definitions
  * Implemented `AstBuilder` with regex handling and proper type annotations
  * Added comprehensive node types for all Lark grammar constructs
  * Enhanced typing system for better IDE support and error detection

* **Native Grammar Support**
  * Added `grammars/` module with Lark-compatible grammar definitions:
    * `lark.lark` - Standard Lark grammar
    * `lark4ls.lark` - Language server optimized grammar
  * Implemented custom parser infrastructure using Lark class
  * Added optimized position propagation for better LSP performance

### New Language Server Features

* **Document Formatting**
  * Complete document formatting implementation with LSP compliance
  * Support for formatting options and configuration
  * Enhanced regex handling for proper code structure preservation
  * Full LSP specification adherence for formatting responses

* **Enhanced Document Processing**
  * Improved boundary checking and validation
  * Better template rule symbol detection support
  * Enhanced document synchronization with full sync mode
  * Streamlined document infrastructure integration

* **Server Infrastructure Improvements**
  * Enhanced server initialization with proper document sync configuration
  * Better error handling and diagnostic reporting
  * Improved LSP feature registration and management

### Development & Testing Enhancements

* **Comprehensive Test Suite Expansion**
  * Major test reorganization with extensive new test coverage:
    * `test_formatter.py` - Complete formatter testing (988+ additions)
    * `test_parser.py` - Parser functionality testing (180+ tests)
    * `test_symbol_table_*.py` - Modular symbol table testing (3000+ tests)
    * `test_syntax_tree*.py` - Syntax tree testing (1000+ tests)
  * Enhanced existing test suites with better coverage
  * Added comprehensive edge case and error condition testing
  * Improved test organization and maintainability

* **Development Environment**
  * Added `rich` library for enhanced development experience
  * Updated pre-commit configuration for better code quality
  * Added version flag support in main module
  * Improved development dependency management

### Internal Improvements

* **Code Quality & Organization**
  * Removed unused imports and simplified code structure
  * Enhanced type safety with better annotations
  * Improved error handling and edge case management
  * Better separation of concerns across modules

* **Performance Optimizations**
  * Optimized parser infrastructure for better LSP response times
  * Enhanced position tracking and symbol resolution
  * Improved memory usage with better data structures
  * Streamlined document processing pipeline

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
