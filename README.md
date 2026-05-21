# Data Collection Script
Running the script fetches the relevant data and produces the graphs used in the report. The detailed stats have been recorded in `stats.txt`.

# How to  run
- Create `.env` in the project root and include your GitHub personal access token as follows. This is required to access the GitHub GraphQL API as explained in the [docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
```
GITHUB_AUTH_TOKEN = your_token
```
- open terminal and run the script using `python main.py > data.txt` (assuming you are in the project root). By default the output goes to stdout. If output is redirected to a file, make sure the file is not called `out.txt` as that name is used by the script to store commit data. 
