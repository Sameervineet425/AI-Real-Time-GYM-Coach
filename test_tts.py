from services.coaching.tts import TextToSpeech

tts = TextToSpeech()

print("Testing AI Coach Voice...")

audio = tts.speak("Hello! Welcome to your AI Gym Coach.")

if audio:
    with open("test_voice.mp3", "wb") as f:
        f.write(audio)

    print("Audio generated successfully!")
    print("File saved as test_voice.mp3")
else:
    print("Audio generation failed!")