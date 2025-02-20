import os
import requests
from openai import OpenAI

client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"OpenAI API key found: {api_key[:5]}...")
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except:
    print("Warning: OpenAI API key not set. Some features will be limited.")
import json

# Set up your OpenAI API key (ensure it's in your environment variables)

def fetch_repo_contents(owner, repo, path=''):
    """Recursively fetch all files and directories in the repository."""
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(contents_url)
    if r.status_code != 200:
        return []
    
    contents = r.json()
    all_contents = []
    
    if not isinstance(contents, list):
        contents = [contents]
    
    for item in contents:
        if item['type'] == 'dir':
            # Recursively fetch directory contents
            all_contents.extend(fetch_repo_contents(owner, repo, item['path']))
        elif item['type'] == 'file':
            # Get file content
            file_content = requests.get(item['download_url']).text
            all_contents.append({
                'path': item['path'],
                'type': 'file',
                'content': file_content,
                'size': item['size']
            })
    return all_contents

def fetch_repo_metadata(repo_url):
    """Parses the GitHub repository URL and fetches complete repository data."""
    try:
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        owner = parts[-2]
        repo = parts[-1]
    except Exception as e:
        print("Error parsing repo URL:", e)
        return None

    # Fetch basic metadata
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api_url)
    if r.status_code == 200:
        metadata = r.json()
    else:
        print("Error fetching repo metadata:", r.status_code)
        return None

    # Fetch README
    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
    r2 = requests.get(readme_url)
    if r2.status_code == 200:
        metadata['readme'] = r2.text
    else:
        metadata['readme'] = "No README found."

    # Fetch all repository contents
    metadata['contents'] = fetch_repo_contents(owner, repo)
    
    return metadata

# --- Define Prompt Functions ---

def call_llm(prompt_text, model="gpt-4-turbo-preview"):
    """
    Calls the OpenAI LLM with the provided prompt and returns the response.
    Available models include:
    - gpt-4-turbo-preview (recommended for best results)
    - gpt-4
    - gpt-3.5-turbo
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("LLM call error:", e)
        return ""

def format_file_contents(contents):
    """Format repository contents for the prompt."""
    files_summary = []
    for item in contents:
        if len(item['content']) > 1000:
            # Truncate large files
            content = item['content'][:1000] + "\n... (content truncated)"
        else:
            content = item['content']
        files_summary.append(f"File: {item['path']}\nContent:\n{content}\n---")
    return "\n".join(files_summary)

def prompt_overview(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Please provide a highly detailed, technically comprehensive overview of the following GitHub project.
Project Metadata:
Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}

Repository Contents:
{format_file_contents(metadata.get('contents', []))}

List the project's purpose, problem statement, core features, key technologies, and any unique aspects.
Focus on the actual implementation details visible in the code.
"""
    return call_llm(prompt, model)

def prompt_technical_analysis(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Based on the project details and code below, please conduct a deep technical analysis:
Project Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}

Repository Contents:
{format_file_contents(metadata.get('contents', []))}

Please analyze:
1. Architecture and design patterns used in the code
2. Key algorithms and their implementation
3. Dependencies and their usage
4. Code organization and structure
5. Potential technical challenges or limitations
"""
    return call_llm(prompt, model)

def prompt_actionable_insights(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Using the project information below, synthesize actionable insights and potential enhancements:
Project Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}

Provide detailed suggestions for improvements, potential integrations, and innovative ideas.
"""
    return call_llm(prompt, model)

