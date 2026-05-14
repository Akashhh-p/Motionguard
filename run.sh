#!/bin/bash

# OpenCV YOLOv8 Project - Run Script
# This script provides easy execution of the image processing and detection tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to display usage
usage() {
    echo "Usage: ./run.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  --image FILE          Process a single image file"
    echo "  --image FILE --width W  Process image with specific width"
    echo "  --webcam              Run real-time webcam detection"
    echo "  --webcam --camera N   Use camera index N"
    echo "  --webcam --conf CONF  Set confidence threshold (0-1)"
    echo "  --help                Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh --image images/sample.jpg"
    echo "  ./run.sh --webcam"
    echo "  ./run.sh --webcam --camera 0 --conf 0.5"
    echo ""
}

# Check if requirements are installed
check_requirements() {
    print_info "Checking if required packages are installed..."
    
    if ! python -c "import cv2" 2>/dev/null; then
        print_error "OpenCV not found. Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    if ! python -c "import ultralytics" 2>/dev/null; then
        print_error "Ultralytics not found. Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    print_info "All dependencies verified!"
}

# Main script logic
if [ $# -eq 0 ]; then
    print_info "Running default image processing..."
    python scripts/image_basics.py
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
elif [ "$1" = "--image" ]; then
    if [ -z "$2" ]; then
        print_error "Image path required after --image"
        usage
        exit 1
    fi
    
    # Build the command
    cmd="python scripts/image_basics.py --image $2"
    
    # Check for additional parameters
    if [ "$3" = "--width" ] && [ ! -z "$4" ]; then
        cmd="$cmd --width $4"
    fi
    
    print_info "Processing image: $2"
    $cmd
    
elif [ "$1" = "--webcam" ]; then
    print_info "Starting webcam detection..."
    cmd="python scripts/image_basics.py --webcam"
    
    # Parse additional webcam options
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --camera)
                if [ ! -z "$2" ]; then
                    cmd="$cmd --camera $2"
                    shift 2
                else
                    print_error "Camera index required after --camera"
                    exit 1
                fi
                ;;
            --conf)
                if [ ! -z "$2" ]; then
                    cmd="$cmd --conf $2"
                    shift 2
                else
                    print_error "Confidence value required after --conf"
                    exit 1
                fi
                ;;
            *)
                print_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    $cmd
else
    print_error "Unknown option: $1"
    usage
    exit 1
fi

print_info "Done!"
