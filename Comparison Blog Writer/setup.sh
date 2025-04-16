#!/bin/bash
# Setup script for Comparison Blog Writer

# Check if running on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows OS"
    ACTIVATE_CMD="venv\\Scripts\\activate"
    PYTHON_CMD="python"
else
    echo "Detected Unix-like OS (macOS/Linux)"
    ACTIVATE_CMD="source venv/bin/activate"
    PYTHON_CMD="python3"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up the Comparison Blog Writer virtual environment...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please make sure Python 3.9+ is installed."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
eval $ACTIVATE_CMD

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    echo "# OpenAI API Key - Replace with your actual API key" > .env
    echo "OPENAI_API_KEY=your-api-key-goes-here" >> .env
    echo -e "${YELLOW}IMPORTANT: Please edit the .env file and add your OpenAI API key.${NC}"
else
    echo ".env file already exists."
fi

# Create necessary directories
mkdir -p logs
mkdir -p output/blogs

echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "To activate the virtual environment, run:"
echo -e "${YELLOW}$ACTIVATE_CMD${NC}"
echo ""
echo "To run the blog generator with a random asset pair, run:"
echo -e "${YELLOW}python main.py --random${NC}"
echo ""
echo "For more information, refer to the README.md file." 