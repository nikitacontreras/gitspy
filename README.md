# GitSpy
```
 ____  __ _____   __ _____ _  _
(( ___ ||  ||    ((  ||_// \\//
 \\_|| ||  ||   \_)) ||     // 
```
**The Ultimate Multi-Protocol Reconnaissance & Extraction Engine**

GitSpy is a high-performance security tool designed to detect and extract sensitive data from exposed repository folders and configuration files. It supports Git, SVN, Mercurial, and various configuration exposures with a focus on speed, binary integrity, and recursive discovery.

---

## Key Features

- **Multi-Technology Probing**: Detects `.git`, `.svn`, `.hg`, `.env`, and `.DS_Store` exposures in a single pass.
- **Recursive Git Mining**: Fully parses the Git `index` (DIRC) and repository objects to reconstruct tree structures even without directory listing enabled.
- **Automatic Recovery & Repair**: Smart `--repair` flag to resume interrupted downloads by scanning local objects and identifying missing pieces.
- **High-Concurrency Engine**: "Impatient" mode with multi-threading and optimized connection pooling (tested with 1000+ parallel requests).
- **Binary Integrity Validation**: Advanced filtering to eliminate honeypots and HTML-based false positives by validating binary file signatures.
- **Subdomain Reconnaissance**: Passive discovery via SSL certificates (`crt.sh`) integrated into the scanning pipeline.
- **Lazy Directory Creation**: Prevents disk pollution by creating folders only when valid repository content is confirmed.

---

## Installation

```bash
git clone https://github.com/nikitacontreras/gitspy.git
cd gitspy
pip install -r requirements.txt
# Optional: link as a system command
ln -s $(pwd)/main.py /usr/local/bin/gitspy
```

---

## Usage Patterns

### 1. Simple Targeted Extraction
Extract a repository from a single known URL:
```bash
gitspy --url https://example.com/.git/
```

### 2. Massive Reconnaissance (Impatient Mode)
Process a list of thousands of domains with high concurrency:
```bash
gitspy --list targets.txt --speed impatient --concurrency 50
```

### 3. Subdomain Expansion & Probing
Identify all subdomains for a target and probe each for exposures:
```bash
gitspy --scan target.com --mode all
```

### 4. Resuming / Repairing Downloads
If a download was interrupted or partial, use the `--repair` flag to resume:
- **Repair a specific folder**:
  ```bash
  gitspy --repair-path ./repos/example.com/
  ```
- **Integrate into a list**:
  ```bash
  gitspy --list list.txt --repair
  ```
  *This will auto-detect which domains in the list already have local folders and continue them.*

---

## Parameters Reference

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `--url` | Input | Target URL (e.g., `https://example.com/.git/`) |
| `--list` | Input | Path to a text file with one URL/domain per line |
| `--scan` | Input | Domain to scan for subdomains via passive/active recon |
| `--repair-path` | Input | Local path to scan for existing repos to finish extraction |
| `--repair` | Flag | Enable repair mode for other inputs (URL/List/Scan) |
| `--speed` | Option | `patient` (sequential) or `impatient` (parallel) |
| `--concurrency` | Number | Parallel tasks (default: 5, recommended: 50+) |
| `--mode` | Option | Scanning mode for `--scan`: `passive`, `search`, or `all` |
| `--output` | Path | Directory to store results (default: `./repos`) |
| `--timeout` | Number | Request timeout in seconds (default: 15) |

---

## Extraction Logic

GitSpy doesn't just crawl files; it understands repository structures:
1. **Infrastructure Probes**: Validates if the target responds with valid binary repository data.
2. **Chain Analysis**: Pulls `HEAD` -> Resolves `refs/heads/...` -> Pulls the latest Commit object.
3. **Index Parsing**: If a Git `index` is found, it parses the binary entries to find all file hashes in the current working tree.
4. **Object Mining**: Iteratively downloads objects from `objects/XX/XXXX...` and decodes tree objects to find sub-trees and blobs.
5. **Validation**: Every file is validated in memory before being written to disk to ensure it's not a honeypot or an error page.

---

## Disclaimer
This tool is for educational and authorized security testing purposes only. The author is not responsible for any misuse or damage caused by this application.
