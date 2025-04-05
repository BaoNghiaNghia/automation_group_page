import requests

# Set up your Claude API key (replace with your actual key)
api_key = "your-api-key-here"

def rewrite_paragraph_with_claude(paragraph):
    url = "https://api.anthropic.com/v1/complete"  # Endpoint for Claude's API
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"Rewrite the following paragraph in a different way: \n{paragraph}"

    data = {
        "model": "claude-v1",  # The model you want to use, could vary depending on available versions
        "prompt": prompt,
        "max_tokens": 500,  # Adjust based on the length of the output you need
        "temperature": 0.7,  # Adjust based on how creative or deterministic you want the output to be
        "top_p": 1.0,  # Optional, adjusts for diversity in responses
        "n": 1,  # How many responses you want
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    if response.status_code == 200:
        rewritten_paragraph = response_data["completion"].strip()
        return rewritten_paragraph
    else:
        return f"Error: {response_data.get('error', {}).get('message', 'Unknown error')}"

# Example usage
original_paragraph = "AI technology has seen tremendous growth in recent years. It is being used in various fields such as healthcare, finance, and education."

rewritten_paragraph = rewrite_paragraph_with_claude(original_paragraph)
print("Original Paragraph: \n", original_paragraph)
print("\nRewritten Paragraph: \n", rewritten_paragraph)
