import os, time, random, pyttsx3, requests, webbrowser, json, groq, pyautogui, threading, logging, geocoder
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from queue import Queue
import weakref

# Configure logging and constants
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
WHATSAPP_OPEN_DELAY, MESSAGE_INTERVAL, TAB_INTERVAL = 5, 0.05, 0.2
TTS_RATE, TTS_VOLUME = 240, 1.0
WINDOW_SIZE, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT = "1200x800", 800, 600

class WhatsAppAutomation:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    @lru_cache(maxsize=32)
    def open_chat(friend_name: str, disable_failsafe: bool = False) -> bool:
        try:
            if not disable_failsafe: pyautogui.FAILSAFE = True
            os.system("start whatsapp:"), time.sleep(WHATSAPP_OPEN_DELAY)
            pyautogui.typewrite(friend_name, interval=0.1), time.sleep(1.5)
            pyautogui.press('down'), time.sleep(0.5), pyautogui.press('enter'), time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Error opening chat: {e}")
            return False

    @staticmethod
    def send_message(friend_name: str, message: str, disable_failsafe: bool = False) -> bool:
        return WhatsAppAutomation.open_chat(friend_name, disable_failsafe) and (
            pyautogui.typewrite(message, interval=MESSAGE_INTERVAL),
            time.sleep(0.5),
            pyautogui.press('enter'),
            True
        )[3] if True else False

    @staticmethod
    def audio_call(friend_name: str, disable_failsafe: bool = False) -> bool:
        return WhatsAppAutomation.open_chat(friend_name, disable_failsafe) and (
            [pyautogui.press('tab') or time.sleep(TAB_INTERVAL) for _ in range(12)],
            pyautogui.press('enter'),
            True
        )[2] if True else False

    @staticmethod
    def video_call(friend_name: str, disable_failsafe: bool = False) -> bool:
        return WhatsAppAutomation.open_chat(friend_name, disable_failsafe) and (
            [pyautogui.press('tab') or time.sleep(TAB_INTERVAL) for _ in range(11)],
            pyautogui.press('enter'),
            True
        )[2] if True else False

class ContactManager:
    def __init__(self):
        self.contacts_file = "emergency_contacts.txt"
        self._contacts = {}
        self._lock = threading.Lock()
        self._load_contacts()

    def _load_contacts(self) -> None:
        try:
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r') as f:
                    for line in f:
                        if '|' in line:
                            name, number = line.strip().split('|')
                            self._contacts[name] = number
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
            self._contacts = {}

    def save_contacts(self) -> bool:
        try:
            with self._lock:
                with open(self.contacts_file, 'w') as f:
                    for name, number in self._contacts.items():
                        f.write(f"{name}|{number}\n")
                return True
        except Exception as e:
            logger.error(f"Error saving contacts: {e}")
            return False

    def add_contact(self, name: str, number: str) -> bool:
        with self._lock:
            self._contacts[name] = number
            return self.save_contacts()

    def remove_contact(self, name: str) -> bool:
        with self._lock:
            if name in self._contacts:
                del self._contacts[name]
                return self.save_contacts()
            return False

    def get_contacts(self) -> Dict[str, str]:
        with self._lock:
            return self._contacts.copy()

