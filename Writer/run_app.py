import sys

sys.path.insert(0, 'src')
from studio.chat.app import detect_terminal, run_chat_studio

# Detect terminal
t = detect_terminal()
print(f'[INFO] Terminal: {t["terminal_name"]}')
print(f'[INFO] Mouse: {"Enabled" if t["supports_mouse"] else "Disabled (use keyboard scrolling)"}')
print()

# Run the app
run_chat_studio()
