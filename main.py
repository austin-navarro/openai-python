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
        
        # Calculate word count if not present in blog_data
        word_count = blog_writer._calculate_word_count(blog_data) if 'word_count' not in blog_data else blog_data.get('word_count', 0)
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