class ChatFrame(ttk.Frame):
    def __init__(self, parent, chatbot):
        super().__init__(parent)
        self.chatbot, self._message_queue = chatbot, Queue()
        self._create_widgets()
        self._start_message_processor()

    def _create_widgets(self):
        # Title and input frame
        ttk.Label(self, text="AI Voice Assistant Chat", style='Title.TLabel').pack(pady=(20, 20))
        input_frame = ttk.Frame(self, style='Card.TFrame')
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 20), padx=10)
        
        # Input field and send button
        self.input_field = ttk.Entry(input_frame, font=("Segoe UI", 10), style='TEntry')
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=15)
        self.input_field.bind('<Return>', self.handle_input)
        ttk.Button(input_frame, text="Send", style='Primary.TButton', command=self.handle_input).pack(side=tk.RIGHT, padx=15, pady=15)

        # Chat display
        chat_frame = ttk.Frame(self, style='Card.TFrame')
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, width=70, height=40, font=("Segoe UI", 10),
            bg=self.chatbot.colors['white'], fg=self.chatbot.colors['text'],
            relief=tk.FLAT, padx=15, pady=15
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_display.config(state=tk.DISABLED)

    def _start_message_processor(self):
        def message_worker():
            while True:
                message = self._message_queue.get()
                if message is None: break
                text, is_bot = message
                self._add_message(text, is_bot)
                self._message_queue.task_done()
        self._message_thread = threading.Thread(target=message_worker, daemon=True)
        self._message_thread.start()

    def handle_input(self, event=None):
        if text := self.input_field.get().strip():
            self.chatbot.handle_input(text)
            self.input_field.delete(0, tk.END)

    def add_message(self, text: str, is_bot: bool = True):
        self._message_queue.put((text, is_bot))

    def _add_message(self, text: str, is_bot: bool = True):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{'🤖 Bot: ' if is_bot else '👤 You: '}{text}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def __del__(self):
        if hasattr(self, '_message_queue'):
            self._message_queue.put(None)
            if hasattr(self, '_message_thread'):
                self._message_thread.join(timeout=1.0)

class ContactsFrame(ttk.Frame):
    def __init__(self, parent, chatbot):
        super().__init__(parent)
        self.chatbot = chatbot
        self._create_widgets()
        self._refresh_contacts()

    def _create_widgets(self):
        # Add contact section
        add_frame = ttk.LabelFrame(self, text="➕ Add New Contact", padding="15")
        add_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Name and number entries
        for label, attr in [("Name:", "name_entry"), ("Phone Number:", "number_entry")]:
            ttk.Label(add_frame, text=label, font=("Segoe UI", 10)).pack(anchor=tk.W)
            setattr(self, attr, ttk.Entry(add_frame, font=("Segoe UI", 10)))
            getattr(self, attr).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(add_frame, text="Add Contact", style='Primary.TButton', command=self._add_contact).pack(pady=5)
        
        # Contacts list
        list_frame = ttk.LabelFrame(self, text="👥 Your Contacts", padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview setup
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=25,
                       background=self.chatbot.colors['white'],
                       fieldbackground=self.chatbot.colors['white'])
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                       background=self.chatbot.colors['bg'])
        
        columns = ("Name", "Number")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(self, text="🗑️ Remove Selected Contact", style='Secondary.TButton',
                  command=self._delete_contact).pack(pady=10)

    def _add_contact(self):
        name, number = self.name_entry.get().strip(), self.number_entry.get().strip()
        if name and number:
            if self.chatbot.contact_manager.add_contact(name, number):
                self.chatbot.add_bot_message(f"✅ Contact '{name}' added successfully!")
                self.chatbot.speak(f"Contact {name} added successfully!")
                self._refresh_contacts()
                self.name_entry.delete(0, tk.END)
                self.number_entry.delete(0, tk.END)
            else:
                self.chatbot.add_bot_message("❌ Failed to add contact.")
                self.chatbot.speak("Failed to add contact.")
        else:
            self.chatbot.add_bot_message("❌ Please enter both name and number.")
            self.chatbot.speak("Please enter both name and number.")

    def _delete_contact(self):
        if selected := self.tree.selection():
            name = self.tree.item(selected[0])['values'][0]
            if self.chatbot.contact_manager.remove_contact(name):
                self.chatbot.add_bot_message(f"✅ Contact '{name}' removed successfully!")
                self.chatbot.speak(f"Contact {name} removed successfully!")
                self._refresh_contacts()
            else:
                self.chatbot.add_bot_message("❌ Failed to remove contact.")
                self.chatbot.speak("Failed to remove contact.")
        else:
            self.chatbot.add_bot_message("❌ Please select a contact to remove.")
            self.chatbot.speak("Please select a contact to remove.")

    def _refresh_contacts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name, number in self.chatbot.contact_manager.get_contacts().items():
            self.tree.insert("", tk.END, values=(name, number))

