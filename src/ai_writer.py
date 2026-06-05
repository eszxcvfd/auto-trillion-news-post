import re
try:
    from google import genai
except ImportError:
    genai = None

def generate_ai_post(title: str, source: str, snippet: str, url: str, platform: str, config) -> str:
    if genai is None:
        print("[ERROR] google-genai is not installed. Please run pip install -r requirements.txt to install it.")
        raise ImportError("google-genai is not installed")
        
    if not config.ai_api_key:
        print("[ERROR] GEMINI_API_KEY is not set in environment variables or .env file.")
        raise ValueError("Missing GEMINI_API_KEY")
        
    # Define prompt template
    prompt = f"""You are a professional content writer.
Write a post for {platform} in English based on this news:

Title: {title}
Source: {source}
Summary: {snippet}
URL: {url}

Requirements:
1. Start with exactly 5 hashtags.
2. The first hashtag must be the main industry hashtag.
3. The other 4 hashtags must be relevant to the news.
4. Write in a professional business style.
5. Mention the trillion-dollar opportunity clearly if relevant.
6. Add strategic insight, not just a summary.
7. Keep the post suitable for {platform}.
8. Do not invent specific facts not present in the title or summary.
9. End with exactly these fixed hashtags:
#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump

Output only the final post. Do not include markdown code block formatting (like ```) around the post.
"""

    client = genai.Client(api_key=config.ai_api_key)
    response = client.models.generate_content(
        model=config.ai_model,
        contents=prompt
    )
    
    post_content = response.text.strip()
    return post_content

def validate_generated_post(content: str, platform: str) -> bool:
    if not content:
        return False
        
    # Check for placeholders
    placeholders = ["{title}", "{source}", "{snippet}", "{url}"]
    for ph in placeholders:
        if ph in content:
            return False
            
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    if not lines:
        return False
        
    # X / Twitter has different validation rules
    if platform.lower() in ["x", "twitter"]:
        hashtags = re.findall(r'#\w+', content)
        return len(hashtags) >= 3
        
    # LinkedIn/Facebook rules
    # 1. Starts with hashtag line containing at least 5 hashtags
    first_line = lines[0]
    top_hashtags = re.findall(r'#\w+', first_line)
    if len(top_hashtags) < 5:
        return False
        
    # 2. Ends with the 5 fixed bottom hashtags
    last_line = lines[-1]
    required_bottom = ["#tahkfoundation", "#henryuniverses", "#usiran", "#ustariffs", "#trump"]
    
    last_line_lower = last_line.lower()
    for bh in required_bottom:
        if bh not in last_line_lower:
            return False
            
    return True
