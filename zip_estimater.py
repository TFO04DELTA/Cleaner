import zipfile
import os
import sys

def get_zip_uncompressed_size(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        total = sum([zinfo.file_size for zinfo in z.infolist()])
    return total

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def prompt_unzip(zip_path, extract_to='.'):
    unzip_size = get_zip_uncompressed_size(zip_path)
    print(f"Estimated unzip size for '{zip_path}': {format_bytes(unzip_size)}")
    cont = input("Proceed with extraction? (y/n): ").strip().lower()
    if cont != 'y':
        print("Aborted by user.")
        sys.exit(0)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(path=extract_to)
    print(f"Extracted to '{extract_to}'")

def main():
    input_path = input("Enter input file path: ").strip()

    if not os.path.isfile(input_path):
        print("File does not exist.")
        sys.exit(1)

    if input_path.endswith('.zip'):
        prompt_unzip(input_path, extract_to='extracted')
        # Assume your processing then runs on files inside 'extracted' folder
    else:
        print("Processing file without extraction.")

    # Prompt for output format
    print("Select output format:")
    print("1) .txt (email:password)")
    print("2) .jsonl (json per line)")
    print("3) Both")
    choice = input("Enter choice [1/2/3]: ").strip()

    output_txt = output_json = None
    if choice in ('1', '3'):
        output_txt = input("Enter output .txt filename: ").strip()
    if choice in ('2', '3'):
        output_json = input("Enter output .jsonl filename: ").strip()

    # Here you would call your cleaning functions, passing these filenames

    print("Setup complete. Starting processing...")

if __name__ == "__main__":
    main()
