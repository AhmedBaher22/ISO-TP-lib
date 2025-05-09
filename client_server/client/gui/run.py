#!/usr/bin/env python3
"""
Car ECU Update System GUI Launcher
---------------------------------
This script launches the GUI for the car's ECU update system.
"""

import sys
import os
import logging
from main_gui_controller import main

if __name__ == "__main__":
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("updater.log"),
                logging.StreamHandler()
            ]
        )
        
        # Run the application
        sys.exit(main())
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
