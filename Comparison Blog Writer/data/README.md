# Data Directory

This directory contains the input data for the blog generation system.

## Files

### crypto_comparison_pairs_cleaned.csv
This file contains the search terms for crypto comparison articles.

#### Structure
The CSV file contains pairs of cryptocurrencies or concepts to compare, which will be used to generate comparison blog posts.

#### Usage
- Used by the content generator agent to create comparison articles
- Each row represents a potential blog topic
- The data is processed to generate SEO-optimized comparison content

#### Processing
The data is processed in the following steps:
1. CSV is read and validated
2. Each pair is transformed into a blog topic
3. Content is generated using the comparison pairs
4. Output is saved in JSON format in the /Users/austin/Desktop/All Coding Projects/openai-agents-python-moso-bloggin-agent/Austin's AI Agent Teams/programmatic_blog_generator/src/agents/comparison_agent/blogs directory

## Data Validation
- CSV format is validated on load
- Empty or invalid rows are logged and skipped
- Data is sanitized before processing

## Updates
When the CSV file is updated:
1. The new data is automatically detected
2. New comparison pairs are processed
3. Existing content is preserved
4. New blog posts are generated 