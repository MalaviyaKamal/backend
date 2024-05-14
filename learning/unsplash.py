
 
 
# import requests

# def get_unsplash_image(query):
#     unsplash_api_key = "Lv_qjJl5whyQ7SX0mJv7HufPh3dlhuAAReFcb1_dT3g"
#     print("unsplah query " ,query)
#     url = f"https://api.unsplash.com/search/photos?per_page=1&query={query}&client_id={unsplash_api_key}"
#     response = requests.get(url)
#     data = response.json()
#     if "results" in data and len(data["results"]) > 0:
#         return data["results"][0]["urls"]["small_s3"]
#     else:
#         return None

import requests

def get_unsplash_image(query):
    unsplash_api_key = "Lv_qjJl5whyQ7SX0mJv7HufPh3dlhuAAReFcb1_dT3g"
    url = f"https://api.unsplash.com/search/photos?per_page=1&query={query}&client_id={unsplash_api_key}"
    response = requests.get(url)
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["urls"]["small"]
    else:
        return None

# {
 
#  "output_units"[
#   {
#     "title": "unit 1: calulate",
#     "chapters": [
#       {
#         "youtube_search_param": "introduction to calculate",
#         "chapter_title": "chapter 1: what is calulate?"
#       },
#       {
#         "youtube_search_param": "the history of calculate",
#         "chapter_title": "chapter 2: history of calculate"
#       },
#       {
#         "youtube_search_param": "why learn calculate",
#         "chapter_title": "chapter 3: why Learn calculus"
#       }
#     ]
#   },
#   {
#     "title": "unit 2: differentiation",
#     "chapters": [
#       {
#         "youtube_search_param": "differentiationn basic",
#         "chapter_title": "chapter 1: basic of differentiation?"
#       },
#       {
#         "youtube_search_param": "Derivative rules",
#         "chapter_title": "chapter 2:Derivative Rules"
#       },
#       {
#         "youtube_search_param": "Application of derivations",
#         "chapter_title": "chapter 3: Application of derivations"
#       }
#     ]
#   },
#   {
#     "title": "unit 3:integration",
#     "chapters": [
#       {
#         "youtube_search_param": "algebra basic",
#         "chapter_title": "chapter 1: basic of ?"
#       },
#       {
#         "youtube_search_param": "algebra rules",
#         "chapter_title": "chapter 2:algebra Rules"
#       },
#       {
#         "youtube_search_param": "Application of algebra and methods",
#         "chapter_title": "chapter 3: Application of algebra and methods"
#       }
#     ]
#   }
# ],
#  "imageSearchTerm":{
#      "image_search_term":"calculus"
#  },
#  "course_image":"https://s3.ui-west-2.amazonaws.com/image.unsplash.com/small/"
# }
# {"course_id":"50"}