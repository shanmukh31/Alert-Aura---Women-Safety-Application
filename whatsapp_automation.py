import os
import time
import pyautogui
import geocoder
import logging
from datetime import datetime

class WhatsAppAutomation:
    def __init__(self):
        """Initialize WhatsApp automation"""
        self.setup_logging()
        self.logger.info("WhatsApp Automation initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('WhatsAppAutomation')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        fh = logging.FileHandler('whatsapp_automation.log')
        fh.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def get_current_location(self):
        """Get current location using IP geolocation"""
        try:
            g = geocoder.ip('me')
            if g.ok:
                return g.latlng
            return None
        except Exception as e:
            self.logger.error(f"Error getting location: {str(e)}")
            return None

    @staticmethod
    def open_chat(friend_name, disable_failsafe=False):
        """Open WhatsApp chat with the specified contact"""
        try:
            if disable_failsafe:
                pyautogui.FAILSAFE = False
            
            # Open WhatsApp
            os.system("start whatsapp:")
            time.sleep(5)  # Wait for WhatsApp to open
            
            # Click on search and type contact name
            pyautogui.moveTo(200, 100)
            pyautogui.click()
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'a')  # Select any existing text
            pyautogui.press('delete')      # Clear it
            time.sleep(0.5)
            pyautogui.write(friend_name)
            time.sleep(2)
            
            # Click on the contact
            pyautogui.moveTo(200, 200)
            pyautogui.click()
            time.sleep(2)  # Increased wait time
            
            # Click on message area
            pyautogui.moveTo(700, 700)
            pyautogui.click()
            time.sleep(1)
            
            return True
        except Exception as e:
            print(f"Error opening chat: {e}")
            return False

    @staticmethod
    def close_whatsapp():
        """Close WhatsApp window"""
        try:
            pyautogui.hotkey("alt", "f4")
            time.sleep(1)
        except Exception as e:
            print(f"Error closing WhatsApp: {e}")

    def send_message(self, contact_name, message, disable_failsafe=False):
        """
        Send WhatsApp message to a specific contact
        
        Args:
            contact_name (str): Name of the contact to send message to
            message (str): Message to send
            disable_failsafe (bool): Whether to disable the failsafe delay
        """
        try:
            # Open chat with the contact
            if not self.open_chat(contact_name, disable_failsafe):
                raise Exception("Failed to open chat")
            
            # Clear any existing text
            pyautogui.click()
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Type and send message
            pyautogui.write(message)
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(2)
            
            # Close WhatsApp
            self.close_whatsapp()
            
            self.logger.info(f"Message sent successfully to {contact_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message to {contact_name}: {str(e)}")
            return False

    def send_emergency_alerts(self, message):
        """
        Send emergency alerts to all contacts in emergency_contacts.txt
        
        Args:
            message (str): Emergency message to send
        """
        try:
            with open("emergency_contacts.txt", "r") as f:
                contacts = [line.strip().split("|") for line in f.readlines()]
            
            if not contacts:
                self.logger.warning("No emergency contacts found")
                return False
            
            success = True
            for name, _ in contacts:  # We only need the name for WhatsApp
                try:
                    if self.send_message(name, message, disable_failsafe=True):
                        self.logger.info(f"Emergency alert sent to {name}")
                    else:
                        self.logger.error(f"Failed to send emergency alert to {name}")
                        success = False
                except Exception as e:
                    self.logger.error(f"Error sending emergency alert to {name}: {str(e)}")
                    success = False
            
            return success
            
        except FileNotFoundError:
            self.logger.error("Emergency contacts file not found")
            return False
        except Exception as e:
            self.logger.error(f"Error in send_emergency_alerts: {str(e)}")
            return False

if __name__ == "__main__":
    # Test the WhatsApp automation
    wa = WhatsAppAutomation()
    
    # Test location
    location = wa.get_current_location()
    if location:
        print(f"Current location: {location}")
    
    # Test message sending (uncomment to test)
    # wa.send_message("1234567890", "Test message from WhatsApp Automation") 