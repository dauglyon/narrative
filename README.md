# The KBase Narrative Interface

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/kbase/narrative?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

| Branch | Status |
| :--- | :--- |
| master | [![Build Status](https://travis-ci.org/kbase/narrative.svg?branch=master)](https://travis-ci.org/kbase/narrative) [![Coverage Status](https://coveralls.io/repos/kbase/narrative/badge.svg?branch=master)](https://coveralls.io/r/kbase/narrative?branch=master) |
| develop | [![Build Status](https://travis-ci.org/kbase/narrative.svg?branch=develop)](https://travis-ci.org/kbase/narrative) [![Coverage Status](https://coveralls.io/repos/kbase/narrative/badge.svg?branch=develop)](https://coveralls.io/r/kbase/narrative?branch=develop)|

***Table of Contents***

- [About](#about)
- [Installation](#installation)
  - [Local Installation](#local-installation)
    - [Using a Conda Environment](#using-a-conda-environment)
    - [Without Conda](#without-conda)
- [Architecture](#architecture)
- [Testing](#testing)
  - [Manual Testing](#manual-testing)
- [Submitting Code](#submitting-code)

## About

This is the repository for the KBase Narrative Interface. The KBase Narrative Interface builds on the [Jupyter Notebook](http://jupyter.org) and contains elements to interact with various KBase tools and data stores.

This document contains links to various documentation in the [docs](docs) directory, with a brief description of each.

## Installation

If you want to use the KBase Narrative Interface, just point your browser at https://narrative.kbase.us, make a free account, and jump in. This repo is only for people who wish to contribute to the development of the interface.

### Local Installation

Short version:
Requires the following:

-   Python 3.6+
-   Anaconda/Miniconda as an environment manager (<https://www.anaconda.com/>)
-   Node.js (latest LTS recommended)
-   Bower 1.8.8+

### Git Pre-commit installation

Our git [pre-commit](https://pre-commit.com/#install) [hooks](/.pre-commit-config.yaml) allow you to run flake8 and black upon `git commit` and save you from having to run these linters manually.

- change into the base directory
- `pip install pre-commit`
- `pre-commit install` to set up the git hook scripts
- edit a python file and `git commit -m <comment>` it in to test out the installation


### *Using a Conda Environment*

This is the recommended method of installation!

```
git clone https://github.com/kbase/narrative
cd narrative
conda create -n my_narrative_environment
conda activate my_narrative_environment
./scripts/install_narrative.sh
kbase-narrative
```

If the previous instructions do not work, try

```
# source ~/anaconda3/bin/activate or wherever you have python installed
conda create -n my_narrative_environment
conda activate my_narrative_environment
sh scripts/install_narrative.sh
# scripts/install_narrative.sh
kbase-narrative
```

### *Without conda*

This process installs lots of requirements of specific versions and may clobber things on your PYTHONPATH.

```
git clone https://github.com/kbase/narrative
cd narrative
./scripts/install_narrative.sh
kbase-narrative
```

Long version: [Local Narrative setup](docs/install/local_install.md)

## Architecture

***In progress!***

The Narrative sits on top of the Jupyter Notebook, so most of its architecture is a mirror of that. However, the Narrative's interaction with other KBase elements - namely the data stores and job running services - merits its own description. This will be ongoing (and evolving!), but a brief description of how a job gets run and registered is available here:

[Narrative App/Method Running](docs/developer/narrative_app_error_states.md)

When deployed in production, the Narrative Interface is compiled into a [Docker](https://www.docker.com) container. When a user logs in, they have their own instance provisioned for them through an [Nginx](http://nginx.org) proxy, which provides a temporary server-side Narrative environment only for that user. Any changes made to a Narrative get saved as part of KBase data stores, but any changes to the file system or the Narrative kernel (e.g. local variables) are lost when the user logs out and their Docker instance gets shut down.

## Testing

For general testing instructions and guidance refer to [docs/testing.md](docs/testing.md). For information about headless browser testing refer to [docs/HeadlessTesting.md](docs/HeadlessTesting.md).

## Submitting code

Follow the gitflow directions located at [docs/git-workflow.md](docs/git-workflow.md) to submit code to this repository.
