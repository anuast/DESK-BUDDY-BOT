from pydub import AudioSegment
import os

def convert_whatsapp_audio(input_filename, output_filename):
    print(f"[Engine] Searching for raw WhatsApp media: '{input_filename}'...")
    
    if os.path.exists(input_filename):
        # 1. Parse the complex .opus/.ogg binary stream via FFmpeg backend
        sound = AudioSegment.from_file(input_filename)
        
        # 2. Re-encode the audio properties natively into a standard 128kbps MP3
        sound.export(output_filename, format="mp3", bitrate="128k")
        print(f" Success! Your WhatsApp voice clip is now active at: '{output_filename}'")
    else:
        print(f" Error: Could not find '{input_filename}' inside this directory.")

if __name__ == "__main__":
    # Change 'voice_message.opus' to match whatever your downloaded WhatsApp file is named!
    convert_whatsapp_audio("whatsapp_audio.ogg", "yell_procrastination.mp3")
