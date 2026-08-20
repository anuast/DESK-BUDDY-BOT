#include <iostream>
#include <string>
#include <cstdlib>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "[C++ Worker] Error: No audio filename received!" << std::endl;
        return 1;
    }

    std::string audio_file = argv[1];

    std::cout << "\n=============================================" << std::endl;
    std::cout << "[C++ HARDWARE CORE]: FORCING DIRECT MP3 OUT" << std::endl;
    std::cout << "Target Asset: " << audio_file << std::endl;
    std::cout << "=============================================\n" << std::endl;

    //  FIX: We add 'Add-Type -AssemblyName PresentationCore' at the beginning 
    // to load the missing framework so Windows understands MediaPlayer!
    std::string command = "powershell -c \"Add-Type -AssemblyName PresentationCore; $player = New-Object System.Windows.Media.MediaPlayer; $player.Open((Get-Item '" + audio_file + "').FullName); $player.Play(); Start-Sleep -Seconds 5\"";
    
    std::system(command.c_str());
    return 0;
}
