#!/usr/bin/env python
import datetime
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from epdlib import Layout, Screen
from humanize import intcomma, naturaldelta

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
FONT_FILE = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

# GitHub API and token
GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


logger = logging.getLogger(__name__)


@dataclass
class Repo:
    name: str
    issue_count: int
    pr_count: int
    star_count: int
    commit_date: datetime.datetime
    commit_hash: str
    commit_message: str
    commit_author: str

    @property
    def commit_timedelta(self):
        return datetime.datetime.now() - self.commit_date


class Nestbox:
    def __init__(self, epd, organization):
        self.organization = organization
        self.screen = Screen(epd=epd)
        self.layout = Layout(
            resolution=self.screen.resolution,
            layout={
                "title": {
                    "type": "TextBlock",
                    "width": 1,
                    "height": 0.2,
                    "padding": 10,
                    "abs_coordinates": (0, 0),
                    "hcenter": True,
                    "vcenter": True,
                    "relative": ["title", "title"],
                    "font": FONT_FILE,
                    "fill": "white",
                    "bkground": "black",
                },
                "stats_padding": {
                    "type": "TextBlock",
                    "text": " ",
                    "width": 1 / 10,
                    "height": 0.15,
                    "abs_coordinates": (0, None),
                    "relative": ["stats_padding", "title"],
                    "font": FONT_FILE,
                },
                "issue_image": {
                    "type": "ImageBlock",
                    "width": 1 / 15,
                    "height": 0.15,
                    "padding": 3,
                    "abs_coordinates": (0, None),
                    "vcenter": True,
                    "relative": ["stats_padding", "title"],
                },
                "issue_count": {
                    "type": "TextBlock",
                    "width": 1 / 5,
                    "height": 0.15,
                    "padding": 2,
                    "abs_coordinates": (None, None),
                    "vcenter": True,
                    "relative": ["issue_image", "title"],
                    "font": FONT_FILE,
                },
                "pr_image": {
                    "type": "ImageBlock",
                    "width": 1 / 15,
                    "height": 0.15,
                    "padding": 5,
                    "abs_coordinates": (None, None),
                    "vcenter": True,
                    "relative": ["issue_count", "title"],
                },
                "pr_count": {
                    "type": "TextBlock",
                    "width": 1 / 5,
                    "height": 0.15,
                    "padding": 5,
                    "abs_coordinates": (None, None),
                    "vcenter": True,
                    "relative": ["pr_image", "title"],
                    "font": FONT_FILE,
                },
                "star_image": {
                    "type": "ImageBlock",
                    "width": 1 / 15,
                    "height": 0.15,
                    "padding": 5,
                    "abs_coordinates": (None, None),
                    "vcenter": True,
                    "relative": ["pr_count", "title"],
                },
                "star_count": {
                    "type": "TextBlock",
                    "width": 1 / 5,
                    "height": 0.15,
                    "padding": 5,
                    "abs_coordinates": (None, None),
                    "vcenter": True,
                    "relative": ["star_image", "title"],
                    "font": FONT_FILE,
                },
                "last_commit": {
                    "type": "TextBlock",
                    "width": 1,
                    "height": 0.15,
                    "padding": 10,
                    "abs_coordinates": (0, None),
                    "vcenter": True,
                    "relative": ["last_commit", "stats_padding"],
                    "font": FONT_FILE,
                },
                "last_commit_message": {
                    "type": "TextBlock",
                    "max_lines": 6,
                    "width": 1,
                    "height": 0.5,
                    "padding": 10,
                    "abs_coordinates": (0, None),
                    "relative": ["last_commit_message", "last_commit"],
                    "font": FONT_FILE,
                },
            },
        )

    def get_github_graphql(self, organization):
        query = """
            query($organization: String!, $numRepos: Int = 100) {
                organization(login: $organization) {
                    repositories(first: $numRepos, privacy: PUBLIC) {
                        edges {
                            node {
                                name
                                issues(states: OPEN) {
                                    totalCount
                                }
                                pullRequests(states: OPEN) {
                                    totalCount
                                }
                                stargazerCount
                                defaultBranchRef {
                                    target {
                                        ... on Commit {
                                            history(first: 1) {
                                                edges {
                                                    node {
                                                        committedDate
                                                        oid
                                                        message
                                                        author {
                                                            user {
                                                                login
                                                            }
                                                            name
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """
        response = requests.post(
            GITHUB_API_URL,
            json={"query": query, "variables": {"organization": organization}},
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_github_data(self, organization, updated_days=30):
        response = self.get_github_graphql(organization=organization)
        updated_cut_off_date = datetime.datetime.now() - datetime.timedelta(days=updated_days)

        repo_list = []

        logger.debug(
            "%d repos in GitHub response",
            len(response["data"]["organization"]["repositories"]["edges"]),
        )

        for repo_edge in response["data"]["organization"]["repositories"]["edges"]:
            repo_node = repo_edge["node"]
            history_edge = repo_node["defaultBranchRef"]["target"]["history"]["edges"][0]
            commit_node = history_edge["node"]

            repo_name = repo_node["name"]
            issue_count = repo_node["issues"]["totalCount"]
            pr_count = repo_node["pullRequests"]["totalCount"]
            star_count = repo_node["stargazerCount"]

            commit_date = datetime.datetime.strptime(
                commit_node["committedDate"], "%Y-%m-%dT%H:%M:%SZ"
            )
            commit_hash = commit_node["oid"][0:7]
            commit_message = commit_node["message"]

            author = commit_node["author"]
            if author["user"]:
                commit_author = "@{}".format(author["user"]["login"])
            else:
                commit_author = author["name"]

            # Skip any repos that haven't been committed to recently
            if commit_date < updated_cut_off_date:
                continue

            repo_list.append(
                Repo(
                    name=repo_name,
                    issue_count=issue_count,
                    pr_count=pr_count,
                    star_count=star_count,
                    commit_date=commit_date,
                    commit_hash=commit_hash,
                    commit_message=commit_message,
                    commit_author=commit_author,
                )
            )

        logger.debug("%d repos with recent commits", len(repo_list))

        return repo_list

    def run(self):
        while True:
            repo_list = self.get_github_data(organization=self.organization)

            for repo in repo_list:
                self.layout.update_contents(
                    {
                        "title": repo.name,
                        "issue_image": (IMAGE_DIR / "issue.png").as_posix(),
                        "issue_count": intcomma(repo.issue_count),
                        "pr_image": (IMAGE_DIR / "pr.png").as_posix(),
                        "pr_count": intcomma(repo.pr_count),
                        "star_image": (IMAGE_DIR / "star.png").as_posix(),
                        "star_count": intcomma(repo.star_count),
                        "last_commit": (
                            f"{repo.commit_hash} - {naturaldelta(repo.commit_timedelta)} ago"
                        ),
                        "last_commit_message": f"{repo.commit_author} - {repo.commit_message}",
                    }
                )

                self.screen.writeEPD(self.layout.concat())
                logger.info("sleeping...")
                time.sleep(60)


if __name__ == "__main__":
    nestbox = Nestbox(epd="epd4in2_V2", organization="wagtail")
    nestbox.run()
