#!/usr/bin/env python
"""
Test script for the clip_anything service.
This script allows you to test the clip_anything functionality directly without going through the API.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the src directory to the path so we can import the services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.clip_anything import process_video_with_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to test the clip_anything service.
    """
    parser = argparse.ArgumentParser(description='Test the clip_anything service')
    parser.add_argument('--video', '-v', type=str, required=True, help='Path to the input video file')
    parser.add_argument('--prompt', '-p', type=str, required=True, help='Text prompt to extract relevant clips')
    args = parser.parse_args()
    
    video_path = args.video
    prompt = args.prompt
    
    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}")
        return 1
    
    try:
        logging.info(f"Processing video: {video_path}")
        logging.info(f"Prompt: {prompt}")
        
        # Process the video
        output_path = process_video_with_prompt(video_path, prompt)
        
        if output_path:
            logging.info(f"Video processing completed successfully!")
            logging.info(f"Output video saved to: {output_path}")
            return 0
        else:
            logging.error("No matching segments found in the video")
            return 1
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
