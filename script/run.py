import json
import os
import re
from pathlib import Path
from typing import List

import requests
from omegaconf import DictConfig, OmegaConf

image_suffixs = [
    ".png",
    ".jpg",
]


def parseUrl(
    repo: str,
    branch: str,
    regex: str,
) -> List[str]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    path_list = []

    try:
        print(f"parseUrl: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}")
        data = response.json()["tree"]

        for item in data:
            for suffix in image_suffixs:
                if item["path"].endswith(suffix):
                    path_list.append(item["path"])
    except Exception as e:
        print(f"parseUrl error: {e}")

    icons = []
    for p in path_list:
        if not re.match(regex, p):
            continue

        icons.append(
            {
                "name": Path(p).stem,  # 删除后缀
                "url": f"https://raw.githubusercontent.com/{repo}/{branch}/{p}",
            }
        )
    return icons


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config: DictConfig = OmegaConf.load(os.path.join(project_root, "config.yml"))
    targets = config.get("targets", [])
    for target in targets:
        if not target.get("name"):
            print("name is empty")
            continue
        icons = parseUrl(
            repo=target.get("repo"),
            branch=target.get("branch", "main"),
            regex=target.get("regex", ".*"),
        )
        if len(icons) == 0:
            continue
        name = target.get("name")
        filepath = os.path.join(
            project_root, "json", f'{target.get("filename", name)}.json'
        )
        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as f:
            result = {
                "name": name,
                "description": target.get("description", ""),
                "icons": icons,
            }
            json.dump(result, f, indent=2)
