import json
from flask import Flask,request
from flask_restx import Api, Resource,reqparse,fields
import requests

app = Flask(__name__)
api = Api(app, version='1.0', title='Bitbucket API', description='Bitbucket API operations')

ns = api.namespace('Bitbucket', description='Bitbucket operations')

parser = reqparse.RequestParser()
parser.add_argument('BITBUCKET_URL', type=str, required=True)
parser.add_argument('BITBUCKET_TOKEN', type=str, required=False)
parser.add_argument('BITBUCKET_USERNAME', type=str, required=False, help='Bitbucket username')
parser.add_argument('BITBUCKET_PASSWORD', type=str, required=False, help='Bitbucket password')

project_model = api.model('Project', {
    'key': fields.String(required=True, description='Project key'),
    'name': fields.String(required=True, description='Project name'),
    'description': fields.String(required=False,description='Project description')
})
# Project_key = api.model('project', {
#     'key': fields.String(required=True)
# })

repo_model = api.model('Repository', {
    'name': fields.String(required=True, description='Repository name'),
    'public': fields.Boolean(required=False, description='Whether the repository is public'),
    'description': fields.String(required=False, description='Repository description')
})

@ns.route('/users')
class UserList(Resource):
    @api.doc('list_users')
    @api.expect(parser)
    def get(self):
        """List all Bitbucket users"""
        args = parser.parse_args()  # Parse the request parameters
        
        # Retrieve the values of BITBUCKET_URL and BITBUCKET_TOKEN from args
        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        response = requests.get(f'{BITBUCKET_URL}/users', 
                                headers=headers)

        if response.status_code == 200:
            try:
                response_data = response.json()
                
                return response_data, 200
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {str(e)}"}, 500
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}, 500

@ns.route('/projects')
class ProjectList(Resource):
    @api.doc('list_projects')
    @api.expect(parser)
    def get(self):
        """List all Bitbucket projects"""
        args = parser.parse_args()  

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        all_projects_and_repos = []

        response = requests.get(f'{BITBUCKET_URL}/projects', 
                                headers=headers)
        projects_data = response.json()

        for project in projects_data['values']:
            project_key = project['key']

            # repositories_url = f'{BITBUCKET_URL}/projects/{project_key}/repos'
            response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}/repos',
                                     headers=headers)

            repositories_data = response.json()
            project_info = {
                'project_name': project['name'],
                'repositories': repositories_data['values']
            }
            all_projects_and_repos.append(project_info)
        return all_projects_and_repos

    @api.doc('create_project')
    @api.expect(parser,project_model)
    def post(self):
        """Create a new Bitbucket project"""
        args = parser.parse_args() 
        
        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_USERNAME = args['BITBUCKET_USERNAME']
        BITBUCKET_PASSWORD = args['BITBUCKET_PASSWORD']
        data = request.json
        
        payload = {
                'key': data['key'],
                'name': data['name'],
                'description': data['description']
            }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        try:
            response = requests.post(f'{BITBUCKET_URL}/projects', 
                                     headers=headers, 
                                     json=payload,
                                     auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))

            if response.status_code == 201:
                response_data = response.json()
                return response_data, 201
            else:
                return {"error": f"Request failed with status code: {response.status_code}"}, 500
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}, 500

        
@ns.route('/project/<project_key>')
class Project(Resource):
    @api.doc('get_project')
    @api.expect(parser)
    def get(self, project_key):
        """Get a specific Bitbucket project by project key"""
        args = parser.parse_args()  

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}', 
                                headers=headers)

        if response.status_code == 200:
            try:
                response_data = response.json()
                
                return response_data, 200
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {str(e)}"}, 500
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}, 500
    
    @api.doc('delete_project')
    @api.expect(parser)
    def delete(self, project_key):
        """Delete a Bitbucket project by project key"""
        args = parser.parse_args()

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        BITBUCKET_USERNAME = args['BITBUCKET_USERNAME']
        BITBUCKET_PASSWORD = args['BITBUCKET_PASSWORD']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}',
            'Accept': 'application/json'
        }
        try:
            # Check if the project exists before deleting
            check_response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}', 
                                          headers=headers)

            if check_response.status_code == 200:
                # Project exists, proceed to delete
                delete_response = requests.delete(f'{BITBUCKET_URL}/projects/{project_key}', 
                                                  headers=headers,
                                                  auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))

                if delete_response.status_code == 204:
                    return {"message": "Project deleted successfully"}, 204
                else:
                    return {"error": f"Failed to delete project with status code: {delete_response.status_code}"}, 500
            elif check_response.status_code == 404:
                return {"error": f"Project with key {project_key} not found"}, 404
            else:
                return {"error": f"Failed to check project existence with status code: {check_response.status_code}"}, 500
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}, 500
    
    @api.doc('update_project')
    @api.expect(parser, project_model)
    def put(self, project_key):
        """Update a Bitbucket project by project key"""
        args = parser.parse_args()

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_USERNAME = args['BITBUCKET_USERNAME']
        BITBUCKET_PASSWORD = args['BITBUCKET_PASSWORD']
        data = request.json

        project_data = {
            'key': project_key,  # Use the provided project key in the URL
            'name': data.get('name'),
            'description': data.get('description')
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        try:
            # Update the project using the provided project key
            update_response = requests.put(f'{BITBUCKET_URL}/projects/{project_key}', 
                                           headers=headers, 
                                           json=project_data, 
                                           auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))

            if update_response.status_code == 200:
                updated_data = update_response.json()
                return updated_data, 200
            else:
                return {"error": f"Failed to update project with status code: {update_response.status_code}"}, 500
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}, 500



