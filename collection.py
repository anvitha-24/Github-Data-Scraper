import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


users = []


class GitHubRepository:
    def __init__(
        self,
        owner,
        name,
        description,
        homepage,
        license,
        forks,
        watchers,
        date_of_collection=None,
    ):
        self.owner = owner
        self.name = name
        self.description = description
        self.homepage = homepage
        self.license = license
        self.forks = forks
        self.watchers = watchers
        self.date_of_collection = (
            datetime.strptime(date_of_collection, "%Y-%m-%d %H:%M:%S")
            if date_of_collection
            else datetime.now()
        )

        self.pull_requests = []

    def fetch_pull_requests(self):
        # GitHub API endpoint for pull requests
        api_url = f"https://api.github.com/repos/{self.owner}/{self.name}/pulls"

        # Make a GET request to the GitHub API with headers
        response = requests.get(api_url)

        if response.status_code == 200:
            # Parse the JSON response
            pull_requests_data = response.json()

            # Create GitHubPullRequest objects and add them to the list
            for pr_data in pull_requests_data:
                pr = GitHubPullRequest(pr_data)
                self.pull_requests.append(pr)
        else:
            print(
                f"Error: Unable to fetch pull requests. Status code: {response.status_code}"
            )

    def get_summary(self):
        if not self.pull_requests:
            return "No pull requests available for summary."

        oldest_pr_date = min(
            pr.created_at for pr in self.pull_requests if pr.created_at
        )
        open_prs = sum(1 for pr in self.pull_requests if pr.state == "open")
        closed_prs = sum(1 for pr in self.pull_requests if pr.state == "closed")
        unique_users = len(set(pr.user for pr in self.pull_requests))

        summary = (
            f"Summary for {self.owner}/{self.name}:\n"
            f"Number of open pull requests: {open_prs}\n"
            f"Number of closed pull requests: {closed_prs}\n"
            f"Number of unique users: {unique_users}\n"
            f"Date of the oldest pull request: {oldest_pr_date}\n"
        )
        return summary

    def to_csv(self):
        return f"{self.owner},{self.name},{self.description},{self.homepage},{self.license},{self.forks},{self.watchers},{self.date_of_collection}"


class GitHubPullRequest:
    def __init__(self, data):
        self.title = data.get("title", "")
        self.number = data.get("number", 0)
        self.body = data.get("body", "")
        self.state = data.get("state", "")
        self.created_at = data.get("created_at", "")
        self.closed_at = data.get("closed_at", "")
        self.user = data.get("user", {}).get("login", "")
        self.commits = 0
        self.additions = 0
        self.deletions = 0
        self.changed_files = 0
        self.repo_name = data.get("base", {}).get("repo", {}).get("full_name", "")
        self.authors = {}

    def fetch_pull_request_details(self):
        api_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.number}"

        # Make a GET request to the GitHub API
        response = requests.get(api_url)

        if response.status_code == 200:
            # Parse the JSON response
            pr_details = response.json()

            # Extract relevant information
            self.commits = pr_details.get("commits", 0)
            self.additions = pr_details.get("additions", 0)
            self.deletions = pr_details.get("deletions", 0)
            self.changed_files = pr_details.get("changed_files", 0)
        else:
            print(
                f"Error: Unable to fetch pull request details. Status code: {response.status_code}"
            )

    def update_author_stats(self, username):
        if username not in self.authors:
            self.authors[username] = 1
        else:
            self.authors[username] += 1

    def to_csv(self):
        return (
            f"{self.repo_name},{self.title},{self.number},{self.body},{self.state},"
            f"{self.created_at},{self.closed_at},{self.user},{self.commits},"
            f"{self.additions},{self.deletions},{self.changed_files}"
        )


class GitHubUser:
    def __init__(self, username):
        self.username = username
        self.pull_requests_count = 0
        self.repositories_count = 0
        self.followers_count = 0
        self.following_count = 0
        self.contributions_last_year = 0

    def scrape_user_profile(self):
        profile_url = f"https://github.com/{self.username}"

        # Make a GET request to the user profile page
        response = requests.get(profile_url)

        if response.status_code == 200:
            # Use BeautifulSoup to parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract relevant information from the user profile
            try:
                # Extracting the contributions in the last year from the user profile
                contributions_last_year_tag = soup.find(
                    "div", class_="js-yearly-contributions"
                )
                self.contributions_last_year = int(
                    contributions_last_year_tag["data-count"]
                )
            except (TypeError, KeyError, ValueError):
                print("Error: Unable to fetch contributions_last_year.")
                self.contributions_last_year = 0

            try:
                # Extracting the followers count from the user profile
                followers_tag = soup.find("a", class_="Link--secondary")
                self.followers_count = int(followers_tag.span.get_text(strip=True))
            except (TypeError, ValueError):
                print("Error: Unable to fetch followers count.")
                self.followers_count = 0

            try:
                # Extracting the following count from the user profile
                following_tag = soup.find_all("a", class_="Link--secondary")[1]
                self.following_count = int(following_tag.span.get_text(strip=True))
            except (TypeError, ValueError):
                print("Error: Unable to fetch following count.")
                self.following_count = 0
        else:
            print(
                f"Error: Unable to fetch user profile. Status code: {response.status_code}"
            )

    def to_csv(self):
        return (
            f"{self.username},{self.pull_requests_count},{self.repositories_count},"
            f"{self.followers_count},{self.following_count},{self.contributions_last_year}"
        )


