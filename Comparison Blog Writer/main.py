#!/usr/bin/env python3
"""
Comparison Blog Writer

A script to generate comparison blog posts between two crypto assets.
"""

import os
import sys
import argparse
import logging
from typing import Tuple
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from .env file in the project root
    dotenv_path = Path(__file__).parent / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded environment variables from {dotenv_path}")
    else:
        load_dotenv()  # Try default locations
        print("Loaded environment variables from default location")
except ImportError:
    print("python-dotenv package not found. Environment variables must be set manually.")

# Add the current directory to the path so we can import our module
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from src.comparison_blog_writer import ComparisonBlogWriter
except ImportError:
    print("Error: Could not import ComparisonBlogWriter. Make sure the src directory is set up correctly.")
    sys.exit(1)

def configure_logging():
    """Set up logging configuration for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the script."""
    parser = argparse.ArgumentParser(
        description="Generate a comparison blog post between two crypto assets."
    )
    
    # Create a mutually exclusive group for the different ways to specify assets
    group = parser.add_mutually_exclusive_group()
    
    # Add arguments for specifying asset terms
    group.add_argument(
        "--term-a",
        help="First crypto asset term to compare",
        type=str
    )
    
    parser.add_argument(
        "--term-b",
        help="Second crypto asset term to compare (used with --term-a)",
        type=str
    )
    
    # Add argument for random selection
    group.add_argument(
        "--random",
        help="Select a random asset pair from the CSV",
        action="store_true"
    )
    
    # Add arguments for batch processing
    group.add_argument(
        "--batch",
        help="Generate blogs for a range of pairs from the CSV file",
        action="store_true"
    )
    
    parser.add_argument(
        "--start-line",
        help="Starting line number in the CSV file (1-based, defaults to 2)",
        type=int,
        default=2
    )
    
    parser.add_argument(
        "--end-line",
        help="Ending line number in the CSV file (1-based, inclusive)",
        type=int,
        default=5
    )
    
    # Add argument to list available pairs
    group.add_argument(
        "--list-pairs",
        help="List available asset pairs from the CSV file",
        action="store_true"
    )
    
    parser.add_argument(
        "--limit",
        help="Limit the number of pairs to display when using --list-pairs",
        type=int,
        default=10
    )
    
    return parser.parse_args()

def get_asset_terms(args: argparse.Namespace) -> Tuple[str, str]:
    """
    Get the asset terms to compare.
    
    Args:
        args: Command line arguments
        
    Returns:
        A tuple containing (term_a, term_b)
    """
    if args.random:
        # Select a random asset pair
        blog_writer = ComparisonBlogWriter()
        return blog_writer.get_random_asset_pair()
    
    if args.term_a and args.term_b:
        # Use the provided asset terms
        return args.term_a, args.term_b
    
    # If no valid option was provided, exit
    print("Error: Please specify two asset terms (--term-a and --term-b) or use --random.")
    sys.exit(1)

def generate_blog(term_a: str, term_b: str) -> None:
    """
    Generate a comparison blog post.
    
    Args:
        term_a: The first asset term
        term_b: The second asset term
    """
    try:
        # Initialize the blog writer
        blog_writer = ComparisonBlogWriter()
        
        # Generate the blog post
        blog_data = blog_writer.process_blog_generation(term_a, term_b)
        
        print("\nBlog post generated successfully!")
        print(f"Title: {blog_data.get('title', 'No title')}")
        
        # Calculate word count
        word_count = blog_writer._calculate_word_count(blog_data)
        print(f"Word count: {word_count}")
        
        # Extract read time from the read_time field (e.g. "3 min read" -> 3)
        read_time_str = blog_data.get('read_time', '0 min read')
        read_time = int(read_time_str.split()[0]) if read_time_str else 0
        print(f"Read time: {read_time} minutes")
        
        slug = blog_data.get('slug', 'blog')
        print(f"Output: {blog_writer.output_path / f'{slug}.json'}")
        
    except Exception as e:
        logging.error(f"Error generating blog post: {e}")
        sys.exit(1)

