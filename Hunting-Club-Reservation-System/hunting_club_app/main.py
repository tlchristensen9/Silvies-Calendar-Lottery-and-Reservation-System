# Application entry point
#!/usr/bin/env python3
"""
Hunting Club Reservation System - Main Application Entry Point

This is the main entry point for the Hunting Club Reservation System.
The application manages cabin reservations for 21 club members during
the May-July hunting season using a fair lottery system.

Author: AI Assistant
Date: 2025
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.app_controller import AppController
from utils.data_manager import DataManager
from utils.constants import APP_NAME, APP_VERSION

def setup_logging():
    """Set up logging configuration for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hunting_club.log'),
            logging.StreamHandler()
        ]
    )

def setup_application():
    """Configure the QApplication with appropriate settings."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Hunting Club")
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app

def initialize_data():
    """Initialize the application data and create necessary directories."""
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create initial data files if they don't exist
        data_manager.initialize_data_files()
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize data: {e}")
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to initialize application data:\n{str(e)}\n\nPlease check permissions and try again."
        )
        return False

def main():
    """Main application entry point."""
    try:
        # Set up logging
        setup_logging()
        logging.info(f"Starting {APP_NAME} v{APP_VERSION}")
        
        # Create and configure QApplication
        app = setup_application()
        
        # Initialize data
        if not initialize_data():
            return 1
        
        # Create and show main controller
        controller = AppController()
        controller.show()
        
        # Start the application event loop
        exit_code = app.exec_()
        
        logging.info(f"Application exiting with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logging.error(f"Critical error in main: {e}")
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "Critical Error",
                f"A critical error occurred:\n{str(e)}\n\nThe application will now exit."
            )
        return 1

if __name__ == "__main__":
    sys.exit(main())