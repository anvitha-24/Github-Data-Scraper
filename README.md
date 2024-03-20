# GitHub Data Scraper

This Python script allows you to collect and analyze data from GitHub repositories and users. It leverages the GitHub API and web scraping techniques to gather information such as pull requests, user profiles, and repository details.

## Features

- Collect data for a specific repository
- Show all collected repositories
- Show all pull requests from a certain repository
- Show the summary of a repository
- Calculate correlation for pull requests data
- Create and store visual representation data for repositories
- Calculate correlation for user data

## Usage

1. Clone this repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Run the `main.py` script using Python.

## How it works

The script interacts with the GitHub API to fetch repository information and uses web scraping techniques to pull user profile data from the GitHub website.

### GitHubUser Class

The `GitHubUser` class represents a user on GitHub. It has attributes such as `username`, `pull_requests_count`, `repositories_count`, `followers_count`, `following_count`, and `contributions_last_year`. The `scrape_user_profile` method is responsible for pulling user data from the GitHub website.

### GitHubRepository Class

The `GitHubRepository` class represents a GitHub repository. It collects information such as `owner`, `repo_name`, `description`, `homepage`, `license`, `forks`, `watchers`, and `date_of_collection`. The `collect_data_for_repository` function collects data for the specified repository.

### Data Analysis

The script provides various data analysis functionalities, including:

- Visual representation of pull request data using line graphs, histograms, scatter plots, and box plots.
- Calculation of correlation matrices for pull requests and user data.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request with any improvements or additional features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
1
