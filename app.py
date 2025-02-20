from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from main import fetch_repo_metadata, prompt_overview, prompt_technical_analysis, prompt_actionable_insights, prompt_dependency_analysis, prompt_code_quality, prompt_security_review, client

app = Flask(__name__, static_folder='static')
CORS(app)

PROJECTS_DIR = 'projects'

# Ensure projects directory exists
os.makedirs(PROJECTS_DIR, exist_ok=True)

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/api/projects', methods=['GET'])
def list_projects():
    projects = []
    for project_dir in os.listdir(PROJECTS_DIR):
        project_path = os.path.join(PROJECTS_DIR, project_dir)
        if os.path.isdir(project_path):
            metadata_path = os.path.join(project_path, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    projects.append({
                        'id': project_dir,
                        'name': metadata.get('name', 'Unknown'),
                        'description': metadata.get('description', ''),
                        'url': metadata.get('html_url', '')
                    })
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json
        repo_url = data.get('repo_url')
        model = data.get('model', 'gpt-4-turbo-preview')  # Default to GPT-4 Turbo if not specified
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400

        # Fetch repository metadata
        metadata = fetch_repo_metadata(repo_url)
        if not metadata:
            return jsonify({'error': 'Failed to fetch repository metadata. Please check the URL and try again.'}), 400

        # Create project directory
        project_id = metadata['name'].lower().replace(' ', '_')
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)

        # Save metadata
        with open(os.path.join(project_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        # Generate analyses
        analyses = {
            'overview': 'OpenAI API key not set. Analysis not available.',
            'technical_analysis': 'OpenAI API key not set. Analysis not available.',
            'actionable_insights': 'OpenAI API key not set. Analysis not available.',
            'dependency_analysis': 'OpenAI API key not set. Analysis not available.',
            'code_quality': 'OpenAI API key not set. Analysis not available.',
            'security_review': 'OpenAI API key not set. Analysis not available.'
        }
        
        if client is not None:
            try:
                analyses = {
                    'overview': prompt_overview(metadata, model),
                    'technical_analysis': prompt_technical_analysis(metadata, model),
                    'actionable_insights': prompt_actionable_insights(metadata, model),
                    'dependency_analysis': prompt_dependency_analysis(metadata, model),
                    'code_quality': prompt_code_quality(metadata, model),
                    'security_review': prompt_security_review(metadata, model)
                }
            except Exception as e:
                print(f"Error generating analyses: {str(e)}")
                # Continue with default analyses if OpenAI calls fail

        # Save analyses
        with open(os.path.join(project_dir, 'analyses.json'), 'w') as f:
            json.dump(analyses, f, indent=2)

        return jsonify({
            'id': project_id,
            'name': metadata['name'],
            'description': metadata.get('description', ''),
            'url': metadata['html_url']
        })
    except Exception as e:
        print(f"Error in create_project: {str(e)}")
        return jsonify({'error': f'Failed to process repository: {str(e)}'}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.exists(project_dir):
        return jsonify({'error': 'Project not found'}), 404

    metadata_path = os.path.join(project_dir, 'metadata.json')
    analyses_path = os.path.join(project_dir, 'analyses.json')

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    with open(analyses_path, 'r') as f:
        analyses = json.load(f)

    return jsonify({
        'metadata': metadata,
        'analyses': analyses
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
