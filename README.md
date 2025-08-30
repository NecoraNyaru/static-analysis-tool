# 🛠️ Static Analysis Toolkit for C/C++

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/)

A multi-faceted toolkit to analyze C/C++ projects for declared dependencies, reused open-source components, and vendored libraries.

## 📜 Overview

Managing dependencies and identifying third-party code in C and C++ projects can be challenging due to the lack of a standardized package manager and the common practice of vendoring code. This toolkit provides a command-line interface (`scan.py`) that integrates three distinct scanning methodologies.

* **TPL Scanner:** Parses build system and package manager files (`CMake`, `Make`, `Conan`, etc.) to find explicitly declared third-party library dependencies.

* **OSS Identifier:** Uses function-level source code hashing to detect reused open-source components, even if they have been modified or are not explicitly declared.

* **OSV Scanner:** Two modes:
  - API mode identifies vendored (copy-pasted) libraries by hashing source files and querying the [OSV.dev DetermineVersion API](https://google.github.io/osv.dev/post-v1-determineversion/).
  - CLI mode drives the [osv-scanner](https://github.com/google/osv-scanner) binary to enumerate packages discovered in your source tree.

## ✨ Core Features

* **Unified Interface:** Access all scanners through a single, easy-to-use command-line script.
* **Declared Dependency Analysis:** Scans over 15 different C/C++ build systems and package managers.
* **Deep Source Code Matching:** Identifies OSS components by creating a database of function hashes and finding matches within your code.
* **Vendored Code Detection:** Leverages file hashing and the OSV API to identify entire libraries that have been copied into your repository.
* **OSV CLI Wrapper:** Runs the `osv-scanner` binary and outputs a list of identified packages.
* **Flexible and Configurable:** All paths and key parameters are configurable via command-line arguments, with no hardcoded paths.

## 🚀 Getting Started

### Prerequisites

* Python 3.7+ and Pip
* Git
* **Universal Ctags:** for the OSS scanner. Install it via your system's package manager.
    ```sh
    # On Debian/Ubuntu
    sudo apt-get install universal-ctags
    ```
* **OSV-Scanner:** for the OSV CLI mode. Install from https://github.com/google/osv-scanner or your package manager, and ensure it is on `PATH`, or pass `--scanner-path`.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/NecoraNyaru/static-analysis-tool.git
    cd static-analysis-tool
    ```

2.  **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```

## 📖 Usage

The primary entry point for all operations is `scan.py`.

```sh
python scan.py [tpl | oss | osv] [options...]
```

### 1. TPL Scanner: Identifying Declared Dependencies

This scanner analyzes build files to find explicitly configured dependencies.

**Command:**
```sh
python scan.py tpl -d <path/to/your/project> -o <path/to/output.json>
```

- `-d, --directory`: Project directory to scan.
- `-o, --output`: File path to save JSON results.

**Example:**
```sh
python scan.py tpl -d ./my-awesome-project -o my-project-dependencies.json
```

### 2. OSS Identifier: Detecting Reused Source Code

A three-step process to find code copied from other open-source projects.

#### Step 1: Collect OSS Data

Build a database of function hashes from known open-source projects.

**Command:**
```sh
python scan.py oss collect -i <path/to/urls.txt> -o <path/to/collector_output> --ctags-path <path/to/ctags_binary>
```

- `-i, --input`: Text file with one git clone URL per line.
- `-o, --output-dir`: Directory for cloned repos and function data.
- `--ctags-path`: (Optional) Path to ctags binary.

**Example:**
```sh
python scan.py oss collect -i oss/osscollector/sample -o ./oss_data/collector
```

#### Step 2: Preprocess the Data

Process collected data to create the component database.

**Command:**
```sh
python scan.py oss preprocess -i <path/to/collector_output> -o <path/to/preprocessor_output> --mode [full|lite]
```

- `-i, --input-dir`: Output directory from the collect step.
- `-o, --output-dir`: Directory for generated database files.
- `--mode`: `full` (default, more accurate) or `lite` (faster).

**Example:**
```sh
python scan.py oss preprocess -i ./oss_data/collector -o ./oss_data/preprocessor --mode full
```

#### Step 3: Detect Components in Your Project

Run the detector using the generated database.

**Command:**
```sh
python scan.py oss detect -d <path/to/your/project> \
  -o <path/to/results_dir> \
  --collector-dir <path/to/collector_output> \
  --preprocessor-dir <path/to/preprocessor_output>
```

- `-d, --directory`: Project directory to scan.
- `-o, --output-dir`: Directory for detection results.
- `--collector-dir`: Output directory from the collect step.
- `--preprocessor-dir`: Output directory from the preprocess step.

**Example:**
```sh
python scan.py oss detect -d ./my-awesome-project \
  -o ./scan_results \
  --collector-dir ./oss_data/collector \
  --preprocessor-dir ./oss_data/preprocessor
```

### 3. OSV Scanner

Two ways to use OSV in this toolkit:

#### A) API mode: Finding Vendored Libraries

Uses the OSV DetermineVersion API to find whole libraries copied into vendor-like folders (e.g., `third_party`, `external`).

**Command:**
```sh
python scan.py osv api -d <path/to/your/project> -o <path/to/output.json> [--threshold 0.15] [--scan-git]
```

- `-d, --directory`: Project directory to scan.
- `-o, --output`: File path to save JSON results.
- `--threshold`: (Optional) Confidence score (0.0 to 1.0) to report a match. Default: 0.15.
- `--scan-git`: (Optional) If set, will not skip `.git` directories.

**Example:**
```sh
python scan.py osv api -d ./my-awesome-project -o osv-api-results.json --threshold 0.2
```

#### B) CLI wrapper mode: Enumerating Packages with osv-scanner

Runs the `osv-scanner` binary and saves a JSON with the discovered packages.

**Command:**
```sh
python scan.py osv cli -d <path/to/your/project> -o <path/to/output.json> [--scanner-path /full/path/to/osv-scanner]
```

- `-d, --directory`: Project directory to scan.
- `-o, --output`: File path to save the processed JSON results.
- `--scanner-path`: (Optional) Explicit path to the `osv-scanner` executable. If omitted, it must be discoverable via `PATH`.

**Examples:**
```sh
# Use osv-scanner from PATH
python scan.py osv cli -d ./my-awesome-project -o osv-cli-packages.json

# Provide an explicit scanner path
python scan.py osv cli -d ./my-awesome-project -o osv-cli-packages.json --scanner-path /usr/local/bin/osv-scanner
```

## 📄 License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for more information.
