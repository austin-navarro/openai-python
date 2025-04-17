import os
import json
import csv
import random
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
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
            json.dump(blog_data, f, indent=2, ensure_ascii=False)
            
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
        # Create the basic prompt content
        prompt = """
You are an expert crypto content creator specializing in educational comparison blog posts.

Task: Create a detailed comparison blog post between {term_a} and {term_b}.

Audience: Crypto enthusiasts and investors seeking in-depth, technical comparisons.

Output Style:
- Objective and educational
- Get creative with the introduction paragraph and dont be generic
- Follows SEO best practices
- Uses markdown formatting for headings and clear readability
- Structured exactly to the JSON format provided below
- Total content should be roughly 1,300–1,500 words
- Don't be generic with the conclusion paragraphs either    

Content Length Guidelines:
| Section         | # of Paragraphs    | Sentences per Paragraph |
|-----------------|--------------------|-----------------------|
| Introduction    | 1                  | 5-7                   |
| Background      | 4-5                | 4-6                   |
| Key Differences | 5 items            | -                     |
| - feature_title | -                  | -                     |
| - a_description | 1 paragraph        | 4-5                   |
| - b_description | 1 paragraph        | 4-5                   |
| Comparison Table| 5-6 features       | Short bullet-style    |
| Ideal For       | 2 lines            | 1-2                   |
| Conclusion      | 2                  | 4-6                   |

JSON Schema Format:
Return the blog as a JSON object in this exact format:

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
    "term_a": "{term_a_lower}-comparison-blog",
    "term_b": "{term_b_lower}-comparison-blog"
  }},
  "introduction_paragraphs": [
    {{ "text": "A detailed single paragraph introducing the comparison between {term_a} and {term_b}, covering the main points that will be discussed in the blog." }}
  ],
  "jump_link_text": "Jump to {term_a} vs {term_b} Comparison",
  "background": {{
    "heading": "Understanding {term_a} and {term_b}",
    "paragraphs": [
      {{ "text": "Paragraph about {term_a} and {term_b}, containing 4-6 sentences." }},
      {{ "text": "Paragraph about {term_a} and {term_b}, containing 4-6 sentences." }},
      {{ "text": "Paragraph about {term_a} and {term_b}, containing 4-6 sentences." }},
      {{ "text": "Paragraph about {term_a} and {term_b}, containing 4-6 sentences." }}
    ]
  }},
  "key_differences": {{
    "heading": "Key Differences Between {term_a} and {term_b}",
    "items": [
      {{
        "feature_title": "string",
        "a_description": "One paragraph of 4–5 sentences describing {term_a}'s take on this feature.",
        "b_description": "One paragraph of 4–5 sentences describing {term_b}'s take on this feature."
      }}
    ]
  }},
  "comparison_table": {{
    "heading": "{term_a} vs {term_b} Comparison",
    "features": [
      {{
        "label": "Feature Name",
        "a_value": "Short value or stat for {term_a}",
        "b_value": "Short value or stat for {term_b}"
      }}
    ],
    "ideal_for": {{
      "a": "1–2 sentences describing who {term_a} is ideal for.",
      "b": "1–2 sentences describing who {term_b} is ideal for."
    }}
  }},
  "conclusion": {{
    "heading": "Conclusion: {term_a} vs {term_b}",
    "summary_paragraphs": [
      {{ "text": "First concluding paragraph summarizing the key differences between {term_a} and {term_b}." }},
      {{ "text": "Second concluding paragraph offering final thoughts and recommendations based on user needs." }}
    ]
  }}
}}

Use the following research to inform your comparison:

{research_context}
"""
        # Format the prompt with the terms
        formatted_prompt = prompt.format(
            term_a=term_a,
            term_b=term_b,
            term_a_lower=term_a.lower(),
            term_b_lower=term_b.lower(),
            research_context=research_context
        )
        
        return formatted_prompt
    
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
            
            # Build the API call with plain dictionaries to avoid any serialization issues
            response = self.client.responses.create(
                model="gpt-4.1-nano-2025-04-14",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "comparison_blog_generator",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The title of the comparison blog."
                                },
                                "slug": {
                                    "type": "string",
                                    "description": "The unique identifier for the blog post."
                                },
                                "published_date": {
                                    "type": "string",
                                    "description": "The date and time when the blog was published in ISO 8601 format."
                                },
                                "read_time": {
                                    "type": "string",
                                    "description": "Estimated time required to read the blog."
                                },
                                "author": {
                                    "type": "object",
                                    "description": "Information about the author of the blog.",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The name of the author."
                                        },
                                        "role": {
                                            "type": "string",
                                            "description": "The role of the author in relation to the blog topic."
                                        }
                                    },
                                    "required": [
                                        "name",
                                        "role"
                                    ],
                                    "additionalProperties": False
                                },
                                "media": {
                                    "type": "object",
                                    "description": "Media information related to the blog post.",
                                    "properties": {
                                        "term_a": {
                                            "type": "string",
                                            "description": f"Media term for {term_a}."
                                        },
                                        "term_b": {
                                            "type": "string",
                                            "description": f"Media term for {term_b}."
                                        }
                                    },
                                    "required": [
                                        "term_a",
                                        "term_b"
                                    ],
                                    "additionalProperties": False
                                },
                                "introduction_paragraphs": {
                                    "type": "array",
                                    "description": "A collection of paragraphs introducing the topic.",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {
                                                "type": "string",
                                                "description": "Text of the introduction paragraph."
                                            }
                                        },
                                        "required": [
                                            "text"
                                        ],
                                        "additionalProperties": False
                                    }
                                },
                                "jump_link_text": {
                                    "type": "string",
                                    "description": "Text for the jump link navigating to the comparison section."
                                },
                                "background": {
                                    "type": "object",
                                    "description": "Background information about the terms being compared.",
                                    "properties": {
                                        "heading": {
                                            "type": "string",
                                            "description": "Heading for the background section."
                                        },
                                        "paragraphs": {
                                            "type": "array",
                                            "description": "Background paragraphs explaining both terms.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "text": {
                                                        "type": "string",
                                                        "description": "Text of the background paragraph."
                                                    }
                                                },
                                                "required": [
                                                    "text"
                                                ],
                                                "additionalProperties": False
                                            }
                                        }
                                    },
                                    "required": [
                                        "heading",
                                        "paragraphs"
                                    ],
                                    "additionalProperties": False
                                },
                                "key_differences": {
                                    "type": "object",
                                    "description": "Details on key differences between the two terms.",
                                    "properties": {
                                        "heading": {
                                            "type": "string",
                                            "description": "Heading for the key differences section."
                                        },
                                        "items": {
                                            "type": "array",
                                            "description": "List of key differences.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "feature_title": {
                                                        "type": "string",
                                                        "description": "Title of the feature being compared."
                                                    },
                                                    "a_description": {
                                                        "type": "string",
                                                        "description": f"{term_a}'s description of the feature."
                                                    },
                                                    "b_description": {
                                                        "type": "string",
                                                        "description": f"{term_b}'s description of the feature."
                                                    }
                                                },
                                                "required": [
                                                    "feature_title",
                                                    "a_description",
                                                    "b_description"
                                                ],
                                                "additionalProperties": False
                                            }
                                        }
                                    },
                                    "required": [
                                        "heading",
                                        "items"
                                    ],
                                    "additionalProperties": False
                                },
                                "comparison_table": {
                                    "type": "object",
                                    "description": "Comparison table information.",
                                    "properties": {
                                        "heading": {
                                            "type": "string",
                                            "description": "Heading for the comparison table."
                                        },
                                        "features": {
                                            "type": "array",
                                            "description": "List of features being compared.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "label": {
                                                        "type": "string",
                                                        "description": "Feature name."
                                                    },
                                                    "a_value": {
                                                        "type": "string",
                                                        "description": f"Value for {term_a}."
                                                    },
                                                    "b_value": {
                                                        "type": "string",
                                                        "description": f"Value for {term_b}."
                                                    }
                                                },
                                                "required": [
                                                    "label",
                                                    "a_value",
                                                    "b_value"
                                                ],
                                                "additionalProperties": False
                                            }
                                        },
                                        "ideal_for": {
                                            "type": "object",
                                            "description": "Information about who each term is ideal for.",
                                            "properties": {
                                                "a": {
                                                    "type": "string",
                                                    "description": f"Description of the ideal audience for {term_a}."
                                                },
                                                "b": {
                                                    "type": "string",
                                                    "description": f"Description of the ideal audience for {term_b}."
                                                }
                                            },
                                            "required": [
                                                "a",
                                                "b"
                                            ],
                                            "additionalProperties": False
                                        }
                                    },
                                    "required": [
                                        "heading",
                                        "features",
                                        "ideal_for"
                                    ],
                                    "additionalProperties": False
                                },
                                "conclusion": {
                                    "type": "object",
                                    "description": "Conclusion section of the blog post.",
                                    "properties": {
                                        "heading": {
                                            "type": "string",
                                            "description": "Heading for the conclusion section."
                                        },
                                        "summary_paragraphs": {
                                            "type": "array",
                                            "description": "Final summary paragraphs.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "text": {
                                                        "type": "string",
                                                        "description": "Text of the conclusion paragraph."
                                                    }
                                                },
                                                "required": [
                                                    "text"
                                                ],
                                                "additionalProperties": False
                                            }
                                        }
                                    },
                                    "required": [
                                        "heading",
                                        "summary_paragraphs"
                                    ],
                                    "additionalProperties": False
                                }
                            },
                            "required": [
                                "title",
                                "slug",
                                "published_date",
                                "read_time",
                                "author",
                                "media",
                                "introduction_paragraphs",
                                "jump_link_text",
                                "background",
                                "key_differences",
                                "comparison_table",
                                "conclusion"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                reasoning={},
                tools=[],
                temperature=0.7,
                max_output_tokens=4000,
                top_p=1,
                store=True
            )
            
            # Extract JSON content from the response
            content = response.output_text
            
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
        If OpenAI's JSON response is already properly structured, this function 
        simply returns the content as is.
        
        Args:
            content: The JSON string to clean
            
        Returns:
            A cleaned JSON string
        """
        # With the improved JSON schema definition, we usually don't need cleaning
        # This simplified function is kept as a fallback mechanism only
        return content
    
    def _post_process_blog_json(self, blog_json: Dict[str, Any], term_a: str, term_b: str) -> Dict[str, Any]:
        """
        Post-process the blog JSON data to ensure consistent structure.
        
        Args:
            blog_json: The blog data to process
            term_a: The first asset term
            term_b: The second asset term
            
        Returns:
            The processed blog data
        """
        # Create a new ordered dictionary to control the field order
        ordered_blog = {}
        
        # Always use current date for published_date in ISO 8601 format
        blog_json["published_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Copy title and slug first if they exist
        if "title" in blog_json:
            ordered_blog["title"] = blog_json["title"]
        if "slug" in blog_json:
            ordered_blog["slug"] = blog_json["slug"]
        if "published_date" in blog_json:
            ordered_blog["published_date"] = blog_json["published_date"]
        if "read_time" in blog_json:
            ordered_blog["read_time"] = blog_json["read_time"]
        
        # Add author if it exists or create default
        if "author" in blog_json:
            ordered_blog["author"] = blog_json["author"]
        else:
            ordered_blog["author"] = {
                "name": "Moso Panda",
                "role": "Crypto Connoisseur"
            }
        
        # Add terms object between author and media
        ordered_blog["terms"] = {
            "term_a": term_a,
            "term_b": term_b
        }
        
        # Add media if it exists or create default
        if "media" in blog_json:
            ordered_blog["media"] = blog_json["media"]
        else:
            ordered_blog["media"] = {
                "term_a": f"{term_a.lower()}-comparison-blog",
                "term_b": f"{term_b.lower()}-comparison-blog"
            }
            
        # Ensure read_time is set
        if "read_time" not in ordered_blog:
            ordered_blog["read_time"] = "5 min read"
        
        # Copy remaining fields from the original blog_json
        for field in ["introduction_paragraphs", "jump_link_text", "background", 
                     "key_differences", "comparison_table", "conclusion"]:
            if field in blog_json:
                ordered_blog[field] = blog_json[field]
        
        # Ensure we have default values for essential sections
        if "jump_link_text" not in ordered_blog:
            ordered_blog["jump_link_text"] = f"Jump to {term_a} vs {term_b} Comparison"
        
        # Ensure introduction has only one paragraph (combine if multiple)
        if "introduction_paragraphs" in ordered_blog and isinstance(ordered_blog["introduction_paragraphs"], list):
            if len(ordered_blog["introduction_paragraphs"]) > 1:
                # Combine multiple paragraphs into one
                combined_text = " ".join([p.get("text", "") for p in ordered_blog["introduction_paragraphs"] if isinstance(p, dict) and "text" in p])
                ordered_blog["introduction_paragraphs"] = [{"text": combined_text}]
        
        # Ensure conclusion has only two paragraphs
        if "conclusion" in ordered_blog and "summary_paragraphs" in ordered_blog["conclusion"]:
            if isinstance(ordered_blog["conclusion"]["summary_paragraphs"], list):
                paragraphs = ordered_blog["conclusion"]["summary_paragraphs"]
                if len(paragraphs) > 2:
                    # Keep only the first two paragraphs
                    ordered_blog["conclusion"]["summary_paragraphs"] = paragraphs[:2]
                elif len(paragraphs) < 2:
                    # Generate default paragraphs if needed
                    defaults = self._generate_default_conclusion_paragraphs(term_a, term_b)
                    # Ensure we have exactly 2 paragraphs
                    while len(ordered_blog["conclusion"]["summary_paragraphs"]) < 2:
                        # Add default paragraphs if needed
                        if defaults:
                            ordered_blog["conclusion"]["summary_paragraphs"].append(defaults.pop(0))
                        else:
                            # Create a generic one if we ran out of defaults
                            ordered_blog["conclusion"]["summary_paragraphs"].append({
                                "text": f"Choosing between {term_a} and {term_b} ultimately depends on individual investment goals and preferences."
                            })
        
        # Return the processed blog JSON
        return ordered_blog
    
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
        
        # Jump link text
        if "jump_link_text" in blog_post:
            all_text += blog_post["jump_link_text"] + " "
            
        # Introduction paragraphs
        if "introduction_paragraphs" in blog_post:
            all_text += self._extract_content_text(blog_post["introduction_paragraphs"])
            
        # Background section
        if "background" in blog_post and "paragraphs" in blog_post["background"]:
            all_text += self._extract_content_text(blog_post["background"]["paragraphs"])
            
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
        wpm = 200  # Changed from 238 to 200
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
                
        # Check introduction paragraph
        if "introduction_paragraphs" in blog_post:
            if len(blog_post["introduction_paragraphs"]) != 1:
                logger.warning("Introduction should have exactly 1 paragraph")
                
        # Check background paragraphs
        if "background" in blog_post and "paragraphs" in blog_post["background"]:
            if len(blog_post["background"]["paragraphs"]) < 4:
                logger.warning("Less than 4 background paragraphs")
                
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
            if len(blog_post["conclusion"]["summary_paragraphs"]) != 2:
                logger.warning("Conclusion should have exactly 2 paragraphs")
    
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
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Blog activity logged to {log_file}")
    
    def _generate_default_conclusion_paragraphs(self, term_a: str, term_b: str) -> List[Dict[str, str]]:
        """
        Generate default conclusion paragraphs when none are provided.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            
        Returns:
            A list of paragraph objects with text keys
        """
        return [
            {"text": f"In conclusion, both {term_a} and {term_b} offer unique value propositions in the cryptocurrency ecosystem. While {term_a} excels in specific use cases, {term_b} has its own strengths that appeal to different user needs and preferences."},
            {"text": f"Investors and users should carefully consider their specific requirements and risk tolerance when choosing between {term_a} and {term_b}. The decision ultimately depends on individual goals, preferences, and the specific functionality needed."}
        ]

    def _generate_default_features(self, term_a: str, term_b: str) -> List[Dict[str, str]]:
        """
        Generate default features for the comparison table.
        
        Args:
            term_a: The first asset term
            term_b: The second asset term
            
        Returns:
            A list of default features
        """
        return [
            {
                "label": "Core Functionality",
                "a_value": f"{term_a} primary function",
                "b_value": f"{term_b} primary function"
            },
            {
                "label": "Technology",
                "a_value": f"{term_a} technology",
                "b_value": f"{term_b} technology"
            },
            {
                "label": "Use Cases",
                "a_value": f"{term_a} use cases",
                "b_value": f"{term_b} use cases"
            },
            {
                "label": "Security",
                "a_value": f"{term_a} security features",
                "b_value": f"{term_b} security features"
            },
            {
                "label": "Market Position",
                "a_value": f"{term_a} market stats",
                "b_value": f"{term_b} market stats"
            }
        ] 