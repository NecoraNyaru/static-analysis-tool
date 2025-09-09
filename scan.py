#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scan.py
import argparse
import os
import sys

from osv.cli_runner import run_osv_scanner_cli

# Add the project root to the Python path to ensure all modules can be found.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- Import project modules ---
from osv.api_scanner import scan_project_for_vendored_libs
from tpl.scanner import scanner as TPLScanner
from tpl.utils.utils import save_js
from oss.osscollector.OSS_Collector import collect as oss_collect
from oss.preprocessor.Preprocessor_full import preprocess as oss_preprocess_full
from oss.preprocessor.Preprocessor_lite import preprocess as oss_preprocess_lite
from oss.detector.Detector import detect as oss_detect


# --- Command Handlers ---


def handle_tpl(args):
    """Handler for the 'tpl' command."""
    print("\n🚀 Running TPL Scanner...")
    scan_dir = args.directory
    if not os.path.isdir(scan_dir):
        print(f"❌ Error: Target directory not found at {scan_dir}", file=sys.stderr)
        sys.exit(1)
    scanner_obj = TPLScanner(scan_dir)
    results = scanner_obj.to_dict()
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        print(f"❌ Error: Output directory not found at {output_dir}", file=sys.stderr)
        sys.exit(1)
    save_js(results, output_path)
    print(f"\n✅ TPL Scanner analysis complete. Results saved to {output_path}")


