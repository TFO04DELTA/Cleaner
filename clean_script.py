import csv
import json
import os
import re
import chardet
import argparse
import tempfile
import shutil
import gzip
import bz2
import lzma
import zipfile
from pathlib import Path
from collections import Counter
from tqdm import tqdm

CLEANED_SET = set()
DELIMITERS = [':', '|', ';', ',']

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read(10000)  # sample first 10k bytes for encoding
    return chardet.detect(raw)['encoding'] or 'utf-8'

def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", email)

def normalize_line(line):
    for delim in DELIMITERS:
        if delim in line:
            parts = line.strip().split(delim)
            if len(parts) >= 2:
                email = parts[0].strip().lower()
                password = delim.join(parts[1:]).strip()
                if is_valid_email(email):
                    return email, password
    return None

def open_maybe_compressed(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == '.gz':
        return gzip.open(filepath, 'rt', encoding=detect_encoding(filepath), errors='ignore')
    elif ext == '.bz2':
        return bz2.open(filepath, 'rt', encoding=detect_encoding(filepath), errors='ignore')
    elif ext == '.xz':
        return lzma.open(filepath, 'rt', encoding=detect_encoding(filepath), errors='ignore')
    else:
        return open(filepath, 'r', encoding=detect_encoding(filepath), errors='ignore')

def clean_txt(filepath):
    with open_maybe_compressed(filepath) as f:
        for line in tqdm(f, desc=f"Processing {os.path.basename(filepath)}"):
            result = normalize_line(line)
            if result:
                CLEANED_SET.add(result)

def clean_csv(filepath):
    with open_maybe_compressed(filepath) as f:
        reader = csv.reader(f)
        for row in tqdm(reader, desc=f"Processing {os.path.basename(filepath)}"):
            if len(row) >= 2:
                email = row[0].strip().lower()
                password = row[1].strip()
                if is_valid_email(email):
                    CLEANED_SET.add((email, password))

def clean_json(filepath):
    with open_maybe_compressed(filepath) as f:
        try:
            data = json.load(f)
            for record in tqdm(data, desc=f"Processing {os.path.basename(filepath)}"):
                email = str(record.get('email', '')).strip().lower()
                password = str(record.get('password', '')).strip()
                if is_valid_email(email):
                    CLEANED_SET.add((email, password))
        except json.JSONDecodeError:
            print(f"[!] Skipped JSON (malformed): {filepath}")

def clean_sql(filepath):
    with open_maybe_compressed(filepath) as f:
        for line in tqdm(f, desc=f"Processing {os.path.basename(filepath)}"):
            result = normalize_line(line)
            if result:
                CLEANED_SET.add(result)

def extract_zip(filepath):
    temp_dir = tempfile.mkdtemp(prefix="breach_unzip_")
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        # Return list of extracted files
        return [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
    except Exception as e:
        print(f"[!] Error extracting zip {filepath}: {e}")
        shutil.rmtree(temp_dir)
        return []

def process_file(filepath):
    ext = Path(filepath).suffix.lower()

    # Handle zip specially
    if ext == '.zip':
        extracted_files = extract_zip(filepath)
        for ef in extracted_files:
            process_file(ef)
        return

    # Detect file type and clean accordingly
    if ext == '.csv':
        clean_csv(filepath)
    elif ext == '.json':
        clean_json(filepath)
    elif ext == '.sql':
        clean_sql(filepath)
    else:
        # fallback for .txt, .log, .gz, .bz2, .xz, and unknown extensions
        clean_txt(filepath)

def write_txt(out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for email, password in sorted(CLEANED_SET):
            f.write(f"{email}:{password}\n")

def write_jsonl(out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for email, password in sorted(CLEANED_SET):
            json.dump({"email": email, "password": password}, f)
            f.write('\n')

def prompt_user_options():
    print("\n📤 Choose Output Format:")
    print("1. .txt (newline-delimited email:password)")
    print("2. .jsonl (1 JSON object per line)")
    print("3. Both")
    format_choice = input("Enter choice [1/2/3]: ").strip()

    txt_file = ""
    json_file = ""

    if format_choice == "1":
        txt_file = input("Enter output .txt filename (e.g., output.txt): ").strip()
    elif format_choice == "2":
        json_file = input("Enter output .jsonl filename (e.g., output.jsonl): ").strip()
    elif format_choice == "3":
        txt_file = input("Enter output .txt filename (e.g., output.txt): ").strip()
        json_file = input("Enter output .jsonl filename (e.g., output.jsonl): ").strip()
    else:
        print("[!] Invalid selection. Exiting.")
        exit(1)

    return format_choice, txt_file, json_file

def print_summary():
    emails = [email for email, _ in CLEANED_SET]
    passwords = [password for _, password in CLEANED_SET]
    domains = [email.split('@')[1] for email in emails if '@' in email]

    print("\n📊 Summary Stats:")
    print(f"Total valid records: {len(CLEANED_SET)}")
    print(f"Unique emails: {len(set(emails))}")

    domain_counts = Counter(domains).most_common(10)
    print("\nTop 10 email domains:")
    for domain, count in domain_counts:
        print(f" - {domain}: {count}")

    pwd_counts = Counter(passwords).most_common(10)
    print("\nTop 10 passwords:")
    for pwd, count in pwd_counts:
        print(f" - {pwd}: {count}")

def main():
    parser = argparse.ArgumentParser(description="🧹 Breach Cleaner with auto unzip, progress bar & stats")
    parser.add_argument('files', nargs='+', help='Input files to clean (supports .zip, .gz, .bz2, .xz)')
    args = parser.parse_args()

    print(f"\n[🔍] Starting cleanup on {len(args.files)} file(s)...")
    for file in args.files:
        if os.path.isfile(file):
            print(f"[+] Processing: {file}")
            process_file(file)
        else:
            print(f"[!] File not found: {file}")

    print(f"\n[✔] Total valid unique entries: {len(CLEANED_SET)}")

    format_choice, txt_file, json_file = prompt_user_options()

    if format_choice == "1":
        write_txt(txt_file)
        print(f"[💾] .txt saved as {txt_file}")
    elif format_choice == "2":
        write_jsonl(json_file)
        print(f"[💾] .jsonl saved as {json_file}")
    elif format_choice == "3":
        write_txt(txt_file)
        write_jsonl(json_file)
        print(f"[💾] Saved both {txt_file} and {json_file}")

    print_summary()

    print("\n✅ Done.")

if __name__ == "__main__":
    main()
