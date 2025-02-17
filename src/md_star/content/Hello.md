---
title: MD Star
keywords:
  - MD Star
  - Markdown to HTML
created: 2025-02-03 23:32:42
updated: 2025-02-17 07:54
---

## MD Star

[![PyPI - Version](https://img.shields.io/pypi/v/md-star.svg)](https://pypi.org/project/md-star)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/md-star.svg)](https://pypi.org/project/md-star)

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Features

Markdown to HTML

- To HTMl
  - Lang
  - Schema website name
  - Schema Article
  - X card
  - rel="canonical" link
  - Sitemap
- Other
  - Drafts
  - Serve

## Installation

```console
pip install md-star
```

## Usage

```console
mdstar init my-blog
cd my-blog
mdstar build
mdstar serve [-p 8000]
```

### Deploy Cloudflare Pages

Build configuration:

- Build command: pip install md-star && mdstar build
- Build output: dist

## License

`md-star` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
