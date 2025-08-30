import os
import hashlib
import base64
import json
import argparse
import requests
from typing import Dict, Any, Optional, List

VENDORED_LIB_NAMES = {
    "3rdparty",
    "dep",
    "deps",
    "thirdparty",
    "third-party",
    "third_party",
    "libs",
    "external",
    "externals",
    "vendor",
    "vendored",
}
FILE_EXTS = (".hpp", ".h", ".hh", ".cc", ".c", ".cpp")
MAX_DETERMINE_VERSION_FILES = 10000
OSV_API_URL = "https://api.osv.dev/v1experimental/determineversion"


def query_determine_versions(
    library_path: str, scan_git_dir: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Core extraction logic: Scans a single library directory, hashes files,
    and queries the OSV API.
    """
    print(f"\n[Extractor] Analyzing potential library at: {library_path}")
    file_hashes = []

    for root, dirs, files in os.walk(library_path, topdown=True):
        dirs[:] = [
            d
            for d in dirs
            if (scan_git_dir or d != ".git") and d.lower() not in VENDORED_LIB_NAMES
        ]

        for filename in files:
            if not filename.endswith(FILE_EXTS):
                continue

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, library_path)

            try:
                with open(full_path, "rb") as f:
                    content = f.read()
                    md5_digest = hashlib.md5(content).digest()
                    b64_hash = base64.b64encode(md5_digest)
                    hash_str = b64_hash.decode("utf-8")

                    file_hashes.append(
                        {
                            "file_path": relative_path.replace("\\", "/"),
                            "hash": hash_str,
                        }
                    )
            except IOError as e:
                print(f"  Warning: Could not read file {full_path}: {e}")
                continue

            if len(file_hashes) >= MAX_DETERMINE_VERSION_FILES:
                print(
                    f"  Warning: Reached file limit of {MAX_DETERMINE_VERSION_FILES}. Stopping hash collection."
                )
                break

        if len(file_hashes) >= MAX_DETERMINE_VERSION_FILES:
            break

    print(f"  Found {len(file_hashes)} relevant C/C++ files to hash.")
    if not file_hashes:
        return None

    library_name = os.path.basename(os.path.normpath(library_path))
    payload = {"name": library_name, "file_hashes": file_hashes}

    print(f"  Sending request to OSV API for library '{library_name}'...")
    try:
        response = requests.post(OSV_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error calling OSV API: {e}")
        if e.response is not None:
            print(f"  Response Body: {e.response.text}")
        return None


def scan_project_for_vendored_libs(
    project_root: str, scan_git: bool, threshold: float, output_file: Optional[str]
):
    """
    Scanner Framework: Walks a project directory to find and analyze all
    vendored libraries, saving confident matches to a list.
    """
    print(f"Starting scan for vendored libraries in: {project_root}")
    found_any = False
    all_results: List[Dict[str, Any]] = []

    for root, dirs, _ in os.walk(project_root, topdown=True):
        parent_dir_name = os.path.basename(root).lower()
        if parent_dir_name in VENDORED_LIB_NAMES:
            print(f"[Scanner] Found potential vendor directory: {root}")
            for lib_dir_name in dirs:
                library_path = os.path.join(root, lib_dir_name)
                if not os.path.isdir(library_path):
                    continue

                found_any = True
                result = query_determine_versions(library_path, scan_git)

                if not result or not result.get("matches"):
                    print(
                        "  -> No potential matches found by the OSV API for this library."
                    )
                    continue

                best_match = result["matches"][0]
                if best_match["score"] > threshold:
                    repo_info = best_match.get("repo_info", {})
                    # --- Console Logging (preserved) ---
                    print("\n  --- ✅ Confident Match Found ---")
                    print(f"  Library Path: {library_path}")
                    print(
                        f"  Score: {best_match['score']:.2f} (Threshold: {threshold})"
                    )
                    print(f"  Repository: {repo_info.get('address')}")
                    print(
                        f"  Version/Tag: {repo_info.get('version') or repo_info.get('tag')}"
                    )

                    # --- Collect result for JSON output ---
                    result_data = {
                        "library_path": library_path,
                        "score": best_match["score"],
                        "repo_info": repo_info,
                    }
                    all_results.append(result_data)
                else:
                    print("\n  --- ❌ No confident match found ---")
                    print(
                        f"  Best match score was {best_match['score']:.2f}, below the threshold of {threshold}."
                    )

    if not found_any:
        print(
            "\nScan complete. No directories matching the vendored library structure were found."
        )
        return

    print(f"\nScan complete. Found {len(all_results)} confident matches.")

    # --- Write collected results to JSON file if path is provided ---
    if output_file:
        print(f"Saving results to {output_file}...")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print("Successfully saved results.")
        except IOError as e:
            print(f"Error: Could not write to file {output_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Scans a project directory to find and identify all C/C++ vendored libraries using the OSV API.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("project_path", help="The root path of the project to scan.")
    parser.add_argument(
        "--scan-git",
        action="store_true",
        help="If set, do not skip directories containing a '.git' subdirectory.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        help="The minimum score for a match to be considered valid. (Default: 0.15)",
    )
    parser.add_argument("-o", "--output", help="Path to save the JSON results file.")

    args = parser.parse_args()
    scan_project_for_vendored_libs(
        args.project_path, args.scan_git, args.threshold, args.output
    )


if __name__ == "__main__":
    main()
