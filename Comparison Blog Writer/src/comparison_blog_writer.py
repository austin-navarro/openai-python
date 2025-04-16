import os
import json
import csv
import random
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import math

# Try to import the OpenAI client
try:
    from openai import OpenAI
except ImportError:
    print("OpenAI package not found. Please install it using: pip install openai")
    exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', f'blog_generator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'))
    ]
)
logger = logging.getLogger("ComparisonBlogWriter")

# Schema definitions
class ParagraphItem:
    """Schema for paragraph items in the blog post."""
    text: str
    
class ComparisonBlogPost:
    """Schema for the structured blog post."""
    title: str
    slug: str
    published_date: str
    read_time: str
    author: Dict[str, str]
    media: Dict[str, str]
    introduction_paragraphs: List[ParagraphItem]
    jump_link_text: str
    background: Dict[str, str]
    key_differences: Dict[str, List[Dict[str, str]]]
    comparison_table: Dict[str, Any]
    conclusion: Dict[str, Any]

class ComparisonBlogWriter:
    """
    A class to generate comparison blog posts between two crypto assets.
    
    This class handles:
    1. Loading asset pairs from CSV
    2. Retrieving research data for each asset
    3. Generating a comparison blog using OpenAI
    4. Post-processing the blog content
    5. Calculating word count and read time
    6. Saving the output to JSON
    """
    
    def __init__(self, base_path: str = "."):
        """
        Initialize the ComparisonBlogWriter.
        
        Args:
            base_path: The base path for the project
        """
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.research_path = self.base_path / "research"
        self.output_path = self.base_path / "output" / "blogs"
        self.logs_path = self.base_path / "logs"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)
        
        # Initialize OpenAI client
        self.client = self._initialize_openai_client()
    
    def _initialize_openai_client(self) -> OpenAI:
        """
        Initialize the OpenAI client.
        
        Returns:
            An initialized OpenAI client
        """
        # Check if OPENAI_API_KEY is set in the environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # Try to load from .env file
            try:
                from dotenv import load_dotenv
                # Look for .env file in the project root
                env_path = Path(self.base_path).parent / '.env'
                if env_path.exists():
                    load_dotenv(dotenv_path=env_path)
                else:
                    # Try in the current directory
                    load_dotenv()
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    logger.info("Loaded API key from .env file")
                else:
                    logger.warning("API key not found in .env file")
            except ImportError:
                logger.error("dotenv package not found and OPENAI_API_KEY not set in environment")
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or create a .env file.")
            
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or create a .env file.")
            
        return OpenAI(api_key=api_key)
    
    def get_random_asset_pair(self) -> Tuple[str, str]:
        """
        Select a random asset pair from the CSV file.
        
        Returns:
            A tuple containing (term_a, term_b)
        """
        csv_path = self.data_path / "crypto_comparison_pairs_cleaned.csv"
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Skip header row
            next(reader)
            # Get all rows
            pairs = list(reader)
            
        if not pairs:
            raise ValueError("No asset pairs found in the CSV file")
            
        # Select a random pair
        selected_pair = random.choice(pairs)
        term_a, term_b = selected_pair
        
        logger.info(f"Selected asset pair: {term_a} vs {term_b}")
        return term_a, term_b
    
    def load_research(self, asset_name: str) -> Optional[Dict[str, Any]]:
        """
        Load research data for a given asset.
        
        Args:
            asset_name: The name of the asset to load research for
            
        Returns:
            Research data as a dictionary or None if not found
        """
        # Convert asset name to lowercase for file lookup
        asset_name_lower = asset_name.lower()
        research_file = self.research_path / "assets" / f"{asset_name_lower}.json"
        
        try:
            with open(research_file, 'r', encoding='utf-8') as f:
                research_data = json.load(f)
                logger.info(f"Loaded research for {asset_name}")
                return research_data
        except FileNotFoundError:
            logger.warning(f"Research data not found for {asset_name}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error decoding research data for {asset_name}")
            return None
    
    def process_blog_generation(self, term_a: str, term_b: str) -> Dict[str, Any]:
        """
        Generate a comparison blog post for two assets.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            
        Returns:
            A dictionary containing the blog post data
        """
        # Create slug for the blog post
        slug = self._create_slug(f"{term_a}-vs-{term_b}")
        
        # Load research data for both assets
        research_a = self.load_research(term_a)
        research_b = self.load_research(term_b)
        
        # Combine research data
        research_context = self._combine_research(term_a, term_b, research_a, research_b)
        
        # Generate the blog post
        blog_data = self.generate_blog_post(term_a, term_b, research_context)
        
        # Post-process the blog data
        blog_data = self._post_process_blog_json(blog_data, term_a, term_b)
        
        # Calculate word count and read time
        word_count = self._calculate_word_count(blog_data)
        read_time = self._calculate_read_time(word_count)
        
        # Add metadata
        blog_data["read_time"] = f"{read_time} min read"
        
        # Validate the blog post structure
        self._validate_blog_post_schema(blog_data)
        
        # Save the blog post
        output_file = self.output_path / f"{slug}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(blog_data, f, indent=2)
            
        logger.info(f"Blog post saved to {output_file}")
        
        return blog_data
    
    def _combine_research(self, term_a: str, term_b: str, 
                          research_a: Optional[Dict[str, Any]], 
                          research_b: Optional[Dict[str, Any]]) -> str:
        """
        Combine research data for two assets into a single context string.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            research_a: Research data for the first asset
            research_b: Research data for the second asset
            
        Returns:
            A string containing the combined research data
        """
        research_context = f"## Research for {term_a}:\n\n"
        
        if research_a and "research_content" in research_a:
            research_context += research_a["research_content"]
        else:
            research_context += f"No detailed research available for {term_a}."
            
        research_context += f"\n\n## Research for {term_b}:\n\n"
        
        if research_b and "research_content" in research_b:
            research_context += research_b["research_content"]
        else:
            research_context += f"No detailed research available for {term_b}."
            
        return research_context
    
    def _get_prompt(self, term_a: str, term_b: str, research_context: str) -> str:
        """
        Create the prompt for the OpenAI API.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            research_context: The combined research data
            
        Returns:
            The formatted prompt string
        """
        prompt = f"""
You are an expert crypto content creator specializing in educational comparison blog posts.

Task: Create a comprehensive comparison blog post between {term_a} and {term_b}.

Audience: Crypto enthusiasts and investors seeking in-depth, technical comparisons.

Goals:
- Be informative, detailed, and objective in your comparison
- Follow strict SEO best practices for crypto comparison content
- Structure the content to match the required JSON output format exactly
- Use properly formatted markdown for all text content
- Ensure the content is between 1,300-1,500 words total

Your blog post must follow this exact structure:

1. A clear, SEO-friendly title comparing {term_a} and {term_b}
2. 2-3 introduction paragraphs explaining the comparison purpose
3. Background section with a heading and content for both assets
4. 5 key differences between {term_a} and {term_b}, each with a feature title, description for {term_a}, and description for {term_b}
5. A comparison table with at least 5 features
6. A conclusion section with 3 summary paragraphs

The schema MUST match this exact format:
{{
  "title": "string",
  "slug": "string",
  "published_date": "YYYY-MM-DDThh:mm:ssZ",
  "read_time": "X min read",
  "author": {{
    "name": "Moso Panda",
    "role": "Crypto Connoisseur"
  }},
  "media": {{
    "term_a": "{term_a.lower()}-comparison-blog",
    "term_b": "{term_b.lower()}-comparison-blog"
  }},
  "introduction_paragraphs": [
    {{ "text": "paragraph text" }},
    {{ "text": "paragraph text" }}
  ],
  "jump_link_text": "Jump to {term_a} vs {term_b} Comparison",
  "background": {{
    "heading": "Understanding {term_a} and {term_b}",
    "content": "Detailed background information on both cryptocurrencies..."
  }},
  "key_differences": {{
    "heading": "Key Differences Between {term_a} and {term_b}",
    "items": [
      {{
        "feature_title": "string",
        "a_description": "description for {term_a}",
        "b_description": "description for {term_b}"
      }},
      // Include 5 key differences total
    ]
  }},
  "comparison_table": {{
    "heading": "{term_a} vs {term_b} Comparison",
    "features": [
      {{
        "label": "Feature Name",
        "a_value": "Value for {term_a}",
        "b_value": "Value for {term_b}"
      }},
      // Include at least 5 features
    ],
    "ideal_for": {{
      "a": "Who {term_a} is best for",
      "b": "Who {term_b} is best for"
    }}
  }},
  "conclusion": {{
    "heading": "Conclusion: {term_a} vs {term_b}",
    "summary_paragraphs": [
      {{ "text": "paragraph text" }},
      {{ "text": "paragraph text" }},
      {{ "text": "paragraph text" }}
    ]
  }}
}}

Use the following research to inform your comparison:

{research_context}
"""
        return prompt
    
    def generate_blog_post(self, term_a: str, term_b: str, research_context: str) -> Dict[str, Any]:
        """
        Generate a comparison blog post using OpenAI's API.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            research_context: The combined research data
            
        Returns:
            A dictionary containing the blog post data
        """
        prompt = self._get_prompt(term_a, term_b, research_context)
        
        try:
            logger.info(f"Calling OpenAI API to generate blog post for {term_a} vs {term_b}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4096,
                frequency_penalty=0.2,
                presence_penalty=0.1,
                response_format={"type": "json_object"}
            )
            
            # Extract JSON content from the response
            content = response.choices[0].message.content
            
            # Log the raw response for debugging purposes
            self._log_blog_activity(term_a, term_b, True, content)
            
            # Parse the JSON content
            try:
                blog_data = json.loads(content)
                return blog_data
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {e}")
                # Try to clean and fix the JSON
                cleaned_content = self._clean_json_content(content)
                blog_data = json.loads(cleaned_content)
                return blog_data
                
        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            self._log_blog_activity(term_a, term_b, False, str(e))
            raise
    
    def _clean_json_content(self, content: str) -> str:
        """
        Clean and fix JSON content from OpenAI's response.
        
        Args:
            content: The JSON string to clean
            
        Returns:
            A cleaned JSON string
        """
        # Remove any markdown code block indicators
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        
        # Fix common issues with quotation marks
        content = content.replace("'", '"')
        
        # Fix unquoted keys
        content = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', content)
        
        # Fix trailing commas in arrays and objects
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        return content
    
    def _post_process_blog_json(self, blog_json: Dict[str, Any], term_a: str, term_b: str) -> Dict[str, Any]:
        """
        Post-process the blog JSON data to fix any issues.
        
        Args:
            blog_json: The blog data to process
            term_a: The first asset term
            term_b: The second asset term
            
        Returns:
            The processed blog data
        """
        # Ensure published_date is in the correct format (ISO 8601)
        if "published_date" not in blog_json or not blog_json["published_date"]:
            blog_json["published_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            # Try to convert existing date to ISO 8601 if it's not already
            try:
                # Check if date is simple YYYY-MM-DD format and convert to full ISO 8601
                if re.match(r'^\d{4}-\d{2}-\d{2}$', blog_json["published_date"]):
                    # Convert to full ISO 8601 by adding time component
                    date_obj = datetime.strptime(blog_json["published_date"], "%Y-%m-%d")
                    blog_json["published_date"] = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                # If parsing fails, set to current time in ISO 8601
                blog_json["published_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
        # Ensure read_time is set
        if "read_time" not in blog_json or not blog_json["read_time"]:
            blog_json["read_time"] = "5 min read"
            
        # Ensure author is set
        if "author" not in blog_json:
            blog_json["author"] = {
                "name": "Moso Panda",
                "role": "Crypto Connoisseur"
            }
            
        # Ensure media terms are set
        if "media" not in blog_json:
            blog_json["media"] = {
                "term_a": f"{term_a.lower()}-comparison-blog",
                "term_b": f"{term_b.lower()}-comparison-blog"
            }
            
        # Ensure introduction_paragraphs is a list of objects with 'text' key
        if "introduction_paragraphs" in blog_json and isinstance(blog_json["introduction_paragraphs"], list):
            for i, para in enumerate(blog_json["introduction_paragraphs"]):
                if isinstance(para, str):
                    blog_json["introduction_paragraphs"][i] = {"text": para}
        
        # Ensure jump_link_text is set
        if "jump_link_text" not in blog_json or not blog_json["jump_link_text"]:
            blog_json["jump_link_text"] = f"Jump to {term_a} vs {term_b} Comparison"
            
        # Ensure background is formatted correctly
        if "background" not in blog_json:
            blog_json["background"] = {
                "heading": f"Understanding {term_a} and {term_b}",
                "content": "Detailed background information on both cryptocurrencies..."
            }
        
        # Convert old background_a and background_b if present
        if "background_a" in blog_json and "background_b" in blog_json:
            combined_content = ""
            # Extract text from background_a
            if isinstance(blog_json["background_a"], list):
                for para in blog_json["background_a"]:
                    if isinstance(para, dict) and "text" in para:
                        combined_content += para["text"] + "\n\n"
                    elif isinstance(para, str):
                        combined_content += para + "\n\n"
            
            # Add a separator
            combined_content += f"### {term_b}\n\n"
            
            # Extract text from background_b
            if isinstance(blog_json["background_b"], list):
                for para in blog_json["background_b"]:
                    if isinstance(para, dict) and "text" in para:
                        combined_content += para["text"] + "\n\n"
                    elif isinstance(para, str):
                        combined_content += para + "\n\n"
            
            # Create new background format
            blog_json["background"] = {
                "heading": f"Understanding {term_a} and {term_b}",
                "content": combined_content.strip()
            }
            
            # Remove old keys
            if "background_a" in blog_json:
                del blog_json["background_a"]
            if "background_b" in blog_json:
                del blog_json["background_b"]
        
        # Ensure key_differences is formatted correctly
        if "key_differences" not in blog_json:
            blog_json["key_differences"] = {
                "heading": f"Key Differences Between {term_a} and {term_b}",
                "items": []
            }
            
        # Convert old key_differences format if present
        if "key_differences" in blog_json and isinstance(blog_json["key_differences"], list):
            old_key_differences = blog_json["key_differences"]
            new_key_differences = {
                "heading": f"Key Differences Between {term_a} and {term_b}",
                "items": []
            }
            
            for diff in old_key_differences:
                if isinstance(diff, dict) and "title" in diff and "description" in diff:
                    # Split the description to use half for each term
                    description_text = ""
                    if isinstance(diff["description"], list):
                        for para in diff["description"]:
                            if isinstance(para, dict) and "text" in para:
                                description_text += para["text"] + " "
                            elif isinstance(para, str):
                                description_text += para + " "
                    
                    # Basic split of content for demo purposes
                    words = description_text.split()
                    midpoint = len(words) // 2
                    a_description = " ".join(words[:midpoint])
                    b_description = " ".join(words[midpoint:])
                    
                    new_key_differences["items"].append({
                        "feature_title": diff["title"],
                        "a_description": a_description,
                        "b_description": b_description
                    })
            
            blog_json["key_differences"] = new_key_differences
        
        # Ensure comparison_table is formatted correctly
        if "comparison_table" not in blog_json:
            blog_json["comparison_table"] = {
                "heading": f"{term_a} vs {term_b} Comparison",
                "features": [],
                "ideal_for": {
                    "a": f"{term_a} is ideal for long-term investors and those seeking store of value.",
                    "b": f"{term_b} is ideal for developers and those interested in smart contracts."
                }
            }
            
        # Convert old comparison_table format if present
        if "comparison_table" in blog_json and "rows" in blog_json["comparison_table"]:
            old_table = blog_json["comparison_table"]
            new_table = {
                "heading": f"{term_a} vs {term_b} Comparison",
                "features": [],
                "ideal_for": {
                    "a": f"{term_a} is ideal for long-term investors and those seeking store of value.",
                    "b": f"{term_b} is ideal for developers and those interested in smart contracts."
                }
            }
            
            if "rows" in old_table and isinstance(old_table["rows"], list):
                for row in old_table["rows"]:
                    if isinstance(row, dict) and "category" in row:
                        new_table["features"].append({
                            "label": row.get("category", ""),
                            "a_value": row.get(term_a, ""),
                            "b_value": row.get(term_b, "")
                        })
            
            blog_json["comparison_table"] = new_table
        
        # Ensure conclusion is formatted correctly
        if "conclusion" not in blog_json:
            blog_json["conclusion"] = {
                "heading": f"Conclusion: {term_a} vs {term_b}",
                "summary_paragraphs": []
            }
            
        # Convert old summary_paragraphs to conclusion format if present
        if "summary_paragraphs" in blog_json and isinstance(blog_json["summary_paragraphs"], list):
            conclusion_paragraphs = []
            
            for para in blog_json["summary_paragraphs"]:
                if isinstance(para, dict) and "text" in para:
                    conclusion_paragraphs.append({"text": para["text"]})
                elif isinstance(para, str):
                    conclusion_paragraphs.append({"text": para})
            
            blog_json["conclusion"] = {
                "heading": f"Conclusion: {term_a} vs {term_b}",
                "summary_paragraphs": conclusion_paragraphs
            }
            
            # Remove old summary_paragraphs
            if "summary_paragraphs" in blog_json:
                del blog_json["summary_paragraphs"]
        
        # Ensure term_a and term_b are set in the final structure
        blog_json["term_a"] = term_a
        blog_json["term_b"] = term_b
        
        # Remove word_count and read_time_minutes if present (as they are now calculated separately)
        if "word_count" in blog_json:
            del blog_json["word_count"]
        if "read_time_minutes" in blog_json:
            del blog_json["read_time_minutes"]
        
        return blog_json
    
    def _calculate_word_count(self, blog_post: Dict[str, Any]) -> int:
        """
        Calculate the total word count of the blog post.
        
        Args:
            blog_post: The blog post data
            
        Returns:
            The total word count
        """
        word_count = 0
        
        # Extract text from all sections
        all_text = self._extract_blog_text_content(blog_post)
        
        # Count words in the extracted text
        word_count = len(all_text.split())
        
        logger.info(f"Blog post word count: {word_count}")
        return word_count
    
    def _extract_blog_text_content(self, blog_post: Dict[str, Any]) -> str:
        """
        Extract all text content from the blog post.
        
        Args:
            blog_post: The blog post data
            
        Returns:
            A string containing all text content
        """
        all_text = ""
        
        # Title
        if "title" in blog_post:
            all_text += blog_post["title"] + " "
            
        # Introduction paragraphs
        if "introduction_paragraphs" in blog_post:
            all_text += self._extract_content_text(blog_post["introduction_paragraphs"])
            
        # Background section
        if "background" in blog_post and "content" in blog_post["background"]:
            all_text += blog_post["background"]["content"] + " "
            
        # Key differences
        if "key_differences" in blog_post and "items" in blog_post["key_differences"]:
            for diff in blog_post["key_differences"]["items"]:
                if "feature_title" in diff:
                    all_text += diff["feature_title"] + " "
                if "a_description" in diff:
                    all_text += diff["a_description"] + " "
                if "b_description" in diff:
                    all_text += diff["b_description"] + " "
                    
        # Comparison table
        if "comparison_table" in blog_post and "features" in blog_post["comparison_table"]:
            for feature in blog_post["comparison_table"]["features"]:
                if "label" in feature:
                    all_text += feature["label"] + " "
                if "a_value" in feature:
                    all_text += feature["a_value"] + " "
                if "b_value" in feature:
                    all_text += feature["b_value"] + " "
                    
            # Also count ideal_for text
            if "ideal_for" in blog_post["comparison_table"]:
                ideal_for = blog_post["comparison_table"]["ideal_for"]
                if "a" in ideal_for:
                    all_text += ideal_for["a"] + " "
                if "b" in ideal_for:
                    all_text += ideal_for["b"] + " "
                    
        # Conclusion
        if "conclusion" in blog_post and "summary_paragraphs" in blog_post["conclusion"]:
            all_text += self._extract_content_text(blog_post["conclusion"]["summary_paragraphs"])
            
        return all_text
    
    def _extract_content_text(self, content_list: List[Dict[str, str]]) -> str:
        """
        Extract text from a list of content objects.
        
        Args:
            content_list: A list of content objects with 'text' keys
            
        Returns:
            A string with all text content
        """
        text = ""
        for item in content_list:
            if isinstance(item, dict) and "text" in item:
                text += item["text"] + " "
            elif isinstance(item, str):
                text += item + " "
        return text
    
    def _calculate_read_time(self, word_count: int) -> int:
        """
        Calculate the estimated read time in minutes.
        
        Args:
            word_count: The total word count
            
        Returns:
            The estimated read time in minutes
        """
        # Average reading speed (words per minute)
        wpm = 238
        read_time = math.ceil(word_count / wpm)
        
        # Minimum read time is 1 minute
        read_time = max(1, read_time)
        
        logger.info(f"Estimated read time: {read_time} minutes")
        return read_time
    
    def _create_slug(self, text: str) -> str:
        """
        Create a URL-friendly slug from text.
        
        Args:
            text: The text to convert to a slug
            
        Returns:
            A URL-friendly slug
        """
        # Convert to lowercase
        slug = text.lower()
        
        # Replace spaces with hyphens
        slug = slug.replace(" ", "-")
        
        # Remove special characters
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        # Remove multiple hyphens
        slug = re.sub(r'-+', '-', slug)
        
        return slug
    
    def _validate_blog_post_schema(self, blog_post: Dict[str, Any]) -> None:
        """
        Validate the structure of the blog post.
        
        Args:
            blog_post: The blog post data to validate
        """
        # Check required fields
        required_fields = [
            "title", "slug", "published_date", "read_time", "author",
            "media", "introduction_paragraphs", "jump_link_text",
            "background", "key_differences", "comparison_table", "conclusion"
        ]
        
        for field in required_fields:
            if field not in blog_post:
                logger.warning(f"Missing required field: {field}")
                
        # Check list lengths
        if "introduction_paragraphs" in blog_post:
            if len(blog_post["introduction_paragraphs"]) < 2:
                logger.warning("Less than 2 introduction paragraphs")
                
        # Check key_differences items
        if "key_differences" in blog_post and "items" in blog_post["key_differences"]:
            if len(blog_post["key_differences"]["items"]) < 5:
                logger.warning("Less than 5 key differences")
                
        # Check comparison table features
        if "comparison_table" in blog_post and "features" in blog_post["comparison_table"]:
            if len(blog_post["comparison_table"]["features"]) < 5:
                logger.warning("Less than 5 features in comparison table")
                
        # Check conclusion paragraphs
        if "conclusion" in blog_post and "summary_paragraphs" in blog_post["conclusion"]:
            if len(blog_post["conclusion"]["summary_paragraphs"]) < 3:
                logger.warning("Less than 3 conclusion paragraphs")
    
    def _log_blog_activity(self, term_a: str, term_b: str, success: bool, content: str) -> None:
        """
        Log the blog generation activity.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            success: Whether the generation was successful
            content: The content to log
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_path / f"blog_{term_a}_vs_{term_b}_{timestamp}.json"
        
        log_data = {
            "timestamp": timestamp,
            "term_a": term_a,
            "term_b": term_b,
            "success": success,
            "content": content
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
            
        logger.info(f"Blog activity logged to {log_file}") 