def generate_blogs_batch(start_line: int, end_line: int) -> None:
    """
    Generate multiple comparison blog posts for a range of asset pairs from the CSV.
    
    Args:
        start_line: The starting line number in the CSV (1-based)
        end_line: The ending line number in the CSV (1-based, inclusive)
    """
    # Initialize the blog writer
    blog_writer = ComparisonBlogWriter()
    
    # Get the path to the CSV file
    csv_path = blog_writer.data_path / "crypto_comparison_pairs_cleaned.csv"
    
    try:
        # Read the CSV file and extract the specified lines
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Skip header row
            lines = csvfile.readlines()[1:]  # 0-based index, so we start from index 1 for row 2
            
            # Adjust for 0-based indexing (line 2 in the file is index 1 in the list)
            start_index = start_line - 2  # Line 2 becomes index 0
            end_index = end_line - 2      # Inclusive end
            
            # Ensure indices are within bounds
            if start_index < 0:
                start_index = 0
                print(f"Warning: Start line adjusted to line 2 (minimum).")
                
            if end_index >= len(lines):
                end_index = len(lines) - 1
                print(f"Warning: End line adjusted to line {end_index + 2} (maximum).")
                
            # Get the specified range of lines
            selected_lines = lines[start_index:end_index + 1]
            
            # Process each line
            for i, line in enumerate(selected_lines):
                # Parse the line to get the asset pair
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    term_a, term_b = parts[0], parts[1]
                    
                    # Generate the blog
                    print(f"\n[{i+1}/{len(selected_lines)}] Processing: {term_a} vs {term_b}")
                    try:
                        # Generate the blog post
                        blog_data = blog_writer.process_blog_generation(term_a, term_b)
                        
                        # Print success info
                        print(f"✅ Blog generated successfully!")
                        print(f"   Title: {blog_data.get('title', 'No title')}")
                        
                        # Calculate word count
                        word_count = blog_writer._calculate_word_count(blog_data)
                        print(f"   Word count: {word_count}")
                        
                        # Extract read time
                        read_time_str = blog_data.get('read_time', '0 min read')
                        read_time = int(read_time_str.split()[0]) if read_time_str else 0
                        print(f"   Read time: {read_time} minutes")
                        
                        # Output file path
                        slug = blog_data.get('slug', 'blog')
                        print(f"   Output: {blog_writer.output_path / f'{slug}.json'}")
                        
                    except Exception as e:
                        logging.error(f"Error generating blog for {term_a} vs {term_b}: {e}")
                        print(f"❌ Failed to generate blog for {term_a} vs {term_b}: {e}")
                else:
                    logging.warning(f"Invalid line format at line {start_index + i + 2}: {line.strip()}")
                    print(f"⚠️ Skipping invalid line: {line.strip()}")
            
            print(f"\nBatch processing complete. Generated {len(selected_lines)} blog posts.")
                
    except FileNotFoundError:
        error_msg = f"CSV file not found: {csv_path}"
        logging.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        print(f"Error: Failed to process CSV file: {e}")
        sys.exit(1)

def list_available_pairs(limit: int = 10) -> None:
    """
    List available asset pairs from the CSV file.
    
    Args:
        limit: Maximum number of pairs to display
    """
    # Initialize the blog writer just to get the data path
    blog_writer = ComparisonBlogWriter()
    
    # Get the path to the CSV file
    csv_path = blog_writer.data_path / "crypto_comparison_pairs_cleaned.csv"
    
    try:
        # Read the CSV file
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Read all lines and skip header
            lines = csvfile.readlines()
            header = lines[0].strip()
            pairs = lines[1:]  # Skip header row
            
            total_pairs = len(pairs)
            
            print(f"\nFound {total_pairs} asset pairs in the CSV file.")
            print("CSV Header:", header)
            print("\nSample pairs:")
            print("-" * 40)
            
            # Show limited number of pairs
            display_limit = min(limit, total_pairs)
            for i in range(display_limit):
                line_parts = pairs[i].strip().split(',')
                if len(line_parts) >= 2:
                    print(f"Line {i+2}: {line_parts[0]} vs {line_parts[1]}")
            
            if display_limit < total_pairs:
                print(f"\n... and {total_pairs - display_limit} more pairs.")
            
            print("-" * 40)
            print("To generate blogs for a range of pairs, use:")
            print("python main.py --batch --start-line 2 --end-line 5")
            
    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def main():
    """Main entry point for the script."""
    # Configure logging
    configure_logging()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Process based on the provided arguments
    if args.list_pairs:
        # List available asset pairs
        list_available_pairs(args.limit)
    elif args.batch:
        # Generate blogs in batch mode
        print(f"Generating blogs for pairs from lines {args.start_line} to {args.end_line}")
        generate_blogs_batch(args.start_line, args.end_line)
    else:
        # Get the asset terms to compare
        term_a, term_b = get_asset_terms(args)
        
        print(f"Generating comparison blog post: {term_a} vs {term_b}")
        
        # Generate a single blog post
        generate_blog(term_a, term_b)

if __name__ == "__main__":
    main() 