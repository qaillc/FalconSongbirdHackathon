import os
import random
import base64

def select_audio_file():
    audio_files = ["start1.mp3", "start2.mp3", "start3.mp3"]
    selected_audio = random.choice(audio_files)
    audio_file_path = os.path.join("audios", selected_audio)
    return audio_file_path

def get_audio_html(audio_data_url):
    audio_html = f"""
    <audio id="start-audio" autoplay>
        <source src="{audio_data_url}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    <script>
        document.getElementById('start-audio').play();
    </script>
    """
    return audio_html

def play_audio():
    audio_file_path = select_audio_file()
    audio_bytes = open(audio_file_path, "rb").read()
    audio_data_url = f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}"
    audio_html = get_audio_html(audio_data_url)
    return audio_html
