#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# obtain_repo.py
import argparse
import json
import os
import sys
import time
from functools import partial

import requests
from tqdm.contrib.concurrent import thread_map

# Configurations
BASE_URL = "https://api.github.com/search/repositories"
MAX_REPOS_PER_QUERY = 1000  # GitHub's API limit

# Base query parts
BASE_QUERY = "language:C++ language:C fork:false"

# Define star ranges to partition the search
STAR_RANGES = [
    ">10000",
    "5001..10000",
    "4001..5000",
    "3001..4000",
    "2001..3000",
    "1501..2000",
    "1251..1500",
    "1126..1250",
    "1001..1125",
]


def safe_request(url, headers, params=None, json_data=None, max_retries=3):
    """A request function with rate-limit handling and retries."""
    for _ in range(max_retries):
        try:
            if json_data:
                response = requests.post(
                    url, json=json_data, headers=headers, timeout=10
                )
            else:
                response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200 or response.status_code == 404:
                return response

            if response.status_code == 403 and "rate limit" in response.text.lower():
                reset_time = int(
                    response.headers.get("X-RateLimit-Reset", time.time() + 60)
                )
                sleep_time = max(reset_time - time.time(), 10)
                print(f"Rate limited. Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                continue

            print(f"Request failed: {response.status_code} - {response.text}")
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            time.sleep(5)

    return None


def fetch_repos_for_query(query, headers):
    """Fetch up to 1000 repositories for a single specific query."""
    repositories = []
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 100,
        "page": 1,
    }

    while len(repositories) < MAX_REPOS_PER_QUERY:
        response = safe_request(BASE_URL, headers, params=params)
        if not response:
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            repositories.append(
                {
                    "full_name": item["full_name"],
                    "html_url": item["html_url"],
                    "default_branch": item["default_branch"],
                    "stars": item["stargazers_count"],
                    "fork": item["fork"],
                }
            )

        if "next" not in response.links:
            break
        params["page"] += 1
        # Prevent fetching more than the API limit allows
        if params["page"] > 10:
            print("Reached maximum page limit for this query.")
            break

    return repositories


def process_repository(repo, headers):
    """Process a single repository to check for CMakeLists.txt."""
    cmake_url = (
        f"https://api.github.com/repos/{repo['full_name']}/contents/CMakeLists.txt"
    )
    # Use a HEAD request for efficiency as we only need the status code
    response = safe_request(cmake_url, headers)
    has_cmake = response.status_code == 200 if response else False

    # # Get language information (secondary verification)
    # lang_response = safe_request(repo["languages_url"], headers)
    # languages = lang_response.json().keys() if lang_response else []

    # # Get the commit id of the default branch
    # commit_url = f"https://api.github.com/repos/{repo['full_name']}/commits/{repo['default_branch']}"
    # commit_response = safe_request(commit_url, headers)
    # commit_id = None
    # if commit_response and commit_response.status_code == 200:
    #     commit_data = commit_response.json()
    #     commit_id = commit_data.get("sha")

    return {
        **repo,
        # "commit_id": commit_id,
        "has_cmake": has_cmake,
        # "languages": list(languages),
        # "is_valid": has_cmake and ("C" in languages or "C++" in languages),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and process GitHub repositories."
    )
    parser.add_argument(
        "-t",
        "--github-token",
        type=str,
        required=True,
        help="GitHub token for API access",
    )
    parser.add_argument(
        "-w",
        "--max-workers",
        type=int,
        default=20,
        help="Number of concurrent threads (default: 20)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    if output_dir and not os.path.isdir(output_dir):
        print(f"❌ Error: Output directory not found at {output_dir}", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {args.github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    all_repositories = []
    print("Fetching repository list by slicing star counts...")

    # Iterate through each star range to gather repositories
    for s_range in STAR_RANGES:
        query = f"{BASE_QUERY} stars:{s_range}"
        print(f"\nExecuting query: '{query}'")
        repos_for_range = fetch_repos_for_query(query, headers)
        all_repositories.extend(repos_for_range)
        print(f"Found {len(repos_for_range)} repositories in this range.")

    # --- De-duplicate the results ---
    # A repo's star count could change, making it appear in two queries.
    # We use a dictionary with the unique 'full_name' as the key to remove duplicates.
    unique_repos_dict = {repo["full_name"]: repo for repo in all_repositories}
    unique_repositories = list(unique_repos_dict.values())

    # Optional: Re-sort the final list by stars
    unique_repositories.sort(key=lambda r: r["stars"], reverse=True)

    print(f"\nTotal unique repositories found: {len(unique_repositories)}")

    # Process all unique repositories in parallel
    print("Processing repositories to check for CMakeLists.txt...")

    process_func = partial(process_repository, headers=headers)
    results = list(
        thread_map(
            process_func,
            unique_repositories,
            max_workers=args.max_workers,
            desc="Processing repos",
            unit="repo",
        )
    )

    valid_repos = [r for r in results if r["has_cmake"]]
    excluded_repos = [r for r in results if not r["has_cmake"]]

    # Save the results
    with open(os.path.join(output_dir, "cmake_repos.json"), "w") as f:
        json.dump(valid_repos, f, indent=2)

    with open(os.path.join(output_dir, "excluded_repos.json"), "w") as f:
        json.dump(excluded_repos, f, indent=2)

    print("\n--- Results ---")
    print(f"Repositories with CMakeLists.txt: {len(valid_repos)}")
    print(f"Repositories without CMakeLists.txt: {len(excluded_repos)}")
    print(f"Output files saved in: {output_dir}")


if __name__ == "__main__":
    main()