@ns.route('/project/<project_key>/repos')
class ProjectRepos(Resource):
    @api.doc('list_project_repos')
    @api.expect(parser)
    def get(self, project_key):
        """List repositories of a specific Bitbucket project by project key"""
        args = parser.parse_args() 

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}/repos', headers=headers)
        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data, 200
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {str(e)}"}, 500
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}, 500
        
    @api.doc('create_repo')
    @api.expect(parser,repo_model)
    def post(self, project_key):
        """Create a Bitbucket repository in a specific project by project key"""
        args = parser.parse_args() 
        data =request.json
        
        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_USERNAME = args['BITBUCKET_USERNAME']
        BITBUCKET_PASSWORD = args['BITBUCKET_PASSWORD']

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        repo_data = {
        "name": data['name'], 
        "public": data['public'], 
        "description": data['description'] 
    }
        response = requests.post(f'{BITBUCKET_URL}/projects/{project_key}/repos',
                                 headers=headers, 
                                 json=repo_data,
                                 auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))
        
        if response.status_code == 201:  # 201 indicates the resource was created.
            try:
                response_data = response.json()
                return response_data, 201
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {str(e)}"}, 500
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}, 500
        
@ns.route('/project/<project_key>/repos/<repositorySlug>')
class ProjectRepo(Resource):
    @api.doc('delete_repo')
    @api.expect(parser)
    def delete(self,project_key,repositorySlug):
        args = parser.parse_args()
        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_USERNAME = args['BITBUCKET_USERNAME']
        BITBUCKET_PASSWORD = args['BITBUCKET_PASSWORD']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}/repos/{repositorySlug}', 
                                headers=headers, 
                                auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))

        if response.status_code == 200:
            # Repository exists, proceed with deletion
            response = requests.delete(f'{BITBUCKET_URL}/projects/{project_key}/repos/{repositorySlug}', 
                                       headers=headers, 
                                       auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD))
            
            if response.status_code == 204:  # 204 indicates a successful deletion.
                return {"message": "Repository deleted successfully"}, 204
            else:
                return {"error": f"Failed to delete the repository with status code: {response.status_code}"}, 500
        elif response.status_code == 404:
            # Repository does not exist
            return {"message": "Repository does not exist"}, 404
        else:
            return {"error": f"Request to check repository existence failed with status code: {response.status_code}"}, 500
        
@ns.route('/projects/<project_key>/permissions/users')
class ProjectUsers(Resource):
    @api.doc('list_project_users')
    @api.expect(parser)
    def get(self, project_key):
        """List users of a specific Bitbucket project by project key"""
        args = parser.parse_args() 

        BITBUCKET_URL = args['BITBUCKET_URL']
        BITBUCKET_TOKEN = args['BITBUCKET_TOKEN']
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {BITBUCKET_TOKEN}'
        }
        response = requests.get(f'{BITBUCKET_URL}/projects/{project_key}/permissions/users', headers=headers)
        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data, 200
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {str(e)}"}, 500
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}, 500

if __name__ == '__main__':
    app.run("0.0.0.0",5050,debug=True)
