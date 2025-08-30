import argparse
import json
import os
import subprocess
import sys
import shutil
from typing import Dict, Any, List, Optional


def run_scanner(scanner_path: Optional[str], project_path: str) -> Dict[str, Any]:
    """
    Executes the osv-scanner command on the given project path
    and returns the parsed JSON output.
    """
    command = [
        scanner_path or "osv-scanner",
        "scan",
        "source",
        "-r",
        "--all-packages",
        "--format=json",
        project_path,
    ]
    print(f"🚀 Executing command: {' '.join(command)}")

    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        )

        output = process.stdout.strip()
        if not output:
            print("❌ Error: No output returned from osv-scanner.", file=sys.stderr)
            if process.returncode != 0:
                print(
                    f"⚠️ osv-scanner exited with code {process.returncode}.",
                    file=sys.stderr,
                )
            sys.exit(1)

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            print(
                "❌ Error: Failed to parse JSON output from osv-scanner.",
                file=sys.stderr,
            )
            if process.returncode != 0:
                print(
                    f"⚠️ osv-scanner exited with code {process.returncode}.",
                    file=sys.stderr,
                )
            preview = output.splitlines()[:10]
            print("📄 Output preview:", file=sys.stderr)
            for line in preview:
                print(line, file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError:
        print(f"❌ Error: Command '{command[0]}' not found.", file=sys.stderr)
        print(
            "⚠️ Please ensure osv-scanner is installed and in your system's PATH, or provide the path using --scanner-path.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def process_scan_results(full_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses the full JSON output from osv-scanner, simplifying the packages structure.
    """
    processed_results = []
    if not full_results or "results" not in full_results:
        return []

    for result_group in full_results["results"]:
        new_group = {"source": result_group.get("source", {})}
        new_packages_list = []
        original_packages = result_group.get("packages", [])
        if original_packages:
            for pkg_info in original_packages:
                if "package" in pkg_info:
                    new_packages_list.append(pkg_info["package"])
        new_group["packages"] = new_packages_list
        processed_results.append(new_group)
    return processed_results


def run_osv_scanner_cli(
    project_path: str, output_file: str, scanner_path: Optional[str] = None
):
    """
    Callable entry point for the OSV-Scanner CLI wrapper.
    """
    scanner_executable = scanner_path
    if not scanner_executable:
        if not shutil.which("osv-scanner"):
            print("❌ Error: 'osv-scanner' command not found.", file=sys.stderr)
            print(
                "⚠️ Please provide the path using --scanner-path or ensure it's in your system's PATH.",
                file=sys.stderr,
            )
            sys.exit(1)
    elif not os.path.exists(scanner_executable):
        print(
            f"❌ Error: Provided scanner path does not exist: {scanner_executable}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("🟢 --- Starting OSV-Scanner (CLI Wrapper) ---")
    full_scan_results = run_scanner(scanner_executable, project_path)
    print("✅ --- OSV-Scanner Finished ---")

    print("🔎 --- Processing Scan Results ---")
    processed_results = process_scan_results(full_scan_results)

    if not processed_results:
        print("📭 No packages were identified by the scanner.")
    else:
        print(f"📦 Found {len(processed_results)} result group(s).")

    if output_file:
        print(f"💾 Saving processed results to {output_file}...")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(processed_results, f, indent=2, ensure_ascii=False)
            print("🎉 Successfully saved results.")
        except IOError as e:
            print(
                f"❌ Error: Could not write to file {output_file}: {e}", file=sys.stderr
            )


def main():
    parser = argparse.ArgumentParser(
        description="A Python runner for osv-scanner to find all packages in a project.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-d", "--directory", required=True, help="The root path of the project to scan."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to save the filtered JSON results file.",
    )
    parser.add_argument(
        "--scanner-path", help="Optional path to the osv-scanner executable."
    )

    args = parser.parse_args()
    run_osv_scanner_cli(args.directory, args.output, args.scanner_path)


if __name__ == "__main__":
    main()
