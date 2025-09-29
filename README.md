[![Community-Project][dynova-banner-community]][dynova-homepage]

[![PyPI - Supported versions][badge-pypi-python-versions]][repository]
[![PyPI - Package version][badge-pypi-version]][repository]
[![PyPI - Downloads][badge-pypi-downloads]][repository]
[![PyPI - License][badge-pypi-license]][repository]

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/32cf38efba474a4ab376b35ddfcf5e61)](https://app.codacy.com/gh/dynovaio/lark-parser-language-server/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![pipeline status](https://gitlab.com/softbutterfly/open-source/lark-parser-language-server/badges/master/pipeline.svg)](https://gitlab.com/softbutterfly/open-source/lark-parser-language-server/-/commits/master)

# Lark Parser Language Server

Lark Parser Language Server is a Language Server Protocol (LSP) implementation
for the Lark parsing library. It provides features such as syntax highlighting,
code completion, and error checking for Lark grammar files in compatible code
editors.

## ✨ Features

The language server provides the following LSP features:

* **Diagnostics**: Syntax error detection and undefined symbol validation
* **Code Completion**: Intelligent suggestions for rules, terminals, and
keywords
* **Hover Information**: Documentation and type information on hover
* **Go to Definition**: Navigate to rule and terminal definitions
* **Find References**: Locate all usages of symbols
* **Document Symbols**: Outline view with rules and terminals
* **Semantic Analysis**: Advanced grammar validation
* **Formatting**: Automatic code formatting for Lark grammar files

## Requirements

* Python 3.9.0 or higher

## Install

Install from PyPI

```bash
pip install lark-parser-language-server
```

## Usage

Run the language server

```bash
# Run the server
python -m lark_language_server

# Run with TCP (for debugging)
python -m lark_language_server --tcp --host 127.0.0.1 --port 2087
```

## Docs

Documentation is available at our [docs site ↗][docs].

## Release Notes

All changes to versions of this library are listed in our
[change log ↗][changelog].

## Contributing

Contributions are greatly appreciated.

Please fork this repository and open a pull request to make grammar tweaks, add
support for other subgrammars etc.

## Contributors

See the list of contributors in our [contributors page ↗][contributors].

## License

This project is licensed under the terms of the Apache-2.0 license. See the
[LICENSE ↗][license] file.

[dynova-homepage]: https://dynova.io
[dynova-banner-community]: https://gitlab.com/softbutterfly/open-source/open-source-office/-/raw/master/assets/dynova/dynova-open-source--banner--community-project.png
[badge-pypi-python-versions]: https://img.shields.io/pypi/pyversions/lark-parser-language-server
[badge-pypi-version]: https://img.shields.io/pypi/v/lark-parser-language-server
[badge-pypi-downloads]: https://img.shields.io/pypi/dm/lark-parser-language-server
[badge-pypi-license]: https://img.shields.io/pypi/l/lark-parser-language-server

[repository]: https://github.com/dynovaio/lark-parser-vscode
[docs]: https://dynovaio.github.io/lark-parser-language-server
[changelog]: https://github.com/dynovaio/lark-parser-language-server/blob/develop/CHANGELOG.md
[contributors]: https://github.com/dynovaio/lark-parser-language-server/graphs/contributors
[license]: https://github.com/dynovaio/lark-parser-language-server/blob/develop/LICENSE.txt
