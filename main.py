import sys
import requests
import json
from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
import numpy as np


ROOT_DIR = Path(__file__).parent

# These act as a crude cahing mechanism
OUTFILE = ROOT_DIR / "out.txt"
LAST_ARGS = ROOT_DIR / "cache.json" 

ARGS_CONTRIBUTORS = ["gh", "api", "--paginate", "/repos/berrnd/grocy/contributors?per_page=100", "--method", "GET"]
ARGS_COMMITS = ["gh", "api", "--paginate", "/repos/berrnd/grocy/commits?per_page=100", "--method", "GET"]

def execute(args, dump=False):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    result = json.loads(result.stdout)
    if dump:
        with open(str(OUTFILE), "w") as f:
            json.dump(result, f, indent=0, ensure_ascii=True)
    return result



def display_bar(x, labels=None, x_label=None, y_label=None):
        fig, ax = plt.subplots()
        if labels != None:
            ax.bar(labels, x)
        else:
            ax.bar(np.arange(len(x)), x)
            plt.xticks([])

        ax.set_xlabel(x_label, fontsize=10)
        ax.set_ylabel(y_label, fontsize=10)
        
        plt.show()

def display_stacked_bars(vals, labels=None, x_label=None, y_label=None):
        fig, ax = plt.subplots()
        len_vals = len(next(iter(vals.values())))
        if labels != None:
            x_values = labels
        else:
            x_values = np.arange(len_vals)
            plt.xticks([])

        bottom = np.zeros(len_vals)
        for key, value in vals.items():
            p = ax.bar(x_values, value, label=key, bottom=bottom)

            # ax.bar_label(p, padding=20)
            bottom += np.array(value)

        font_size = 25
        ax.set_xlabel(x_label, fontsize=font_size)
        ax.set_ylabel(y_label, fontsize=font_size)
        ax.tick_params(labelsize=font_size)
        ax.legend(loc="upper right", fontsize=font_size)
        plt.show()

def is_cached(args):
    LAST_ARGS.touch(exist_ok=True)

    with open(LAST_ARGS, "r") as f:
        content = f.read()
        if not content:
            j = ""
        else:
            j = json.load(f)
        
    if args != j:
        with open(LAST_ARGS, "w") as f:
            j = json.dump(args, f)
        return False
    else:
        return True

def get_data(args, cache=True):
    OUTFILE.touch(exist_ok=True)
    if cache and (is_cached(args)):
        with open(OUTFILE, "r") as f:
            return json.load(f)
    else:
        return execute(args, dump=cache)

def get_contributor_data():
    data = get_data(ARGS_CONTRIBUTORS)

    counts = [item["contributions"] for item in data]
    
    commits_excld_berrnd = 0
    for _ in counts[1:]:
        commits_excld_berrnd += 1
    print(f"Commits excluding Bernd: {commits_excld_berrnd}\n")

    display_bar([counts[0], commits_excld_berrnd], labels=["Bernd", "Others"], x_label="Contributors", y_label="Number of Commits")

def get_commits_count():
    data = get_data(ARGS_COMMITS)
    print(f"Total commits: {len(data)}")
    return len(data)



def graph_request(query):
    with open(str(ROOT_DIR / ".env"), "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("GITHUB_AUTH_TOKEN"):
                token = line.split("=", 1)[1].strip()

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    return response.json()

def commit_query(after=None):
    after = "null" if after is None else f'"{after}"'
    return f"""
            query {{
                repository(owner: "berrnd", name: "grocy") {{
                    defaultBranchRef {{
                        target {{
                            ... on Commit {{
                                history(first: 100, after: {after}) {{
                                    nodes {{
                                        oid
                                        committedDate
                                        author {{
                                            name
                                            email
                                        }}
                                        additions
                                        deletions
                                    }}
                                    pageInfo {{
                                        endCursor
                                        hasNextPage
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
    """


def get_commit_data():
    total_commits = get_commits_count()
    cursor = None
    has_next = True

    stats = {}
    count = 0
    while has_next:
        data = graph_request(commit_query(cursor))
        history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]

        for commit in history["nodes"]:
            author = commit["author"]["name"]
            stats.setdefault(author, (0, 0, 0))

            stats[author] = (stats[author][0] + commit["additions"], stats[author][1] + commit["deletions"], stats[author][2] + 1)
            count += 1
            print(f"Downloading commits...{min(count/total_commits*100, 100):.2f}%\r", end="")
        
        page_info = history["pageInfo"]
        has_next = page_info["hasNextPage"]
        cursor = page_info["endCursor"]
        
    authors = []
    adds = []
    deletes = []
    commits = 0
    for key, value in sorted(stats.items(), key=lambda x: x[1][0] + x[1][1], reverse=True):
        authors.append(key)
        adds.append(value[0])
        deletes.append(value[1])
        commits += value[2]
        print(f"{key}: {value[0]} additions and {value[1]} deletions across {value[2]} commits for a total of {value[0]+value[1]} changes")

    vals = {"Additions": adds, "Deletions": deletes}
    display_stacked_bars(vals, x_label="Contributors", y_label="Contributions")
    vals_excluding_bernd = {"Additions": adds[1:], "Deletions": deletes[1:]}
    display_stacked_bars(vals_excluding_bernd, x_label="Contributors", y_label="Contributions")

    print(f"Total Additions: {sum(adds)} Total Deletions: {sum(deletes)}")
    print(f"Total Additions w/o Bernd: {sum(adds[1:])} Total Deletions w/o Bernd: {sum(deletes[1:])}")
    print(f"Total Commits: {commits}")

if __name__ == "__main__":
    # args = sys.argv[1:]
    # if len(args) <= 1:
    #     print(f"Usage: {Path(__file__).name} [args...]")

    # execute(args)
    
    get_commit_data()