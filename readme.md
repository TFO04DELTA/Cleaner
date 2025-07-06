A Python tool to clean and normalize data breach dumps — supports compressed files, shows progress bars, outputs .txt or .jsonl, and provides summary stats.
Installation

    Clone or download this repo.

    Install Python dependencies:

pip install -r requirements.txt

Usage

Run the script with one or more breach dump files (supports .txt, .csv, .json, .sql, .zip, .gz, .bz2, .xz):

python clean_breach.py file1.txt file2.zip dump.json.gz

The script will:

    Automatically unzip/extract compressed files

    Clean and deduplicate data (valid emails + passwords)

    Show a progress bar during processing

    Prompt you to choose output format:

        .txt (newline delimited: email:password)

        .jsonl (one JSON object per line)

        Or both

    Ask for output file names

    Print summary statistics (total entries, top domains, top passwords)

Example

python clean_breach.py leaks.zip bigdump.txt

Output prompt:

📤 Choose Output Format:
1. .txt (newline-delimited email:password)
2. .jsonl (1 JSON object per line)
3. Both
Enter choice [1/2/3]: 3

Enter output .txt filename (e.g., output.txt): cleaned_leaks.txt
Enter output .jsonl filename (e.g., output.jsonl): cleaned_leaks.jsonl

After processing, the cleaned files will be saved as specified.
Notes

    Supports .zip archives (auto-extracts all files inside)

    Supports compressed files .gz, .bz2, .xz transparently

    Requires Python 3.6+

    Requires packages listed in requirements.txt
