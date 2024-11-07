# GitSpy
**Remote Repository Processor**

This project is a tool designed to process and verify remote Git repositories, retrieve repository information, check for a valid `.git` directory, and download files from the remote repository if available.

## Description

The main script, `main.py`, includes a `Repository` class that performs checks on the existence of a valid Git folder in the remote repository, verifies if directory listing is enabled, and initiates the download of configurable files. It relies on functions from the `tools` library to handle Git repository interactions and console message logging.

### Features
- Checks if the remote repository contains a valid `.git` folder.
- Identifies if directory listing is enabled on the repository.
- Downloads files from the remote exposed repository.

## Requirements

To run this project, ensure you have:
- **Python 3.8** or higher
- Required dependencies specified in the `tools` library

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/nikitacontreras/gitspy.git
   cd gitspy
   ```

2. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the `main.py` script to process a set of URLs using the `Repository` class. You can add additional URLs in the `main()` function within the script.

```bash
python main.py
```

## Example Output

The script logs progress messages to the console, including:
- Success messages if a valid `.git` directory is found.
- Error messages if no repository is found at the specified URL.
- Messages indicating whether directory listing is enabled or disabled.

## Contributing

Feel free to submit a **pull request** or open an **issue** to report bugs or request features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
