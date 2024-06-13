import json
import sys
import os
import time
import csv
import subprocess
from github import Github
from github import Auth

auth = Auth.Token(os.getenv("GHPAT"))
org_name = "Client-Org" #Replace with Client GitHub Org

def get_cloud_repos():
    try:
        print("Trying to authenticate with github...")
        g = Github(auth=auth)
        print("Authenticated!")

        # core_rate_limit = g.get_rate_limit().core
        # print("Rate limit: ", core_rate_limit)
        
        print("Trying to get repos from organization...")

        org = g.get_organization(org_name)
        org.login
	
        repos = []
        
        repo_count = 0
        
        for repo in org.get_repos():
            repo_count += 1
            print("REPO COUNT: ",repo_count)
            if repo_limit > 0 and repo_count > repo_limit: # This makes it so the repo list can provide a limited number of repositories rather than all repos 
                print("===============STOP HERE===============")
                return repos
            try:
                name = repo.name
                repos.append(name)
                print(name)
                print("\n")

                remaining_requests = g.get_rate_limit().core.remaining  # Checking remaining requests before reaching rate limit
                print("Remaining requests: ", remaining_requests)
                if remaining_requests < 15:
                    time.sleep(1800)  # 30 minutes (1800 seconds)
            except Exception as e:
                print("Encountered error during API calls: ", e)
                # Writing to file to not lose what we have
                write_file(repos, "incomplete_cloud_pull.csv")

            print("____________________________________________")
        return repos
    except Exception as e:
        print("Error getting repos: ", e)
        return []
    
def ss_format(repo_list):
    formatted_list = [[repo_name, f"git@github.com:{org_name}/{repo_name}.git"] for repo_name in repo_list]
    return formatted_list

def write_file(data, file_name):
    try:
        with open(file_name, 'w', newline='') as f:
            csv_writer = csv.writer(f)
            for item in data:
                csv_writer.writerow(item)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit()
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        repo_limit = int(sys.argv[1])
    else:
        repo_limit = -1
    start_time = time.time()
    repo_list = get_cloud_repos()
    print("Number of repos: ", len(repo_list))
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time)
    repo_list = ss_format(repo_list)

    if repo_list:
        print("Writing file...")
        write_file(repo_list, "list.csv")
        print("Wrote file!")
    else:
        print("Error with repo list.")
        sys.exit(-1)