def handle_oss_collect(args):
    """Handler for the 'oss collect' command."""
    print("\n🚀 Running OSS Collector...")
    # Convert paths to absolute to ensure they are valid after changing directories
    input_file_abs = os.path.abspath(args.input)
    output_dir_abs = os.path.abspath(args.output_dir)
    ctags_path_abs = os.path.abspath(args.ctags_path) if args.ctags_path else None

    if not os.path.isfile(input_file_abs):
        print(f"❌ Error: Input file not found at {input_file_abs}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(output_dir_abs):
        print(f"❌ Error: Output directory not found at {output_dir_abs}", file=sys.stderr)
        sys.exit(1)

    print("✅ Executing collector...")
    oss_collect(
        git_urls_path=input_file_abs,
        output_dir=output_dir_abs,
        ctags_bin_path=ctags_path_abs,
    )

    print(f"\n✅ OSS collection complete. Results saved to {output_dir_abs}")


def handle_oss_preprocess(args):
    """Handler for the 'oss preprocess' command."""
    print(f"\n🚀 Running OSS Preprocessor (mode: {args.mode})...")
    # Convert paths to absolute to ensure they are valid after changing directories
    input_dir_abs = os.path.abspath(args.input_dir)
    output_dir_abs = os.path.abspath(args.output_dir)

    if not os.path.isdir(input_dir_abs):
        print(f"❌ Error: Input directory not found at {input_dir_abs}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(output_dir_abs):
        print(f"❌ Error: Output directory not found at {output_dir_abs}", file=sys.stderr)
        sys.exit(1)

    print("✅ Executing preprocessor...")
    if args.mode == "full":
        oss_preprocess_full(
            collector_dir=input_dir_abs,
            preprocessor_dir=output_dir_abs,
            theta_val=args.theta,
        )
    else:
        oss_preprocess_lite(
            collector_dir=input_dir_abs,
            preprocessor_dir=output_dir_abs,
            theta_val=args.theta,
        )

    print(f"\n✅ OSS preprocessing complete. Results saved to {output_dir_abs}")


def handle_oss_detect(args):
    """Handler for the 'oss detect' command."""
    print("\n🚀 Running OSS Detector...")
    target_dir_abs = os.path.abspath(args.directory)
    output_dir_abs = os.path.abspath(args.output_dir)
    collector_dir_abs = os.path.abspath(args.collector_dir)
    preprocessor_dir_abs = os.path.abspath(args.preprocessor_dir)
    ctags_path_abs = os.path.abspath(args.ctags_path) if args.ctags_path else None

    if not os.path.isdir(target_dir_abs):
        print(f"❌ Error: Target directory not found at {target_dir_abs}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(output_dir_abs):
        print(f"❌ Error: Output directory not found at {output_dir_abs}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(collector_dir_abs):
        print(f"❌ Error: Collector directory not found at {collector_dir_abs}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(preprocessor_dir_abs):
        print(f"❌ Error: Preprocessor directory not found at {preprocessor_dir_abs}", file=sys.stderr)
        sys.exit(1)

    print("✅ Executing detector...")
    oss_detect(
        target_path=target_dir_abs,
        output_dir=output_dir_abs,
        collector_dir=collector_dir_abs,
        preprocessor_dir=preprocessor_dir_abs,
        ctags_bin_path=ctags_path_abs,
    )

    print(f"\n✅ OSS detection complete. Results saved to {output_dir_abs}")


def handle_osv_api(args):
    """Handler for the 'osv api' command."""
    print("\n🚀 Running OSV Vendored Library Scanner (API)...")
    scan_dir = args.directory
    if not os.path.isdir(scan_dir):
        print(f"❌ Error: Target directory not found at {scan_dir}", file=sys.stderr)
        sys.exit(1)
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        print(f"❌ Error: Output directory not found at {output_dir}", file=sys.stderr)
        sys.exit(1)
    scan_project_for_vendored_libs(
        project_root=scan_dir,
        scan_git=args.scan_git,
        threshold=args.threshold,
        output_file=args.output,
    )
    print(
        f"\n✅ OSV Vendored Library Scanner (API) scan complete. Results saved to {args.output}"
    )


def handle_osv_cli(args):
    """Handler for the 'osv cli' command."""
    print("\n🚀 Running OSV Scanner (CLI Wrapper)...")
    scan_dir = args.directory
    if not os.path.isdir(scan_dir):
        print(f"❌ Error: Target directory not found at {scan_dir}", file=sys.stderr)
        sys.exit(1)
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        print(f"❌ Error: Output directory not found at {output_dir}", file=sys.stderr)
        sys.exit(1)
    run_osv_scanner_cli(
        project_path=scan_dir,
        output_file=args.output,
        scanner_path=args.scanner_path,
    )
    print(
        f"\n✅ OSV Scanner (CLI Wrapper) scan complete. Results saved to {args.output}"
    )


# --- Main Argparse Setup ---


def main():
    """Sets up the command-line interface and executes the chosen command."""
    parser = argparse.ArgumentParser(
        description="A Static Analysis Tool.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="target", required=True, help="The target to detect: tpl, oss, osv"
    )

    # --- TPL Subparser ---
    parser_tpl = subparsers.add_parser(
        "tpl", help="Extract third-party libraries from a C/C++ project."
    )
    parser_tpl.add_argument(
        "-d", "--directory", required=True, help="Directory to scan for dependencies."
    )
    parser_tpl.add_argument(
        "-o",
        "--output",
        default="results.json",
        help="Path to save the JSON results (default: results.json).",
    )
    parser_tpl.set_defaults(func=handle_tpl)

    # --- OSS Subparser ---
    parser_oss = subparsers.add_parser(
        "oss", help="Identify open-source software in a project."
    )
    oss_subparsers = parser_oss.add_subparsers(
        dest="command", required=True, help="command to execute"
    )

    # OSS 'collect' command
    parser_collect = oss_subparsers.add_parser(
        "collect", help="Step 1: Collect OSS functions to build the database."
    )
    parser_collect.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input file containing git clone URLs (e.g., oss/osscollector/sample).",
    )
    parser_collect.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Output directory for the collector results.",
    )
    parser_collect.add_argument(
        "--ctags-path", help="Optional path to the universal-ctags binary."
    )
    parser_collect.set_defaults(func=handle_oss_collect)

    # OSS 'preprocess' command
    parser_preprocess = oss_subparsers.add_parser(
        "preprocess", help="Step 2: Preprocess functions to create the component DB."
    )
    parser_preprocess.add_argument(
        "--mode",
        choices=["full", "lite"],
        default="full",
        help="Preprocessor mode (default: full).",
    )
    parser_preprocess.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Path to the collector's results directory.",
    )
    parser_preprocess.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Path to the preprocessor's output directory.",
    )
    parser_preprocess.add_argument(
        "--theta", type=float, default=0.1, help="Theta value (default: 0.1)."
    )
    parser_preprocess.set_defaults(func=handle_oss_preprocess)

    # OSS 'detect' command
    parser_detect = oss_subparsers.add_parser(
        "detect", help="Step 3: Detect components in a target software project."
    )
    parser_detect.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Path to the root of the target software to analyze.",
    )
    parser_detect.add_argument(
        "-o", "--output-dir", required=True, help="Directory to save detection results."
    )
    parser_detect.add_argument(
        "--collector-dir",
        required=True,
        help="Path to the collector's output directory.",
    )
    parser_detect.add_argument(
        "--preprocessor-dir",
        required=True,
        help="Path to the preprocessor's output directory.",
    )
    parser_detect.add_argument(
        "--theta",
        type=float,
        default=0.1,
        help="Threshold for component identification (default: 0.1).",
    )
    parser_detect.add_argument(
        "--ctags-path", help="Optional path to the universal-ctags binary."
    )
    parser_detect.set_defaults(func=handle_oss_detect)

    # --- OSV Subparser ---
    parser_osv = subparsers.add_parser(
        "osv", help="Identify packages used in a project via OSV."
    )
    osv_subparsers = parser_osv.add_subparsers(
        dest="command", required=True, help="OSV scanner mode to use"
    )

    # OSV 'api' command
    parser_osv_api = osv_subparsers.add_parser(
        "api", help="Identify vendored libraries using OSV API file hashing."
    )
    parser_osv_api.add_argument(
        "-d", "--directory", required=True, help="The root path of the project to scan."
    )
    parser_osv_api.add_argument(
        "-o", "--output", required=True, help="Path to save the JSON results file."
    )
    parser_osv_api.add_argument(
        "--scan-git",
        action="store_true",
        help="If set, don't skip .git directories during scan.",
    )
    parser_osv_api.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        help="Minimum score for a confident match (default: 0.15).",
    )
    parser_osv_api.set_defaults(func=handle_osv_api)

    # OSV 'cli' command
    parser_osv_cli = osv_subparsers.add_parser(
        "cli", help="Scan all package types using the external osv-scanner tool."
    )
    parser_osv_cli.add_argument(
        "-d", "--directory", required=True, help="The root path of the project to scan."
    )
    parser_osv_cli.add_argument(
        "-o", "--output", required=True, help="Path to save the JSON results file."
    )
    parser_osv_cli.add_argument(
        "--scanner-path", help="Optional path to the osv-scanner executable."
    )
    parser_osv_cli.set_defaults(func=handle_osv_cli)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
