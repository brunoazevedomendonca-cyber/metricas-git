import requests
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

class GitHubCollector:
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"token {token}"}
        self.base_url = "https://api.github.com"
    
    def get_commits(self, owner: str, repo: str, since: str) -> List[Dict]:
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"since": since, "per_page": 100}
        
        commits = []
        page = 1
        while True:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if not data:
                break
                
            for commit in data:
                commits.append({
                    "sha": commit["sha"],
                    "author": commit["commit"]["author"]["email"],
                    "date": commit["commit"]["author"]["date"],
                    "message": commit["commit"]["message"],
                    "repo": repo
                })
            page += 1
            
        return commits
    
    def get_pulls(self, owner: str, repo: str, since: str) -> List[Dict]:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": "closed", "per_page": 100}
        
        pulls = []
        page = 1
        while True:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if not data:
                break
                
            for pr in data:
                if pr["merged_at"] and pr["created_at"] >= since:
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    
                    pulls.append({
                        "number": pr["number"],
                        "author": pr["user"]["login"],
                        "created_at": pr["created_at"],
                        "merged_at": pr["merged_at"],
                        "merge_time_hours": (merged - created).total_seconds() / 3600,
                        "repo": repo
                    })
            page += 1
            
        return pulls
    
    def get_releases(self, owner: str, repo: str) -> List[Dict]:
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        response = requests.get(url, headers=self.headers)
        
        releases = []
        for release in response.json():
            releases.append({
                "tag": release["tag_name"],
                "date": release["published_at"],
                "repo": repo
            })
            
        return releases

class DatabaseManager:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                sha TEXT PRIMARY KEY,
                author TEXT,
                date TEXT,
                message TEXT,
                repo TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pulls (
                number INTEGER,
                repo TEXT,
                author TEXT,
                created_at TEXT,
                merged_at TEXT,
                merge_time_hours REAL,
                PRIMARY KEY (number, repo)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                tag TEXT,
                repo TEXT,
                date TEXT,
                PRIMARY KEY (tag, repo)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_commits(self, commits: List[Dict]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for commit in commits:
            cursor.execute("""
                INSERT OR REPLACE INTO commits 
                (sha, author, date, message, repo) 
                VALUES (?, ?, ?, ?, ?)
            """, (commit["sha"], commit["author"], commit["date"], 
                  commit["message"], commit["repo"]))
        
        conn.commit()
        conn.close()
    
    def save_pulls(self, pulls: List[Dict]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pr in pulls:
            cursor.execute("""
                INSERT OR REPLACE INTO pulls 
                (number, repo, author, created_at, merged_at, merge_time_hours) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pr["number"], pr["repo"], pr["author"], 
                  pr["created_at"], pr["merged_at"], pr["merge_time_hours"]))
        
        conn.commit()
        conn.close()
    
    def save_releases(self, releases: List[Dict]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for release in releases:
            cursor.execute("""
                INSERT OR REPLACE INTO releases 
                (tag, repo, date) 
                VALUES (?, ?, ?)
            """, (release["tag"], release["repo"], release["date"]))
        
        conn.commit()
        conn.close()

def collect_data():
    with open("config.json") as f:
        config = json.load(f)
    
    collector = GitHubCollector(config["github_token"])
    db = DatabaseManager()
    
    since = "2024-01-01T00:00:00Z"
    
    for repo_config in config["repositories"]:
        owner = repo_config["owner"]
        repo = repo_config["repo"]
        
        print(f"Coletando dados de {owner}/{repo}...")
        
        commits = collector.get_commits(owner, repo, since)
        pulls = collector.get_pulls(owner, repo, since)
        releases = collector.get_releases(owner, repo)
        
        db.save_commits(commits)
        db.save_pulls(pulls)
        db.save_releases(releases)
        
        print(f"Salvos: {len(commits)} commits, {len(pulls)} PRs, {len(releases)} releases")

if __name__ == "__main__":
    collect_data()