def save_as_csv(file_name, obj):
    file_exists = os.path.isfile(file_name)

    with open(file_name, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        if not file_exists:
            header = obj.to_csv().split(",")
            writer.writerow(header)

        data = obj.to_csv().split(",")
        writer.writerow(data)


def collect_data_for_repository(owner, repo_name, users, date_of_collection=None):
    # Capture the current date and time if not provided
    date_of_collection = date_of_collection or datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # GitHub API endpoint for repository information
    repo_info_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    repo_info_response = requests.get(repo_info_url)

    if repo_info_response.status_code == 200:
        # Parse the JSON response for repository information
        repo_info_data = repo_info_response.json()

        # Extract additional information
        description = repo_info_data.get("description", "")
        homepage = repo_info_data.get("homepage", "")

        # Check if "license" key exists
        if "license" in repo_info_data and repo_info_data["license"] is not None:
            license = repo_info_data["license"].get("name", "")
        else:
            license = "No License"  # Set a default value or handle it accordingly

        forks = repo_info_data.get("forks", 0)
        watchers = repo_info_data.get("watchers", 0)

        # Collect data for the specified repository
        repo = GitHubRepository(
            owner,
            repo_name,
            description,
            homepage,
            license,
            forks,
            watchers,
            date_of_collection=date_of_collection,
        )
        repo.fetch_pull_requests()

        for pr in repo.pull_requests:
            pr.fetch_pull_request_details()

            for author in pr.authors:
                username = author
                user = next((u for u in users if u.username == username), None)

                if not user:
                    user = GitHubUser(username)
                    users.append(user)

                user.get_user_data()
                user.pull_requests_count += pr.authors[author]

                if (
                    isinstance(user.following_count, (int, float))
                    and isinstance(user.followers_count, (int, float))
                    and isinstance(user.pull_requests_count, (int, float))
                    and isinstance(user.contributions_last_year, (int, float))
                ):
                    print(
                        f"User: {user.username}, Following: {user.following_count}, "
                        f"Followers: {user.followers_count}, "
                        f"PullRequests: {user.pull_requests_count}, "
                        f"ContributionsLastYear: {user.contributions_last_year}"
                    )

                    save_as_csv("users.csv", user)

                    time.sleep(1)

        save_as_csv("repositories.csv", repo)

        # Print additional details
        print(f"\nDetails for {repo.owner}/{repo.name}:")
        print(f"Description: {description}")
        print(f"Homepage: {homepage}")
        print(f"License: {license}")
        print(f"Forks: {forks}")
        print(f"Watchers: {watchers}")
        print(f"Data collection date: {date_of_collection}")

        print("\nData collection complete.")

        return repo

    else:
        print(
            f"Error: Unable to fetch repository information. Status code: {repo_info_response.status_code}"
        )
        return None


def create_and_store_visual_representation_data(repositories):
    # Line graph: Total number of pull requests per day
    pull_requests_data = {
        "Date": [],
        "Number": [],
        "State": [],
        "Changed Files": [],
        "Commits": [],
    }

    for repo in repositories:
        for pr in repo.pull_requests:
            pull_requests_data["Date"].append(pr.created_at)
            pull_requests_data["Number"].append(pr.number)
            pull_requests_data["State"].append(pr.state)
            pull_requests_data["Changed Files"].append(pr.changed_files)

            # Add "Commits" information if available
            if pr.commits is not None:
                pull_requests_data["Commits"].append(pr.commits)
            else:
                pull_requests_data["Commits"].append(
                    0
                )  # You can replace 0 with another appropriate default value

    if not pull_requests_data["Number"]:
        print("No pull request information found. Exiting.")
        return

    pull_requests_df = pd.DataFrame(pull_requests_data)
    pull_requests_df["Date"] = pd.to_datetime(pull_requests_df["Date"])

    plt.figure(figsize=(10, 6))
    for state in pull_requests_df["State"].unique():
        state_df = pull_requests_df[pull_requests_df["State"] == state]
        plt.plot(
            state_df["Date"], state_df["Number"], marker="o", linestyle="-", label=state
        )

    plt.title("Total Number of Pull Requests Over Time, Separated by State")
    plt.xlabel("Date")
    plt.ylabel("Number of Pull Requests")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()
    # Line graph: Number of open and closed pull requests per day
    open_vs_closed_pull_requests_per_day = pull_requests_df.groupby(
        [pull_requests_df["Date"].dt.date]
    )["Number"].count()

    plt.figure(figsize=(10, 6))
    open_vs_closed_pull_requests_per_day.plot(kind="line")
    plt.title("Number of Open and Closed Pull Requests per Day")
    plt.xlabel("Date")
    plt.ylabel("Number of Pull Requests")
    plt.legend(title="State")
    plt.show()

    pull_request_states = pull_requests_df["State"].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(
        pull_request_states,
        labels=pull_request_states.index,
        autopct="%1.1f%%",
        startangle=90,
    )
    plt.title("Distribution of Pull Request States")
    plt.show()

    # Histogram: Distribution of pull request sizes (number of changes)
    plt.figure(figsize=(10, 6))
    plt.hist(
        pull_requests_df["Changed Files"], bins=20, color="skyblue", edgecolor="black"
    )
    plt.title("Distribution of Pull Request Sizes")
    plt.xlabel("Number of Changed Files")
    plt.ylabel("Frequency")
    plt.show()

    # Scatter plot: Pull request size vs. number of commits
    plt.figure(figsize=(10, 6))
    plt.scatter(
        pull_requests_df["Changed Files"], pull_requests_df["Commits"], color="orange"
    )
    plt.title("Pull Request Size vs. Number of Commits")
    plt.xlabel("Number of Changed Files")
    plt.ylabel("Number of Commits")
    plt.show()

    # Box plot: Pull request size distribution by state
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="State", y="Changed Files", data=pull_requests_df, palette="viridis")
    plt.title("Pull Request Size Distribution by State")
    plt.xlabel("State")
    plt.ylabel("Number of Changed Files")
    plt.show()

    # Bar plot: Number of users per repository
    users_per_repository = pd.DataFrame(
        {
            "Repository": [
                pr.repo_name for repo in repositories for pr in repo.pull_requests
            ],
            "User": [pr.user for repo in repositories for pr in repo.pull_requests],
        }
    )
    users_per_repository = (
        users_per_repository.drop_duplicates().groupby("Repository")["User"].count()
    )

    plt.figure(figsize=(10, 6))
    users_per_repository.plot(kind="bar")
    plt.title("Number of Users per Repository")
    plt.xlabel("Repository")
    plt.ylabel("Number of Users")
    plt.show()