class WhatsAppFrame(ttk.Frame):
    def __init__(self, parent, chatbot):
        super().__init__(parent)
        self.chatbot = chatbot
        self._create_widgets()
        self._refresh_contacts()

    def _create_widgets(self):
        # Contact management frame
        contact_frame = ttk.LabelFrame(self, text="👥 Contact Management", padding="15")
        contact_frame.pack(fill=tk.X, pady=10)

        # Add contact section
        add_frame = ttk.Frame(contact_frame)
        add_frame.pack(fill=tk.X, pady=10)
        
        # Name and number entries
        for label, attr in [("Name:", "name_entry"), ("Phone:", "number_entry")]:
            ttk.Label(add_frame, text=label, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
            setattr(self, attr, ttk.Entry(add_frame, width=20, font=("Segoe UI", 10)))
            getattr(self, attr).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(add_frame, text="➕ Add Contact", style='Primary.TButton',
                  command=self._add_contact).pack(side=tk.LEFT, padx=5)

        # Contact selection frame
        select_frame = ttk.LabelFrame(self, text="📱 Select Contact", padding="15")
        select_frame.pack(fill=tk.X, pady=10)
        
        self.contact_var = tk.StringVar()
        self.contact_dropdown = ttk.Combobox(
            select_frame, textvariable=self.contact_var,
            state="readonly", width=30, font=("Segoe UI", 10)
        )
        self.contact_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        for text, command in [
            ("🗑️ Delete Contact", self._delete_contact),
            ("🔄 Refresh", self._refresh_contacts)
        ]:
            ttk.Button(select_frame, text=text, style='Secondary.TButton',
                      command=command).pack(side=tk.LEFT, padx=5)
        
        # Action buttons frame
        action_frame = ttk.LabelFrame(self, text="⚡ Actions", padding="15")
        action_frame.pack(fill=tk.X, pady=10)
        
        for text, command in [
            ("💬 Send Message", self._send_message),
            ("📞 Make Audio Call", self._make_audio_call),
            ("🎥 Make Video Call", self._make_video_call)
        ]:
            ttk.Button(action_frame, text=text, style='Primary.TButton',
                      command=command).pack(side=tk.LEFT, padx=5)

    def _add_contact(self):
        name, number = self.name_entry.get().strip(), self.number_entry.get().strip()
        if name and number:
            if self.chatbot.contact_manager.add_contact(name, number):
                self.chatbot.add_bot_message(f"✅ Contact '{name}' added successfully!")
                self.chatbot.speak(f"Contact {name} added successfully!")
                self._refresh_contacts()
                self.name_entry.delete(0, tk.END)
                self.number_entry.delete(0, tk.END)
            else:
                self.chatbot.add_bot_message("❌ Failed to add contact.")
                self.chatbot.speak("Failed to add contact.")
        else:
            self.chatbot.add_bot_message("❌ Please enter both name and number.")
            self.chatbot.speak("Please enter both name and number.")

    def _delete_contact(self):
        if contact := self.contact_var.get():
            if self.chatbot.contact_manager.remove_contact(contact):
                self.chatbot.add_bot_message(f"✅ Contact '{contact}' removed successfully!")
                self.chatbot.speak(f"Contact {contact} removed successfully!")
                self._refresh_contacts()
            else:
                self.chatbot.add_bot_message("❌ Failed to remove contact.")
                self.chatbot.speak("Failed to remove contact.")
        else:
            self.chatbot.add_bot_message("❌ Please select a contact to remove.")
            self.chatbot.speak("Please select a contact to remove.")

    def _refresh_contacts(self):
        contacts = self.chatbot.contact_manager.get_contacts()
        self.contact_dropdown['values'] = list(contacts.keys())
        if contacts:
            self.contact_dropdown.set(list(contacts.keys())[0])

    def _send_message(self):
        if not (contact := self.contact_var.get()):
            self.chatbot.add_bot_message("❌ Please select a contact.")
            self.chatbot.speak("Please select a contact.")
            return
            
        if message := simpledialog.askstring("Message", "Enter your message:", parent=self):
            if WhatsAppAutomation.send_message(contact, message):
                self.chatbot.add_bot_message(f"✅ Message sent to {contact}!")
                self.chatbot.speak(f"Message sent to {contact}!")
            else:
                self.chatbot.add_bot_message("❌ Failed to send message.")
                self.chatbot.speak("Failed to send message.")

    def _make_audio_call(self):
        if not (contact := self.contact_var.get()):
            self.chatbot.add_bot_message("❌ Please select a contact.")
            self.chatbot.speak("Please select a contact.")
            return
            
        if WhatsAppAutomation.audio_call(contact):
            self.chatbot.add_bot_message(f"📞 Audio call started with {contact}!")
            self.chatbot.speak(f"Audio call started with {contact}!")
        else:
            self.chatbot.add_bot_message("❌ Failed to start audio call.")
            self.chatbot.speak("Failed to start audio call.")

    def _make_video_call(self):
        if not (contact := self.contact_var.get()):
            self.chatbot.add_bot_message("❌ Please select a contact.")
            self.chatbot.speak("Please select a contact.")
            return
            
        if WhatsAppAutomation.video_call(contact):
            self.chatbot.add_bot_message(f"📹 Video call started with {contact}!")
            self.chatbot.speak(f"Video call started with {contact}!")
        else:
            self.chatbot.add_bot_message("❌ Failed to start video call.")
            self.chatbot.speak("Failed to start video call.")

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Assistant")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Set theme colors
        self.colors = {
            'bg': '#f0f2f5', 'primary': '#25D366', 'secondary': '#128C7E',
            'text': '#1c1e21', 'light_text': '#65676B', 'white': '#FFFFFF',
            'border': '#E4E6EB', 'hover': '#E8F5E9', 'accent': '#34B7F1',
            'success': '#4CAF50', 'warning': '#FFC107', 'error': '#F44336'
        }
        
        # Initialize components
        self._init_styles()
        self.contact_manager = ContactManager()
        self._setup_variables()
        self._create_main_container()
        self._setup_tts_engine()
        
        # Show welcome message
        self.add_bot_message("👋 Welcome! I'm your AI Voice Assistant. Type 'commands' to see available features.")
        self.speak("Welcome! I'm your AI Voice Assistant. Type 'commands' to see available features.")

    def _init_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        style_configs = {
            'TNotebook': {'background': self.colors['bg'], 'borderwidth': 0},
            'TNotebook.Tab': {
                'padding': [15, 5], 'font': ('Segoe UI', 10, 'bold'),
                'background': self.colors['white'], 'foreground': self.colors['text']
            },
            'TFrame': {'background': self.colors['bg']},
            'Card.TFrame': {
                'background': self.colors['white'],
                'relief': 'solid', 'borderwidth': 1
            },
            'TLabel': {
                'background': self.colors['bg'],
                'font': ('Segoe UI', 10)
            },
            'Title.TLabel': {
                'font': ('Segoe UI', 16, 'bold'),
                'foreground': self.colors['primary']
            },
            'Subtitle.TLabel': {
                'font': ('Segoe UI', 12),
                'foreground': self.colors['secondary']
            },
            'TButton': {
                'font': ('Segoe UI', 10),
                'padding': [15, 8]
            },
            'Primary.TButton': {
                'background': self.colors['primary'],
                'foreground': 'white'
            },
            'Secondary.TButton': {
                'background': self.colors['secondary'],
                'foreground': 'white'
            },
            'Accent.TButton': {
                'background': self.colors['accent'],
                'foreground': 'white'
            },
            'TEntry': {
                'font': ('Segoe UI', 10),
                'padding': [5, 5]
            }
        }
        
        for style_name, config in style_configs.items():
            self.style.configure(style_name, **config)
        
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.colors['primary'])],
                      foreground=[('selected', 'white')])
        self.style.map('Primary.TButton',
                      background=[('active', self.colors['secondary'])])
        self.style.map('Secondary.TButton',
                      background=[('active', self.colors['primary'])])
        
        self.root.configure(bg=self.colors['bg'])

    def _setup_variables(self):
        self.groq_api_key = ""
        self.google_api_key = ""
        self.weatherstack_api_key = ""
        
        self.command_patterns = {
            "weather": "weather [city] - Get weather for a city (e.g., 'weather hyderabad')",
            "news": "news [type] - Get news (types: india, world, cinema, sports)",
            "joke": "joke - Get a random dad joke",
            "horror": "horror - Get a short horror story",
            "long horror": "long horror - Get a full horror story",
            "wholesome": "wholesome - Get a feel-good story",
            "following": "following - Share your location with emergency contacts",
            "whatsapp": "whatsapp - Open WhatsApp automation menu",
            "contacts": "contacts - Manage WhatsApp contacts",
            "commands": "commands - Show available commands"
        }

    def _setup_tts_engine(self):
        self.engine = pyttsx3.init()
        for voice in self.engine.getProperty('voices'):
            if "female" in voice.name.lower() or "zira" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', TTS_RATE)
        self.engine.setProperty('volume', TTS_VOLUME)
        self._tts_queue = Queue()
        self._start_tts_thread()

    def _start_tts_thread(self):
        def tts_worker():
            while True:
                text = self._tts_queue.get()
                if text is None: break
                self.engine.say(text)
                self.engine.runAndWait()
                self._tts_queue.task_done()
        
        self._tts_thread = threading.Thread(target=tts_worker, daemon=True)
        self._tts_thread.start()

    def speak(self, text: str):
        self._tts_queue.put(text)

    def __del__(self):
        if hasattr(self, '_tts_queue'):
            self._tts_queue.put(None)
            if hasattr(self, '_tts_thread'):
                self._tts_thread.join(timeout=1.0)

    def _create_main_container(self):
        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.chat_frame = ChatFrame(self.notebook, self)
        self.contacts_frame = ContactsFrame(self.notebook, self)
        self.whatsapp_frame = WhatsAppFrame(self.notebook, self)
        
        self.notebook.add(self.chat_frame, text="💬 Chat")
        self.notebook.add(self.contacts_frame, text="👥 Contacts")
        self.notebook.add(self.whatsapp_frame, text="📱 WhatsApp")
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W, padding=[15, 8],
            font=('Segoe UI', 9), background=self.colors['white'],
            foreground=self.colors['light_text']
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 20))

    def handle_input(self, user_input: str):
        if not user_input: return
        self.add_user_message(user_input)
        threading.Thread(target=self._process_input, args=(user_input.lower(),), daemon=True).start()

    def _process_input(self, user_input: str):
        try:
            if "commands" in user_input:
                self._show_commands()
            elif "weather" in user_input:
                self._handle_weather(user_input)
            elif "news" in user_input:
                self._handle_news(user_input)
            elif "joke" in user_input:
                self._fetch_dadjoke()
            elif "horror" in user_input:
                self._fetch_reddit_content("scarystories" if "long" in user_input else "TwoSentenceHorror",
                                         "long horror" if "long" in user_input else "horror")
            elif "wholesome" in user_input:
                self._fetch_reddit_content("wholesomememes", "wholesome")
            elif "following" in user_input:
                self._share_location()
            elif "whatsapp" in user_input:
                self.notebook.select(2)
            elif "contacts" in user_input:
                self.notebook.select(1)
            elif any(greet in user_input for greet in ["hi", "hello", "hey"]):
                self.add_bot_message("Hey! What would you like to do today?")
                self.speak("Hey! What would you like to do today?")
            else:
                self._fallback_chat(user_input)
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            self.add_bot_message("Sorry, something went wrong. Please try again.")
            self.speak("Sorry, something went wrong. Please try again.")

    def _show_commands(self):
        commands_text = "📋 Available Commands:\n\n"
        emoji_map = {
            'weather': '🌤️', 'news': '📰', 'joke': '😄',
            'horror': '👻', 'long horror': '👻', 'wholesome': '💖',
            'following': '📍', 'whatsapp': '📱', 'contacts': '👥',
            'commands': '📋'
        }
        for command, description in self.command_patterns.items():
            commands_text += f"{emoji_map.get(command, '✨')} {description}\n"
        self.add_bot_message(commands_text)
        self.speak("Here are all the available commands.")

    def _share_location(self):
        try:
            if g := geocoder.ip('me'):
                lat, lng = g.latlng
                location_msg = f"📍 My current location: https://www.google.com/maps?q={lat},{lng}"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if contacts := self.contact_manager.get_contacts():
                    for name in contacts:
                        if WhatsAppAutomation.send_message(name, f"{location_msg}\nTime: {timestamp}"):
                            self.add_bot_message(f"✅ Location shared with {name}")
                            self.speak(f"Location shared with {name}")
                            time.sleep(1)
                            pyautogui.hotkey('alt', 'f4')
                            time.sleep(1)
                        else:
                            self.add_bot_message(f"❌ Failed to share location with {name}")
                            self.speak(f"Failed to share location with {name}")
                else:
                    self.add_bot_message("❌ No contacts found. Please add contacts first using the 'contacts' command.")
                    self.speak("No contacts found. Please add contacts first.")
            else:
                self.add_bot_message("❌ Could not determine your location.")
                self.speak("Could not determine your location.")
        except Exception as e:
            logger.error(f"Error sharing location: {e}")
            self.add_bot_message("❌ Error sharing location.")
            self.speak("Error sharing location.")

    def add_bot_message(self, text):
        self.chat_frame.add_message(text, True)

    def add_user_message(self, text):
        self.chat_frame.add_message(text, False)

    def _handle_weather(self, user_input: str):
        try:
            city = user_input.replace("weather", "").strip()
            if not city:
                self.add_bot_message("❌ Please specify a city (e.g., 'weather hyderabad')")
                self.speak("Please specify a city")
                return
                
            url = f"http://api.weatherstack.com/current?access_key={self.weatherstack_api_key}&query={city}"
            response = requests.get(url)
            data = response.json()
            
            if "error" in data:
                self.add_bot_message(f"❌ Error: {data['error']['info']}")
                self.speak("Error getting weather information")
                return
                
            current = data["current"]
            location = data["location"]
            
            weather_msg = f"🌤️ Weather in {location['name']}, {location['country']}:\n"
            weather_msg += f"Temperature: {current['temperature']}°C\n"
            weather_msg += f"Feels like: {current['feelslike']}°C\n"
            weather_msg += f"Humidity: {current['humidity']}%\n"
            weather_msg += f"Wind: {current['wind_speed']} km/h\n"
            weather_msg += f"Description: {current['weather_descriptions'][0]}"
            
            self.add_bot_message(weather_msg)
            self.speak(f"Here's the weather in {location['name']}")
            
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            self.add_bot_message("❌ Error fetching weather information")
            self.speak("Error fetching weather information")

    def _handle_news(self, user_input: str):
        try:
            news_type = user_input.replace("news", "").strip()
            if not news_type:
                self.add_bot_message("❌ Please specify news type (india, world, cinema, sports)")
                self.speak("Please specify news type")
                return
                
            news_type = news_type.lower()
            if news_type not in ["india", "world", "cinema", "sports"]:
                self.add_bot_message("❌ Invalid news type. Choose from: india, world, cinema, sports")
                self.speak("Invalid news type")
                return
                
            url = f"https://newsapi.org/v2/top-headlines?country={'in' if news_type == 'india' else 'us'}&category={news_type}&apiKey={self.google_api_key}"
            response = requests.get(url)
            data = response.json()
            
            if data["status"] != "ok":
                self.add_bot_message("❌ Error fetching news")
                self.speak("Error fetching news")
                return
                
            articles = data["articles"][:5]
            news_msg = f"📰 Top {news_type.capitalize()} News:\n\n"
            
            for i, article in enumerate(articles, 1):
                news_msg += f"{i}. {article['title']}\n"
                news_msg += f"   Source: {article['source']['name']}\n"
                news_msg += f"   {article['description']}\n\n"
            
            self.add_bot_message(news_msg)
            self.speak(f"Here are the top {news_type} news headlines")
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            self.add_bot_message("❌ Error fetching news")
            self.speak("Error fetching news")

    def _fetch_reddit_content(self, subreddit: str, content_type: str):
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=1"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if "data" not in data or "children" not in data["data"]:
                self.add_bot_message("❌ Error fetching content")
                self.speak("Error fetching content")
                return
                
            post = data["data"]["children"][0]["data"]
            title = post["title"]
            content = post["selftext"] if content_type == "long horror" else post["title"]
            
            if content_type == "long horror":
                self.add_bot_message(f"👻 {title}\n\n{content}")
                self.speak("Here's a horror story for you")
            else:
                self.add_bot_message(f"👻 {content}")
                self.speak("Here's a horror story for you")
                
        except Exception as e:
            logger.error(f"Error fetching {content_type} content: {e}")
            self.add_bot_message("❌ Error fetching content")
            self.speak("Error fetching content")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ChatbotGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        print(f"Error starting application: {e}")