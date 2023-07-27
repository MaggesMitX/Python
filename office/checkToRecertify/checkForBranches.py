import gitlab
import base64
import json
import time
import yaml
import csv

with open('../../config.json') as config_file:
    data = json.load(config_file)

URL = "https://gitlab.com"
CUSTOMER_GROUP_ID = data['Group_ID']
TOKEN = data['Auth_Token']
STAMP_START = "2020-01-01T00:00:00.000Z"  # "YYYY-MM-DDTHH:MM:SS.sssZ" Format
STAMP_END = "2023-07-20T00:00:00.000Z"
TO_RECTIFY = "2023-04-05T00:00:00.000Z"  # Alles was älter ist, als der 4te April 23
PROJECT_ID = data['Project_ID']
FILE_PATH = "deploymentState.yml"
YAML_OLD = "deployment.yml_DEPRECATED"
FILTERED_PROJECTS = []


def connect_to_gitlab():
    return gitlab.Gitlab(URL, private_token=TOKEN, api_version="4")


def get_group_projects(gl, groupId):
    group = gl.groups.get(groupId)
    projects = group.projects.list(all=True)
    return projects


def show_groups():
    if not projects:
        print(f"No Repository in Group: '{CUSTOMER_GROUP_ID}' found.")
    else:
        print(f"Alle Repositorys list: '{CUSTOMER_GROUP_ID}':")
        c = 0
        for project in projects:
            print(f"{project.id}: {project.name}")
            c += 1
        return print(f"Numbers of projects:{c}")


def filter_by_creation(projects, start_date, end_date):
    filtered_projects = FILTERED_PROJECTS
    for project in projects:
        created_at = project.created_at
        if created_at and start_date <= created_at <= end_date:
            filtered_projects.append(project)
    print("\nfiltered projects:")
    c = 0
    for project in filtered_projects:
        print(f"{project.id}: {project.name}")
        c += 1
    return print(f"Numbers of filtered projects: {c}")


def print_formatted_list_of_dicts(list):
    for idx, dictionary in enumerate(list):
        print(f"Dictionary {idx + 1}:")
        for key, value in dictionary.items():
            print(f"    {key}: {value}")


def print_formatted_list(list):
    for idx, dictionary in enumerate(list):
        print(f"Dictionary {idx + 1}:")
        for key, value in dictionary.items():
            print(f"    {key}: {value}")
        print()


def export_to_csv(data_list):
    output_file = "customer_data.csv"
    fieldnames = ["projectId", "projectName", "Hostname new", "Hostname old", "excludedBranches"]

    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for item in data_list:
                writer.writerow(item)
        print("Data has been successfully written to customer_data.csv.")
    except Exception as e:
        print("The error occurred while writing the CSV file:", e)


def estimated_time_counter(current_item, total_items, start_time):
    elapsed_time = time.time() - start_time
    items_left = total_items - current_item
    estimated_time_remaining = (elapsed_time / current_item) * items_left
    print(
        f"Progress: {current_item}/{total_items} - Elapsed Time: {elapsed_time:.2f}s - Estimated Time Remaining: {estimated_time_remaining:.2f}s")


def check_file_in_project(project, file_path, branch):
    try:
        file = project.files.get(file_path=file_path, ref=branch)
        content = base64.b64decode(file.content).decode("utf-8")
        yaml_content = yaml.safe_load(content)

        if yaml_content is not None:
            print("File found in storage!")
            return yaml_content
    except gitlab.exceptions.GitlabGetError:
        return False


def process_project_files(project, branch_name):
    try:
        hostname = None
        hostname_old = None

        file_content = check_file_in_project(project, FILE_PATH, branch_name)
        file_content_old = check_file_in_project(project, YAML_OLD, branch_name)

        if file_content:
            print("A file has been found! : deploymentState.yml")
            hostname = file_content['configuration']['hostname']

            if hostname == 'ta.kampf.de':
                print("Alright! The data 'deploymentState.yml' is in : ", hostname)
            else:
                print("value ta.kampf.de ist not in: ", hostname)

        if file_content_old:
            print("A file has been found! : deployment.yml_DEPRECATED")
            print(file_content_old['hostname'])
            hostname_old = file_content_old['hostname']

            if hostname_old == 'ta.kampf.de':
                print("Alright! The data 'deployment.yml_DEPRECATED' is in: ", hostname_old)
            else:
                print("value ta.kampf.de ist not in:", hostname_old)

        if hostname is None or hostname_old is None:
            print("One or both files not found, or no matching hostnames in the repository.")
        return hostname, hostname_old


    except Exception as e:
        print(f"Error: {e}", " ", project.name)
        return None, None


def filterBranch_backup(project):
    excluded_branch_names = ["main", "master"]
    backup_substring = "Backup"

    branches = []
    for branch in project.branches.list():
        branch_name = branch.name

        if any(name in branch_name for name in excluded_branch_names):
            print(f"Project '{project.name}' contains the excluded branch name: '{branch_name}'")
            continue

        if backup_substring.lower() in branch_name.lower():
            print(f"Project '{project.name}' contains a branch with 'backup' in its name: '{branch_name}'")

        branches.append(branch_name)

    return branches


def filterBranch_all():
    excluded_branch_names = ["main", "master"]

    branches = []
    for branch in project.branches.list():
        branch_name = branch.name

        if branch_name not in excluded_branch_names:
            branches.append(branch_name)

    return branches


if __name__ == "__main__":

    try:
        connection = connect_to_gitlab()
        connection.auth()
        projects = get_group_projects(connection, CUSTOMER_GROUP_ID)
        customerList = []

        if projects:
            sTime = time.time()
            for idx, project_tmp in enumerate(projects):
                project_id = project_tmp.id
                project = connection.projects.get(project_id)
                print("Project", idx, "of", len(projects), ": ", project.name)

                excluded_branches = (project)
                if len(filterBranch_all()) > 0:
                    dict = {
                        "projectId": project_id,
                        "projectName": project.name,
                        "excludedBranches": excluded_branches
                    }
                    customerList.append(dict)
                    print_formatted_list(customerList)

            estimated_time_counter(idx + 1, len(projects), sTime)

        print_formatted_list(customerList)
        eTime = time.time()
        elapsed_time = eTime - sTime
        print(f"\nTotal time taken: {elapsed_time:.2f} seconds")
        export_to_csv(customerList)

    except Exception as e:
        print(f"Error: {e}")