def prompt_metadata_analysis(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Extract and summarize the following metadata and contextual information about the project:
Project Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
License: {metadata.get('license', {}).get('name', 'Not specified')}
Owner: {metadata.get('owner', {}).get('login', 'Not specified')}
README:
{metadata.get('readme', 'N/A')}

Include community activity and project maturity if available.
"""
    return call_llm(prompt, model)

def prompt_tagging_framework(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Generate a comprehensive tagging framework for the GitHub project described below.
Output a JSON object with the following keys: "Technical_Tags", "Domain_and_Purpose", "Complexity_and_Maturity", "Unique_Features", "Potential_Applications".
Project Details:
Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}
"""
    return call_llm(prompt, model)

def prompt_creative_repurposing(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Based on the project details below, propose an entirely new, innovative project concept that repurposes the original technology.
Include a new project name, a comprehensive concept overview, unique value proposition, innovative features, and potential impact.
Project Details:
Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}
"""
    return call_llm(prompt, model)

def prompt_speculative_integration(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Imagine an integration of the project described below with an emerging technology (e.g., blockchain, AR/VR, IoT).
Detail the following:
- The chosen emerging technology.
- An innovative use case enabled by this integration.
- Potential technical challenges and solutions.
- Future impact.
Project Details:
Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}
"""
    return call_llm(prompt, model)

def prompt_cross_disciplinary_innovation(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Using the project information below, design a cross-disciplinary innovation that applies its strengths to a completely different field (e.g., healthcare, education, art).
Include:
- A unique project name.
- A detailed description of the new application.
- How the original technical components can be adapted.
- Potential collaboration opportunities between disciplines.
Project Details:
Name: {metadata.get('name', 'N/A')}
Description: {metadata.get('description', 'N/A')}
README:
{metadata.get('readme', 'N/A')}
"""
    return call_llm(prompt, model)

def prompt_dependency_analysis(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Analyze the dependencies and imports in this codebase:
Repository Contents:
{format_file_contents(metadata.get('contents', []))}

Please provide:
1. List of all external dependencies and their purposes
2. Key internal module relationships and dependencies
3. Potential dependency conflicts or version requirements
4. Suggestions for dependency optimization
"""
    return call_llm(prompt, model)

def prompt_code_quality(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Review the code quality of this project:
Repository Contents:
{format_file_contents(metadata.get('contents', []))}

Please analyze:
1. Code organization and modularity
2. Error handling and edge cases
3. Documentation and code comments
4. Potential code smells or anti-patterns
5. Specific suggestions for code improvements
"""
    return call_llm(prompt, model)

def prompt_security_review(metadata, model="gpt-4-turbo-preview"):
    prompt = f"""Conduct a security review of this codebase:
Repository Contents:
{format_file_contents(metadata.get('contents', []))}

Please identify:
1. Potential security vulnerabilities
2. Unsafe data handling practices
3. Authentication/authorization concerns
4. Input validation issues
5. Recommendations for security improvements
"""
    return call_llm(prompt, model)

# --- Orchestrator ---

def main():
    repo_url = input("Enter the GitHub repository URL: ").strip()
    metadata = fetch_repo_metadata(repo_url)
    if not metadata:
        print("Failed to fetch repository metadata.")
        return

    outputs = {}

    print("Processing overview prompt...")
    outputs["overview"] = prompt_overview(metadata)

    print("Processing technical analysis prompt...")
    outputs["technical_analysis"] = prompt_technical_analysis(metadata)

    print("Processing actionable insights prompt...")
    outputs["actionable_insights"] = prompt_actionable_insights(metadata)

    print("Processing metadata analysis prompt...")
    outputs["metadata_analysis"] = prompt_metadata_analysis(metadata)

    print("Processing tagging framework prompt...")
    outputs["tagging_framework"] = prompt_tagging_framework(metadata)

    print("Processing creative repurposing prompt...")
    outputs["creative_repurposing"] = prompt_creative_repurposing(metadata)

    print("Processing speculative integration prompt...")
    outputs["speculative_integration"] = prompt_speculative_integration(metadata)

    print("Processing cross-disciplinary innovation prompt...")
    outputs["cross_disciplinary_innovation"] = prompt_cross_disciplinary_innovation(metadata)

    print("Processing dependency analysis prompt...")
    outputs["dependency_analysis"] = prompt_dependency_analysis(metadata)

    print("Processing code quality prompt...")
    outputs["code_quality"] = prompt_code_quality(metadata)

    print("Processing security review prompt...")
    outputs["security_review"] = prompt_security_review(metadata)

    # Save the collected outputs to a JSON file
    with open("output.json", "w") as f:
        json.dump({"repo_url": repo_url, "outputs": outputs}, f, indent=2)
    print("All prompts processed. Output saved to output.json.")

if __name__ == "__main__":
    main()
