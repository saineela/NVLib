import pygame  # For handling audio playback
import asyncio  # For asynchronous operations
import edge_tts  # For text-to-speech functionality
import os  # For file handling

# Asynchronous function to convert text to an audio file
async def _text_to_audio_file(text) -> None:
    # Define the path for speech file inside NVLib/TTS-Data folder
    nvlib_folder = "NVLib"
    ttse_folder = os.path.join(nvlib_folder, "TTS-Data")
    
    # Ensure the directory exists
    os.makedirs(ttse_folder, exist_ok=True)
    
    file_path = os.path.join(ttse_folder, "speech.mp3")  # Define speech file path

    if os.path.exists(file_path):  # Remove existing file to avoid conflicts
        os.remove(file_path)

    communicate = edge_tts.Communicate(text, "en-CA-LiamNeural", pitch="+5Hz", rate="+13%")
    await communicate.save(file_path)  # Save speech as an MP3 file

# Function to play the generated speech file
def _play_audio():
    pygame.mixer.init()
    pygame.mixer.music.load("NVLib/TTS-Data/speech.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.stop()
    pygame.mixer.quit()

# Function to handle text-to-speech conversion
def say(text):
    try:
        asyncio.run(_text_to_audio_file(text))  # Convert text to speech file
        _play_audio()  # Play the generated speech file
    except Exception as e:
        print(f"Error in say function: {e}")