def show_pull_requests(repositories):
    print("Choose a repository:")
    for i, repo in enumerate(repositories, 1):
        print(f"{i}. {repo.owner}/{repo.name}")

    repo_index = None
    while repo_index is None:
        try:
            repo_index = int(input("Enter the index of the repository: ")) - 1
            if not (0 <= repo_index < len(repositories)):
                raise ValueError("Invalid index. Please enter a valid index.")
        except ValueError as e:
            print(f"Error: {e}")

    repo = repositories[repo_index]

    # Show only the first 5 pull requests for the selected repository
    num_pull_requests_to_show = min(5, len(repo.pull_requests))
    for i, pr in enumerate(repo.pull_requests[:num_pull_requests_to_show], 1):
        print(f"\nPull Request {i} details:")
        print(f"Title: {pr.title}")
        print(f"Number: {pr.number}")
        print(f"Body: {pr.body}")
        print(f"State: {pr.state}")
        print(f"Created At: {pr.created_at}")
        print(f"Closed At: {pr.closed_at}")
        print(f"User: {pr.user}")
        print(f"Commits: {pr.commits}")
        print(f"Additions: {pr.additions}")
        print(f"Deletions: {pr.deletions}")
        print(f"Changed Files: {pr.changed_files}")
        print(f"Repository Name: {pr.repo_name}")
        print(f"Authors: {pr.authors}")

    see_all = input("Do you want to see all pull requests? (yes/no): ").lower()
    if see_all == "yes":
        for i, pr in enumerate(
            repo.pull_requests[num_pull_requests_to_show:],
            num_pull_requests_to_show + 1,
        ):
            print(f"\nPull Request {i} details:")
            print(f"Title: {pr.title}")
            print(f"Number: {pr.number}")
            print(f"Body: {pr.body}")
            print(f"State: {pr.state}")
            print(f"Created At: {pr.created_at}")
            print(f"Closed At: {pr.closed_at}")
            print(f"User: {pr.user}")
            print(f"Commits: {pr.commits}")
            print(f"Additions: {pr.additions}")
            print(f"Deletions: {pr.deletions}")
            print(f"Changed Files: {pr.changed_files}")
            print(f"Repository Name: {pr.repo_name}")
            print(f"Authors: {pr.authors}")


