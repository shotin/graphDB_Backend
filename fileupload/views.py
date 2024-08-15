import os
import tempfile
import requests
import json 
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedFile
from django.http import HttpResponse

# BLAZEGRAPH_URL = "http://192.168.0.181:9999/blazegraph"
def homepage(request):
    return HttpResponse("Welcome to the homepage!")
@csrf_exempt
def get_files(request):
    files = UploadedFile.objects.all().values('name', 'graph_id', 'size', 'id')
    file_list = list(files)
    return JsonResponse({'files': file_list})

@csrf_exempt
def create_database(request):
    if request.method == 'POST':
        data = request.POST
        namespace = data.get('namespace')
        properties = {
            'com.bigdata.rdf.store.DataLoader': 'com.bigdata.rdf.data.RDFDataLoader',
            'com.bigdata.rdf.store.DataLoader.context': 'com.bigdata.rdf.data.RDFDataLoaderContext',
            'com.bigdata.rdf.sail.isolates': 'true',
            'com.bigdata.rdf.sail.quads': 'true',
            'com.bigdata.rdf.sail.axioms': 'true',
            'com.bigdata.rdf.sail.includeInferred': 'true',
            'com.bigdata.rdf.sail.incremental': 'false',
        }

        url = f'http://192.168.0.181:9999/blazegraph/{namespace}'
        response = requests.post(url, json={'properties': properties})

        if response.status_code == 200:
            return JsonResponse({'message': 'Database created successfully'})
        else:
            return JsonResponse({'error': 'Failed to create database'})

    return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def create_namespace(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            namespace = data.get('namespace')
            
            if not namespace:
                return JsonResponse({"error": "Namespace name is required."}, status=400)
            
            # Define headers and data
            headers = {"Content-Type": "application/json"}
            data = {
                "properties": {
                    "com.bigdata.rdf.store.DataLoader": "com.bigdata.rdf.data.RDFDataLoader",
                    "com.bigdata.rdf.store.DataLoader.context": "com.bigdata.rdf.data.RDFDataLoaderContext",
                    "com.bigdata.rdf.sail.isolates": "true",
                    "com.bigdata.rdf.sail.quads": "true",
                    "com.bigdata.rdf.sail.axioms": "true",
                    "com.bigdata.rdf.sail.includeInferred": "true",
                    "com.bigdata.rdf.sail.incremental": "false"
                }
            }
            
            url = f"http://192.168.0.181:9999/blazegraph/namespace/{namespace}"

            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return JsonResponse({"message": f"Namespace '{namespace}' created successfully."})
            else:
                return JsonResponse({"error": f"Failed to create namespace. Status code: {response.status_code}, Response: {response.text}"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except requests.RequestException as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def upload_ttl(request):
    if request.method == 'POST':
        graph_id = request.POST.get('graph_id')
        ttl_file = request.FILES['file']
        size = ttl_file.size  # Get file size from the file object

        try:
            # Save file data to database
            UploadedFile.objects.create(
                name=ttl_file.name,
                graph_id=graph_id,
                size=size,
                )

       
            url = f"http://127.0.0.1:8000/api/"
            headers = {"Content-Type": "text/turtle"}

            response = requests.post(url, headers=headers, data=ttl_file.read())
            if response.status_code == 200:
                return JsonResponse({"message": f"File '{ttl_file.name}' uploaded successfully."})
            else:
                return JsonResponse({"error": f"Failed to upload file. Status code: {response.status_code}"})
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"})
    return JsonResponse({"error": "Invalid request method."}, status=405)
    z@csrf_exempt
@csrf_exempt
def connect_database(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip_address = data.get('ipAddress')
            port = data.get('port')
            database_type = data.get('databaseType')

            if not ip_address or not port or not database_type:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            url = f"http://{ip_address}:{port}/blazegraph/namespace/{database_type}/sparql"
            response = requests.get(url)

            if response.status_code == 200:
                return JsonResponse({"success": True, "message": "Connected successfully"})
            else:
                return JsonResponse({"success": False, "message": "Failed to connect"}, status=response.status_code)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
@csrf_exempt
def get_active_database(request):
    if request.method == 'GET':
        try:
            url = "http://192.168.0.181:9999/blazegraph/namespace"
            response = requests.get(url)
            data = response.json()
            active_databases = [namespace for namespace in data if namespace['isDefault']]
            if active_databases:
                active_database = active_databases[0]
                return JsonResponse({'active_database': active_database})
            else:
                return JsonResponse({"message": "No active database found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": "Failed to fetch active database"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def get_active_repository(request):
    if request.method == 'GET':
        try:
            url = "http://192.168.0.181:9999/blazegraph/namespace"
            response = requests.get(url)
            data = response.json()
            active_repositories = [namespace for namespace in data if not namespace['isDefault']]
            if active_repositories:
                active_repository = active_repositories[0]
                return JsonResponse({'active_repository': active_repository})
            else:
                return JsonResponse({"message": "No active repository found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": "Failed to fetch active repository"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)