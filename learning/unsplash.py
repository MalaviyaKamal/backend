
import requests

def get_unsplash_image(query):
    unsplash_api_key = "Lv_qjJl5whyQ7SX0mJv7HufPh3dlhuAAReFcb1_dT3g"
    print("unsplah query " ,query)
    url = f"https://api.unsplash.com/search/photos?per_page=1&query={query}&client_id={unsplash_api_key}"
    response = requests.get(url)
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["urls"]["small"]
    else:
        return None
