import speech_recognition as sr
import subprocess
import os

def listen_to_user():
    # 1. Initialize the microphone and recognition framework
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient background room noise automatically
    print(" [Desk Buddy Bot]: Calibrating microphone for background noise...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
    print("\n [Desk Buddy Bot]: I am listening! Just speak to me...")
    print(" (Say phrases containing words like 'procrastinate', 'lazy', or 'quote')\n")

    while True:
        try:
            with microphone as source:
                print("Listening... ")
                # Capture ambient speech waveforms, timing out if silent
                audio_data = recognizer.listen(source, phrase_time_limit=5)
                
            print("Processing voice input... ")
            # Convert raw audio waveforms into a text string using local web-speech hooks
            user_speech = recognizer.recognize_google(audio_data).lower()
            print(f"You said: \"{user_speech}\"")

            # 2. Intent-Matching Routing Protocol
            if "procrastinat" in user_speech or "slack" in user_speech or "lazy" in user_speech:
                print(" Intent: Procrastination Caught!")
                selected_audio = "yell_procrastination.mp3"
                
            elif "quote" in user_speech or "motivation" in user_speech or "inspire" in user_speech:
                print(" Intent: Motivation Request.")
                selected_audio = "quote_motivation.mp3"
                
            elif "exit" in user_speech or "stop" in user_speech:
                print("Shutting down voice tracking.")
                break
                
            else:
                print(" Intent: Unrecognized General Query.")
                selected_audio = "generic_response.mp3"

            # 3. Trigger C++ Multimedia Layer
            executable = "./worker.exe" if os.name == 'nt' else "./worker"
            if os.path.exists(selected_audio):
                subprocess.run([executable, selected_audio])
            else:
                print(f" Asset Error: Missing file '{selected_audio}'")
                
            print("-" * 50)

        except sr.UnknownValueError:
            # Caught if you make noise but don't say actual words
            print(" [Bot]: Sorry, I didn't catch any spoken words. Try again.")
            print("-" * 50)
        except sr.RequestError:
            print(" System Error: Speech service unreachable.")
            break
        except KeyboardInterrupt:
            print("\nVoice monitoring stopped.")
            break

if __name__ == "__main__":
    listen_to_user()
