import requests
from flask import Flask
from flask_restplus import Api, Resource, reqparse
import subprocess
import os

app = Flask(__name__)
api = Api(app)

# Request parsers
create_project_parser = reqparse.RequestParser()
create_project_parser.add_argument('bitbucket_cloud_workspace', type=str, required=True, help='Workspace name')
create_project_parser.add_argument('bitbucket_cloud_username', type=str, required=True, help='Bitbucket Cloud username')
create_project_parser.add_argument('bitbucket_cloud_password', type=str, required=True, help='Bitbucket Cloud password')
create_project_parser.add_argument('bitbucket_cloud_url', type=str, required=True, help='Bitbucket Cloud API URL')

parser = reqparse.RequestParser()
parser.add_argument('BITBUCKET_URL', type=str, required=True)
parser.add_argument('BITBUCKET_TOKEN', type=str, required=True)

@api.route('/create')
class BitbucketCloudMirror(Resource):
    @api.expect(create_project_parser, parser)
    def post(self):
        """move projects, repositories, and files from a source Bitbucket to Bitbucket Cloud"""

        args = create_project_parser.parse_args()
        parser_args = parser.parse_args()
        args.update(parser_args)
        workspace = args['bitbucket_cloud_workspace']
        username = args['bitbucket_cloud_username']
        password = args['bitbucket_cloud_password']
        bitbucket_url = args['bitbucket_cloud_url']
        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }

        # Retrieve a list of projects from the source Bitbucket instance
        response = requests.get(f'{BITBUCKET_URL}/rest/api/1.0/projects', headers=headers)
        source_projects_data = response.json()

        created_items = []

        for project in source_projects_data['values']:
            project_key = project['key']
            project_name = project['name']
            project_description = project.get('description', '')  # Use an empty string if description is not provided

            auth = (username, password)

            # Check if the project exists in Bitbucket Cloud
            project_exists_url = f"{bitbucket_url}/workspaces/{workspace}/projects/{project_key}"
            response = requests.get(project_exists_url, auth=auth)

            if response.status_code != 200:
                # Project doesn't exist, so create it
                project_create_url = f"{bitbucket_url}/workspaces/{workspace}/projects/"
                new_project_data = {
                    "name": project_name,
                    "key": project_key,
                    "description": project_description
                }

                response = requests.post(project_create_url, json=new_project_data, auth=auth)

                if response.status_code == 201:
                    created_items.append(f"Project: {project_name}")

            # Retrieve repositories from the source project
            source_repositories_url = f'{BITBUCKET_URL}/rest/api/1.0/projects/{project_key}/repos'
            response = requests.get(source_repositories_url, headers=headers)
            source_repositories_data = response.json()

            for repository in source_repositories_data['values']:
                repository_name = repository['name']
                repository_description = repository.get('description', '')
                public = repository['public']

                # Create a repository in Bitbucket Cloud (create the repository every time)
                repository_create_url = f"{bitbucket_url}/repositories/{workspace}/{repository_name}"
                new_repository_data = {
                    "scm": "git",
                    "project": {
                        "key": project_key
                    },
                    "is_private": not public,  # Invert the 'public' flag to set private repositories
                    "description": repository_description
                }

                response = requests.post(repository_create_url, json=new_repository_data, auth=auth)

                if response.status_code == 201:
                    created_items.append(f"Repository: {repository_name}")
                repo_name = repository_name
                local_repo_path = f'./{project_name}/{repo_name}'
                if not os.path.exists(local_repo_path):
                    os.makedirs(local_repo_path)

                # Clone the repository from the source Bitbucket instance
                clone_url = f'{BITBUCKET_URL}/scm/{project_key}/{repository_name}.git'
                print(clone_url)
                subprocess.run(['git', 'clone', clone_url, local_repo_path])
                # Push to Bitbucket Cloud using the git mirror command
                cloud_remote_url = f'https://Ambarishg1@bitbucket.org/{workspace}/{repository_name}.git'
                subprocess.run(['git', 'remote', 'add', 'cloud', cloud_remote_url], cwd=local_repo_path)
                print(cloud_remote_url)
                # Fetch and push the repository to Bitbucket Cloud
                subprocess.run(['git', 'fetch', '--all'], cwd=local_repo_path)
                subprocess.run(['git', 'push', '--mirror', 'cloud'], cwd=local_repo_path)

        if created_items:
            return {'message': 'New Bitbucket Cloud projects, repositories, and files moved successfully', 'created_items': created_items}, 201
        else:
            return {'message': 'No projects, repositories, or files were moved to Bitbucket Cloud'}, 204

if __name__ == '__main__':
    app.run(debug=True)