def show_menu():
    print("1. Collect data for a specific repository")
    print("2. Show all collected repositories")
    print("3. Show all pull requests from a certain repository")
    print("4. Show the summary of a repository")
    print("5. Calculate correlation for pull requests data")
    print("6. Create and store visual representation data for repositories")
    print("7. Calculate correlation for user data")
    print("8. Quit")


def show_repository_submenu(repo):
    print(f"Submenu for {repo.owner}/{repo.name}:")
    print("1. Show pull requests")
    print("2. Show summary")
    print("3. Back to main menu")


def main():
    repositories = []
    users = []

    while True:
        show_menu()
        choice = input("Enter your choice: ")

        if choice == "1":
            while True:
                owner = input("Enter the owner of the repository: ")
                repo_name = input("Enter the name of the repository: ")

                # Collect data for the specified repository
                repo = collect_data_for_repository(owner, repo_name, users)
                if repo is not None:  # Check if the repository is not None
                    repositories.append(repo)
                    print("Data collection complete.")

                more_repositories = input(
                    "Do you want to enter more repositories? (yes/no): "
                ).lower()
                if more_repositories != "yes":
                    break

        elif choice == "2":
            print("All collected repositories:")
            for i, repo in enumerate(repositories, 1):
                if repo is not None:
                    print(f"{i}. {repo.owner}/{repo.name}")
            while True:
                try:
                    repo_index = int(input("Enter the index of the repository: ")) - 1
                    if 0 <= repo_index < len(repositories):
                        break
                    else:
                        print("Invalid index. Please enter a valid index.")
                except ValueError:
                    print("Invalid input. Please enter a valid index.")

            repo_submenu_choice = None
            while repo_submenu_choice != "3":
                show_repository_submenu(repositories[repo_index])
                repo_submenu_choice = input("Enter your choice: ")

                if repo_submenu_choice == "1":
                    show_pull_requests(repositories)

                elif repo_submenu_choice == "2":
                    # Show summary for the selected repository
                    summary = repositories[repo_index].get_summary()
                    print(summary)

                elif repo_submenu_choice != "3":
                    print("Invalid choice. Please try again.")

        elif choice == "3":
            show_pull_requests(repositories)

        elif choice == "4":
            repo_index = None
            while repo_index is None:
                try:
                    repo_index = int(input("Enter the index of the repository: ")) - 1
                    if not (0 <= repo_index < len(repositories)):
                        raise ValueError("Invalid index. Please enter a valid index.")
                except ValueError as e:
                    print(f"Error: {e}")

            if 0 <= repo_index < len(repositories):
                # Show summary for the selected repository
                summary = repositories[repo_index].get_summary()
                print(summary)

        elif choice == "5":
            # Calculate correlation for pull requests data
            pull_requests_data = {
                "Title": [],
                "Number": [],
                "Commits": [],
                "Additions": [],
                "Deletions": [],
                "Changed Files": [],
            }

            for repo in repositories:
                for pr in repo.pull_requests:
                    pull_requests_data["Title"].append(pr.title)
                    pull_requests_data["Number"].append(pr.number)
                    pull_requests_data["Commits"].append(pr.commits)
                    pull_requests_data["Additions"].append(pr.additions)
                    pull_requests_data["Deletions"].append(pr.deletions)
                    pull_requests_data["Changed Files"].append(pr.changed_files)

            pull_requests_df = pd.DataFrame(pull_requests_data)
            correlation_matrix = pull_requests_df.corr()
            print("Correlation matrix for pull requests data:")
            print(correlation_matrix)

        elif choice == "6":
            create_and_store_visual_representation_data(repositories)

        elif choice == "7":
            # Calculate correlation for user data
            users_data = {
                "Following": [],
                "Followers": [],
                "PullRequests": [],
                "ContributionsLastYear": [],
            }

            for user in users:
                print(
                    f"User: {user.username}, Following: {user.following_count}, "
                    f"Followers: {user.followers_count}, "
                    f"PullRequests: {user.pull_requests_count}, "
                    f"ContributionsLastYear: {user.contributions_last_year}"
                )
                if (
                    isinstance(user.following_count, (int, float))
                    and isinstance(user.followers_count, (int, float))
                    and isinstance(user.pull_requests_count, (int, float))
                    and isinstance(user.contributions_last_year, (int, float))
                ):
                    users_data["Following"].append(user.following_count)
                    users_data["Followers"].append(user.followers_count)
                    users_data["PullRequests"].append(user.pull_requests_count)
                    users_data["ContributionsLastYear"].append(
                        user.contributions_last_year
                    )

            users_df = pd.DataFrame(users_data)
            users_df = users_df.dropna().astype(float)

            correlation_matrix_users = users_df.corr()

            print("Correlation matrix for user data:")
            print(correlation_matrix_users)

        elif choice == "8":
            print("Exiting the program.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
