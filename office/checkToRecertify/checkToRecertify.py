import gitlab
import base64
import json
import time

with open('../../config.json') as config_file:
    data = json.load(config_file)

URL = "https://gitlab.com"
CUSTOMER_GROUP_ID = data['Group_ID']
TOKEN = data['Auth_Token']
STAMP_START = "2020-01-01T00:00:00.000Z"
STAMP_END = "2023-07-20T00:00:00.000Z"
TO_RECERTIFY = "2023-04-05T00:00:00.000Z"
PROJECT_ID = data['Project_ID']
FILE_PATH = "customerCA/serial"
FILTERED_PROJECTS = []


def connect_to_gitlab():
    return gitlab.Gitlab(URL, private_token=TOKEN, api_version="4")


def get_group_projects(gl, groupId):
    group = gl.groups.get(groupId)
    projects = group.projects.list(all=True)
    return projects


def show_groups():
    if not projects:
        print(f"Keine Repositories in der Gruppe '{CUSTOMER_GROUP_ID}' gefunden.")
    else:
        print(f"Alle Repositories in der Gruppe '{CUSTOMER_GROUP_ID}':")
        c = 0
        for project in projects:
            print(f"{project.id}: {project.name}")
            c += 1
        return print(f"Anzahl an Projekten:{c}")


def filter_by_creation(projects, start_date, end_date):
    filtered_projects = FILTERED_PROJECTS
    for project in projects:
        created_at = project.created_at
        if created_at and start_date <= created_at <= end_date:
            filtered_projects.append(project)
    print("\nGefilterte Projekte:")
    c = 0
    for project in filtered_projects:
        print(f"{project.id}: {project.name}")
        c += 1
    return print(f"Anzahl der gefilterten Projekte: {c}")


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


def estimated_time_counter(current_item, total_items, start_time):
    elapsed_time = time.time() - start_time
    items_left = total_items - current_item
    estimated_time_remaining = (elapsed_time / current_item) * items_left
    print(
        f"Progress: {current_item}/{total_items} - Elapsed Time: {elapsed_time:.2f}s - Estimated Time Remaining: {estimated_time_remaining:.2f}s")


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

                for branch in project.branches.list():
                    if branch.name == "master" or branch.name == "main":
                        branch_name = branch.name
                        break
                if branch_name != "master" and branch_name != "main":
                    print("No master or main branch found for project", project.name)
                    break

                try:
                    files = project.files.get(file_path=FILE_PATH, ref=branch_name)
                    file_content = base64.b64decode(files.content).decode("utf-8")
                except Exception as e:
                    print(f"Fehler: {e}", " ", project.name)
                else:

                    last_commit_id = files.last_commit_id
                    last_commit = project.commits.get(files.last_commit_id)
                    commit_date = last_commit.authored_date
                    commits_before_target_date = []

                    if commit_date < TO_RECERTIFY:
                        commits = project.commits.list(since=STAMP_START, get_all=True)
                        for commit in commits:
                            commit_date_attr = commit.attributes['committed_date']
                            commit_date = commit_date_attr
                            commits_before_target_date.append(commit)
                        dict = {
                            "projectId": project_id,
                            "projectName": project.name,
                            "last_commit_date": commit_date
                        }
                        customerList.append(dict)

                    estimated_time_counter(idx + 1, len(projects), sTime)

            print_formatted_list(customerList)
            eTime = time.time()
            elapsed_time = eTime - sTime
            print(f"\nTotal time taken: {elapsed_time:.2f} seconds")

    except Exception as e:
        print(f"Fehler: {e}")
