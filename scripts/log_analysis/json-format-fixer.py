import json
import sys
import os

def fix_missing_braces_inplace(file_path):
    temp_path = file_path + '.tmp'
    with open(file_path, 'r') as infile, open(temp_path, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                outfile.write(line + '\n')
            except json.JSONDecodeError:
                if line.endswith(','):
                    line = line.rstrip(',')
                if not line.endswith('}'):
                    line += '}'
                try:
                    json.loads(line)
                    outfile.write(line + '\n')
                except json.JSONDecodeError:
                    print(f"Skipping invalid line: {line}", file=sys.stderr)

    os.replace(temp_path, file_path)

if __name__ == "__main__":
    fix_missing_braces_inplace(sys.argv[1])