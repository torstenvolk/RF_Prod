
import streamlit as st
import requests
import time
import csv
import os.path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os


# Your GitHub personal access token
#github_token = st.secrets["github"]["github_api_key"]
github_token = os.getenv('github_api_key')
st.write("## GitHub Stars")

# Directory to save the CSV files
csv_dir = 'pages/github_stars'



# GraphQL query to fetch stargazers with their starredAt date
query = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazers(first: 100, after: $cursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        starredAt
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {github_token}",
    "Content-Type": "application/json",
}

url = "https://api.github.com/graphql"

def fetch_stargazers(owner, name, last_fetched_date=None):
    has_next_page = True
    cursor = None
    stargazers = []

    # Create a text element to display the current count of stars
    star_count_text = st.empty()

    while has_next_page:
        variables = {"owner": owner, "name": name, "cursor": cursor}
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

        response_json = response.json()
        if "errors" in response_json:
            st.warning(response_json["errors"])
            return []

        data = response_json["data"]["repository"]["stargazers"]
        new_stargazers = [{"starredAt": edge["starredAt"]} for edge in data["edges"]]
        if last_fetched_date is not None:
            new_stargazers = [star for star in new_stargazers if datetime.strptime(star["starredAt"], "%Y-%m-%dT%H:%M:%SZ") > last_fetched_date]
            if not new_stargazers:
                break
        stargazers.extend(new_stargazers)
        has_next_page = data["pageInfo"]["hasNextPage"]
        cursor = data["pageInfo"]["endCursor"]

        # Update the star count text
        star_count_text.text(f"Current count of stars: {len(stargazers)}")

    return stargazers




def count_stars_by_date(star_dates, days_ago):
    star_counts = []
    index = 0
    count = 0
    for day in days_ago:
        while index < len(star_dates) and star_dates[index].date() < day:
            count += 1
            index += 1
        star_counts.append(count)
    return star_counts

repos_to_fetch_input = st.text_area("Enter repository names (comma-separated, e.g., 'owner/repo'):")
repos_to_fetch = [repo.strip() for repo in repos_to_fetch_input.split(",") if "/" in repo]

if repos_to_fetch_input and not repos_to_fetch:
    st.error("Please enter repositories in the correct format: 'owner/repo'.")

repo_star_data = {}
today = datetime.now()

for repo in repos_to_fetch:
    owner, name = repo.split("/")
    csv_file_name = os.path.join(csv_dir, f"{owner}_{name}_stars.csv")
    star_dates = []
    if os.path.isfile(csv_file_name):
        with open(csv_file_name, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            star_dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in reader]
    last_fetched_date = star_dates[-1] if star_dates else None
    if last_fetched_date is None or last_fetched_date.date() < today.date():
        new_stargazers = fetch_stargazers(owner, name, last_fetched_date)
        new_star_dates = [datetime.strptime(star["starredAt"], "%Y-%m-%dT%H:%M:%SZ") for star in new_stargazers]
        star_dates.extend(new_star_dates)
        # Check if the directory exists; if not, create it
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        with open(csv_file_name, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for star_date in star_dates:
                writer.writerow([star_date.strftime("%Y-%m-%d")])
    repo_star_data[repo] = star_dates

days_ago = [(today - timedelta(days=i)).date() for i in range(3600, -1, -1)]
fig, ax = plt.subplots(figsize=(12, 6))

for repo, star_dates in repo_star_data.items():
    star_counts = count_stars_by_date(star_dates, days_ago)
    ax.plot(days_ago, star_counts, label=repo)

ax.set_xlabel("Date")
ax.set_ylabel("Number of Stars")
ax.set_title("GitHub Stars Over Time for Different Repositories")
ax.legend()
# Concatenate all the repository names together
repo_names = "_".join([repo.replace("/", "_") for repo in repos_to_fetch])

# Save the plot as .png and .svg files
png_file_name = os.path.join(csv_dir, f"{repo_names}_github_stars.png")
svg_file_name = os.path.join(csv_dir, f"{repo_names}_github_stars.svg")
fig.savefig(png_file_name)
fig.savefig(svg_file_name)

# Display the plot
st.pyplot(fig)

# Create download links for the .png and .svg files
with open(png_file_name, "rb") as f:
    bytes = f.read()
    st.download_button(
        label=f"Download {repo_names} plot as .png",
        data=bytes,
        file_name=f"{repo_names}_github_stars.png",
        mime="image/png",
    )

with open(svg_file_name, "rb") as f:
    bytes = f.read()
    st.download_button(
        label=f"Download {repo_names} plot as .svg",
        data=bytes,
        file_name=f"{repo_names}_github_stars.svg",
        mime="image/svg+xml",
    )
