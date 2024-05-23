import requests
from googletrans import Translator
from .gpt import model

YOUTUBE_API_KEY='AIzaSyDXQs02952eLTbUBJdu2XAXbO3GqsJGVGI'
from youtube_transcript_api import YouTubeTranscriptApi

def search_youtube(search_query):
    search_query = requests.utils.quote(search_query)
    print("Search Query:", search_query)  # Add this line
    response = requests.get(
        f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&q={search_query}&videoDuration=medium&videoEmbeddable=true&type=video&maxResults=5"
    )
    data = response.json()
    print("YouTube API Response:", data)  # Add this line
    if not data or not data.get('items'):
        print("YouTube search failed")
        return None
    return data['items'][0]['id']['videoId']

def get_transcript(video_id):
    try:
        transcript_arr = YouTubeTranscriptApi.get_transcript(video_id, languages=['en','hi'])
        transcript = " ".join([t['text'] for t in transcript_arr])
        return transcript.replace("\n", "")
    except Exception as e:
        print(f"Error when getting transcript: {e}")
        # Handle the error by returning an empty string or using a cached transcript (if available)
        return ""  # or provide a default transcript if you have one


# def get_questions_from_transcript(transcript, course_title):
#     questions = []
#     for _ in range(5):
#         prompt = f"You are a helpful AI that is able to generate multiple-choice questions and answers. Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. The length of each answer should not be more than 15 words. You are to generate a random hard multiple-choice question about {course_title} with context from the following transcript: {transcript}"
#         response = model.generate_content(prompt)
#         mcq = response._result.candidates[0].content.parts[0].text
#         questions.append({'text': mcq})
#     print("questions:", questions)
#     return {'parts': questions}
# def get_questions_from_transcript(transcript, course_title, num_questions=1):
#     num_questions = max(1, min(num_questions, 5))
#     questions = []

#     for _ in range(num_questions):
#         if transcript.strip():
#             prompt = (f"You are a helpful AI that is able to generate multiple-choice questions and answers. "
#                       f"Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. "
#                       f"The length of each answer should not be more than 15 words. You are to generate a random hard multiple-choice question "
#                       f"about {course_title} with context from the following transcript: {transcript}")

#             response = model.generate_content(prompt)
#             mcq = response._result.candidates[0].content.parts[0].text
#         else:
#             mcq = f"I am sorry, but there is no contextual information provided for me to generate a multiple-choice question about Chapter 10: \"{course_title}\"."

#         questions.append({'text': mcq})

#     print("questions:", questions)
#     return {'parts': questions}
def get_questions_from_transcript(transcript, course_title, num_questions=3):
    num_questions = max(3, min(num_questions, 5))
    questions = []

    if not transcript.strip():
        mcq = f"I am sorry, but there is no contextual information provided for me to generate a multiple-choice question about \"{course_title}\"."
        questions.append({'text': mcq})
        return {'parts': questions}

    for i in range(num_questions):
        prompt = (f"You are a helpful AI capable of generating multiple-choice questions and answers. "
                  f"Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. "
                  f"The length of each answer should not be more than 15 words. Generate a hard multiple-choice question "
                  f"about {course_title} with context from the following transcript: {transcript}")

        try:
            response = model.generate_content(prompt)
            mcq = response._result.candidates[0].content.parts[0].text
            questions.append({'text': mcq})
        except Exception as e:
            print(f"Error generating question {i+1}: {str(e)}")
            mcq = "I am sorry, but I couldn't generate a question at this time."
            questions.append({'text': mcq})

    print("questions:", questions)
    return {'parts': questions}

# def get_questions_from_transcript(transcript, course_title, num_questions=1):
#     # Ensure the number of questions is between 1 and 5
#     num_questions = max(1, min(num_questions, 5))
#     questions = []

#     for _ in range(num_questions):
#         if transcript.strip():
#             prompt = (f"You are a helpful AI that is able to generate multiple-choice questions and answers. "
#                       f"Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. "
#                       f"The length of each answer should not be more than 15 words. You are to generate a random hard multiple-choice question "
#                       f"about {course_title} with context from the following transcript: {transcript}")

#             response = model.generate_content(prompt)
#             mcq = response._result.candidates[0].content.parts[0].text
#         else:
#             mcq = ""

#         if not mcq.strip():
#             prompt = (f"You are a helpful AI that is able to generate multiple-choice questions and answers. "
#                       f"Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. "
#                       f"The length of each answer should not be more than 15 words. You are to generate a random hard multiple-choice question "
#                       f"about {course_title}.")
#             response = model.generate_content(prompt)
#             mcq = response._result.candidates[0].content.parts[0].text

#         if transcript.strip():
#             questions.append({'text': mcq})
#         else:
#             questions.append({'video_id': video_id, 'summary_text': summary_text})

#     print("questions:", questions)
#     return {'parts': questions}


