import google.generativeai as genai
from .models import Unit, Chapter, Course
from .unsplash import get_unsplash_image
from django.contrib.auth import get_user_model

# geminai_api_key = getenv("")
genai.configure(api_key="AIzaSyD_BCQn7CjSfDqqwe-KUQeE5JWgXf0xTpM")
model = genai.GenerativeModel('gemini-pro')

def get_keywords_from_content(content):
    return content.split()

def generate_chapters(title, units, user):
    User = get_user_model()

    try:
        user_instance = User.objects.get(id=user)
    except User.DoesNotExist:
        return {"error": f"User with id '{user}' does not exist."}

    try:
        # course_content = model.generate_content(f"A learning course about {title}")
        # keywords = get_keywords_from_content(course_content.text)
        # image_search_term = ' '.join(keywords)
        # print("image search", image_search_term)
        # course_image = get_unsplash_image(image_search_term)
        # course = Course.objects.create(name=title, image=course_image, user=user_instance)
        # course_id = course.id
        course_image = get_unsplash_image(title)
        if not course_image:
            return {"error": "No image found for the given title."}

        # Create the course with the image and user
        course = Course.objects.create(name=title, image=course_image, user=user_instance)
        course_id = course.id
    except Exception as e:
        return {"error": str(e)}

    response_data = []

    for unit_index, unit_name in enumerate(units, start=1):
        unit, created = Unit.objects.get_or_create(name=unit_name, course=course)
        response = model.generate_content(f"You are an AI capable of curating course content, coming up with relevant chapter titles, and finding relevant YouTube videos for each chapter. Create chapters for the unit {unit_name} of the course {title}, and provide detailed YouTube search queries for informative educational videos for each chapter.")
        
        if hasattr(response, 'text'):
            chapters = []
            chapter_counter = 1
            existing_titles = set()
            
            for chapter_title in response.text.split('\n'):
                cleaned_title = chapter_title.strip().replace("**", "").replace("*", "").replace("Chapter", "").strip()
                cleaned_title = cleaned_title.split(":")[-1].strip()

                if not cleaned_title:
                    continue  # Skip empty or invalid titles

                youtube_search_param = cleaned_title.replace(" ", " ")
                while f"Chapter {chapter_counter}: {cleaned_title}" in existing_titles:
                    chapter_counter += 1

                chapter_instance = Chapter.objects.create(
                    unit=unit,
                    name=f"Chapter {chapter_counter}: {cleaned_title}",
                    youtubeSearchQuery=youtube_search_param
                )

                chapters.append({
                    "id": chapter_instance.id,
                    "name": chapter_instance.name,
                    "youtubeSearchQuery": chapter_instance.youtubeSearchQuery,
                    "videoId": chapter_instance.videoId,
                    "summary": chapter_instance.summary
                })
                existing_titles.add(f"Chapter {chapter_counter}: {cleaned_title}")
                chapter_counter += 1
            
            response_data.append({
                "title": f"Unit {unit_index}: {unit_name}",
                "chapters": chapters
            })
        else:
            response_data.append({
                "title": f"Unit {unit_index}: {unit_name}",
                "chapters": []
            })

    return {"course_id": course_id}






























# import google.generativeai as genai
# from .models import Unit, Chapter, Course
# from .unsplash import get_unsplash_image
# from django.contrib.auth import get_user_model

# genai.configure(api_key="AIzaSyD_BCQn7CjSfDqqwe-KUQeE5JWgXf0xTpM")
# model = genai.GenerativeModel('gemini-pro')

# def get_keywords_from_content(content):
#     return content.split()

# def generate_chapters(title, units, user):
#     User = get_user_model()

#     try:
#         user_instance = User.objects.get(id=user)
#     except User.DoesNotExist:
#         return {"error": f"User with id '{user}' does not exist."}

#     try:
#         course_content = model.generate_content(f"A learning  of  course about {title}")
#         keywords = get_keywords_from_content(course_content.text)
#         image_search_term = ' '.join(keywords)
#         print ("image search",image_search_term)
#         course_image = get_unsplash_image(image_search_term)
#         course = Course.objects.create(name=title, image=course_image, user=user_instance)
#         course_id = course.id
#     except Exception as e:
#         return {"error": str(e)}

#     response_data = []

#     for unit_index, unit_name in enumerate(units, start=1):
#         unit, created = Unit.objects.get_or_create(name=unit_name, course=course)
#         response = model.generate_content(f"You are an AI capable of curating course content, coming up with relevant chapter titles, and finding relevant YouTube videos for each chapter.Create chapters for the unit {unit_name} of the course {title}, and provide detailed YouTube search queries for informative educational videos for each chapter.`")
#         if hasattr(response, 'text'):
#             chapters = []
#             chapter_counter = 1
#             existing_titles = set()
#             for chapter_title in response.text.split('\n'):
#                 if not chapter_title.strip():
#                     continue
#                 cleaned_title = chapter_title.strip().replace("**", "").replace("*", "").replace("Chapter", "").strip()
#                 cleaned_title = cleaned_title.split(":")[-1].strip()
#                 youtube_search_param = cleaned_title.replace(" ", " ")
#                 while f"Chapter {chapter_counter}: {cleaned_title}" in existing_titles:
#                     chapter_counter += 1
#                 chapter_instance = Chapter.objects.create(
#                     unit=unit,
#                     name=f"Chapter {chapter_counter}: {cleaned_title}",
#                     youtubeSearchQuery=youtube_search_param
#                 )
#                 chapters.append({
#                     "id": chapter_instance.id,
#                     "name": chapter_instance.name,
#                     "youtubeSearchQuery": chapter_instance.youtubeSearchQuery,
#                     "videoId": chapter_instance.videoId,
#                     "summary": chapter_instance.summary
#                 })
#                 existing_titles.add(f"Chapter {chapter_counter}: {cleaned_title}")
#                 chapter_counter += 1
#             response_data.append({
#                 "title": f"Unit {unit_index}: {unit_name}",
#                 "chapters": chapters
#             })
#         else:
#             response_data.append({
#                 "title": f"Unit {unit_index}: {unit_name}",
#                 "chapters": []
#             })

#     return {"course_id": course_id}  