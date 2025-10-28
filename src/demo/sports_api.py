import os
import requests
import datetime


def get_team_id(team_name):
    api_key = os.getenv("SPORTS_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing environment variable: SPORTS_API_KEY")

    url = "https://v3.football.api-sports.io/teams"
    headers = {"x-apisports-key": api_key}
    params = {"search": team_name}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("response"):
        return data["response"][0]["team"]["id"]
    raise ValueError(f"Team '{team_name}' not found.")


def get_sports_schedule(team_name, date=None, season=None):
    api_key = os.getenv("SPORTS_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing environment variable: SPORTS_API_KEY")

    team_id = get_team_id(team_name)
    if date is None:
        date = datetime.date.today().isoformat()
    if season is None:
        year = datetime.date.fromisoformat(date).year
        season = str(year)

    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": api_key}
    params = {
        "team": team_id,
        "date": date,
        "season": season
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


# Example
if __name__ == "__main__":
    schedule = get_sports_schedule("Flamengo", "2022-10-23")
    print(schedule)
