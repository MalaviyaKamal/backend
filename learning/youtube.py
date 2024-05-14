import requests
from googletrans import Translator
from .gpt import model

YOUTUBE_API_KEY='AIzaSyAB-cybbXpBtEMOMnUCCwNu3LRp5h1POB4'
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
        print("youtube file in video_id",video_id)
        transcript_arr = YouTubeTranscriptApi.get_transcript(video_id,languages=['en'])
        transcript = " ".join([t['text'] for t in transcript_arr])
        print(transcript)
        return transcript.replace("\n", "")
    
    except Exception as e:
        return ""

def get_questions_from_transcript(transcript, course_title):
    questions = []
    for _ in range(5):
        prompt = f"You are a helpful AI that is able to generate multiple-choice questions and answers. Example question format: {{'question': 'What is 2+2?', 'answer': '4', 'option1': '3', 'option2': '5', 'option3': '6'}}. The length of each answer should not be more than 15 words. You are to generate a random hard multiple-choice question about {course_title} with context from the following transcript: {transcript}"
        response = model.generate_content(prompt)
        mcq = response._result.candidates[0].content.parts[0].text
        questions.append({'text': mcq})
    print("questions:", questions)
    return {'parts': questions}