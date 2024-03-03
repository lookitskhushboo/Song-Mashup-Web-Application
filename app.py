# app.py

import os
from flask import Flask, request, jsonify, render_template

from pytube import YouTube
from pytube import Search
from moviepy.editor import VideoFileClip, concatenate_audioclips, AudioFileClip
from youtube_search import YoutubeSearch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_videos(singer_name, num):
    results = YoutubeSearch(f"{singer_name} songs", max_results=num).to_dict()
    create_directory('videos')
    for i in range(num):
        url = "https://www.youtube.com" + results[i]['url_suffix']
        try:
            yt = YouTube(url)
            video = yt.streams.filter(only_audio=True).first()
            video.download(output_path='videos', filename=f'video_{i}.mp4')
        except Exception as e:
            print(f"Error downloading video: {e}")

def convert_to_audio(num):
    create_directory('audios')
    for i in range(num):
        try:
            audio_path = f'audios/audio_{i}.mp3'
            video_path = f'videos/video_{i}.mp4'
            video_clip = AudioFileClip(video_path)
            video_clip.write_audiofile(audio_path)
            video_clip.close()
        except Exception as e:
            print(f"Error converting video to audio: {e}")

def cut_audio(duration, num):
    
    cut_files = []
    for i in range(num):
        try:
            audio_path = f'audios/audio_{i}.mp3'
            audio_clip = AudioFileClip(audio_path)
            if duration > audio_clip.duration:
                print(f"Error cutting audio: Duration exceeds actual duration of the audio clip")
                continue
            cut_clip = audio_clip.subclip(0, duration)
            cut_file = audio_path.replace(".mp3", "-cut.mp3")
            cut_clip.write_audiofile(cut_file)
            cut_files.append(cut_file)
        except Exception as e:
            print(f"Error cutting audio: {e}")

    return cut_files

def merge_audios(audio_files, output_file):
    if not audio_files:
        print("No audio files to merge.")
        return

    try:
        audio_clips = [AudioFileClip(file) for file in audio_files]
        final_clip = concatenate_audioclips(audio_clips)
        final_clip.write_audiofile(output_file)
        print(f"Merged audios saved as {output_file}")
    except Exception as e:
        print(f"Error merging audios: {e}")

def send_email(email, output_file):
    from_email = 'khushboogupta1103@gmail.com'  # Your Gmail address
    from_password = 'ctct nnzv nnzn japu'  # Your Gmail password

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = email
    msg['Subject'] = 'Mashup Result'

    with open(output_file, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{output_file}"')
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    server.sendmail(from_email, email, msg.as_string())
    server.quit()

@app.route('/', methods=['GET', 'POST'])
def mashup():
    message = None
    if request.method == 'POST':
        singer_name = request.form['singerName']
        num = int(request.form['numVideos'])
        audio_duration = int(request.form['audioDuration'])
        email = request.form['email']
        if num <= 10:
            message = "Number of videos should be greater than 10."
            return render_template('index.html', message=message)
        elif audio_duration<=20:
            message = "Duration of audio shoud be greater than 20."
            return render_template('index.html', message=message)
        else:
            download_videos(singer_name, num)
            convert_to_audio(num)
            cut_files = cut_audio(audio_duration, num)
            merge_audios(cut_files, "merged_audio.mp3")
            send_email(email, "merged_audio.mp3")

            message = 'Result sent to your email.'

    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
