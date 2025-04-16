# Comparison Blog Writer

A Python tool for generating structured comparison blog posts between cryptocurrency assets using OpenAI's GPT models.

## Overview

The Comparison Blog Writer automatically:

1. Selects crypto asset pairs from a CSV list (or accepts manual input)
2. Loads pre-existing research data for each asset
3. Combines the research into a detailed prompt
4. Generates a comprehensive comparison blog post
5. Processes the response into a structured JSON format
6. Calculates word count and estimated read time
7. Saves the output to a JSON file

## Directory Structure

```
Comparison Blog Writer/
├── data/                     # Input data directory
│   ├── crypto_comparison_pairs_cleaned.csv  # CSV file with asset pairs
│   └── README.md             # Data directory documentation
├── research/                 # Research data directory
│   └── assets/               # Asset-specific research files
│       ├── bitcoin.json      # Research data for Bitcoin
│       ├── ethereum.json     # Research data for Ethereum
│       └── ...               # Other asset research files
├── src/                      # Source code directory
│   └── comparison_blog_writer.py  # Main implementation
├── output/                   # Output directory
│   └── blogs/                # Generated blog posts
├── logs/                     # Log files
├── venv/                     # Virtual environment (created by setup scripts)
├── .env                      # Environment variables file (with OpenAI API key)
├── setup.sh                  # Unix setup script
├── requirements.txt          # Python dependencies
└── main.py                   # Script entry point
```

## Requirements

- Python 3.9+
- OpenAI API key
- Required Python packages (installed automatically by setup scripts):
  - openai
  - python-dotenv

## Installation

### Automatic Setup (Recommended)

#### Unix-based Systems (macOS/Linux):
```bash
# Clone or download this repository
cd "Comparison Blog Writer"
chmod +x setup.sh
./setup.sh
```

#### Windows:
```cmd
# Clone or download this repository
cd "Comparison Blog Writer"
setup.bat
```

### Manual Setup

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   - Unix-based systems: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate.bat`
4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up your OpenAI API key:
   - Create a `.env` file in the project root with `OPENAI_API_KEY=your-api-key`
   - Or export as an environment variable: `export OPENAI_API_KEY=your-api-key`

## Usage

### Activate the Virtual Environment

Before running the script, activate the virtual environment:

#### Unix-based Systems (macOS/Linux):
```bash
source venv/bin/activate
```

#### Windows:
```cmd
venv\Scripts\activate.bat
```

### Generate a Blog Post

#### With Random Asset Pair:
```bash
python main.py --random
```

#### With Specific Assets:
```bash
python main.py --term-a "Bitcoin" --term-b "Ethereum"
```

#### List Available Asset Pairs:
```bash
# List the first 10 available asset pairs from the CSV file
python main.py --list-pairs

# List more pairs (e.g., 20)
python main.py --list-pairs --limit 20
```

#### Generate Multiple Blog Posts in Batch Mode:
```bash
# Generate blogs for pairs from lines 2-5 in the CSV file
python main.py --batch --start-line 2 --end-line 5

# Generate blogs for a different range of pairs
python main.py --batch --start-line 10 --end-line 20
```

The batch mode reads pairs from the CSV file located at `data/crypto_comparison_pairs_cleaned.csv` and generates a blog for each pair within the specified line range (inclusive). Line numbers are 1-based, with line 1 being the header row, so lines 2-2551 contain the asset pairs (2550 total pairs).

## Output Format

The generated blog posts are saved as JSON files in the `output/blogs/` directory with the following structure:

```json
{
  "title": "Bitcoin vs Ethereum: A Comprehensive Comparison",
  "slug": "bitcoin-vs-ethereum-comparison",
  "published_date": "2025-04-16T13:21:16Z",
  "read_time": "3 min read",
  "author": {
    "name": "Moso Panda",
    "role": "Crypto Connoisseur"
  },
  "terms": {
    "term_a": "Bitcoin",
    "term_b": "Ethereum"
  },
  "media": {
    "term_a": "bitcoin-comparison-blog",
    "term_b": "ethereum-comparison-blog"
  },
  "introduction_paragraphs": [
    { "text": "Introduction paragraph 1..." },
    { "text": "Introduction paragraph 2..." }
  ],
  "jump_link_text": "Jump to Bitcoin vs Ethereum Comparison",
  "background": {
    "heading": "Understanding Bitcoin and Ethereum",
    "paragraphs": [
      { "text": "Background paragraph 1..." },
      { "text": "Background paragraph 2..." }
    ]
  },
  "key_differences": {
    "heading": "Key Differences Between Bitcoin and Ethereum",
    "items": [
      {
        "feature_title": "Purpose",
        "a_description": "Description for Bitcoin...",
        "b_description": "Description for Ethereum..."
      },
      // Additional key differences...
    ]
  },
  "comparison_table": {
    "heading": "Bitcoin vs Ethereum Comparison",
    "features": [
      {
        "label": "Launch Year",
        "a_value": "2009",
        "b_value": "2015"
      },
      // Additional features...
    ],
    "ideal_for": {
      "a": "Bitcoin is ideal for long-term investors...",
      "b": "Ethereum is ideal for developers..."
    }
  },
  "conclusion": {
    "heading": "Conclusion: Bitcoin vs Ethereum",
    "summary_paragraphs": [
      { "text": "Summary paragraph 1..." },
      { "text": "Summary paragraph 2..." },
      { "text": "Summary paragraph 3..." }
    ]
  }
}
```

## Customization

You can modify the following aspects of the blog generation:

- Prompt template in `src/comparison_blog_writer.py`
- Output schema validation rules
- OpenAI model parameters (temperature, max tokens, etc.)

## Logs

All script activity is logged in the `logs/` directory, including:
- API responses 
- Error messages
- Generation statistics

## License

MIT 