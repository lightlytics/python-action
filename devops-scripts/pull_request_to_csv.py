from github import Github
import csv

g = Github("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")
repo = g.get_repo("lightlytics/lightlytics")
g = ""

with open('open_pull_requests10.csv', mode='w') as pr_file:
    pr_writter = csv.writer(pr_file, delimiter=',')
    pr_writter.writerow(["pr_id","pr_number","reviewers","date","commits"])

    # for repo in g.get_user().get_repos("lightlytics/lightlytics"):
    # print(repo)
    pulls = repo.get_pulls(state='all', sort='created', base='master')
    # print(type(pulls))
    for pr in pulls[2018:]:
        list = []
        list.append(str(pr.id))
        list.append(str(pr.number))
        list.append(str(pr.user))
        list.append(str(pr.comments))
        list.append(str(pr.commits))

        print("pr id: " + str(pr.id) + " " + str(pr.number))
        # print ("reviewers: ",end='')
        string_of_reviwers = ""
        for rev in pr.get_reviews():
            string_of_reviwers += (str(rev.user.login) + " ")
            # print(rev.user.login,end='')
        list.append(string_of_reviwers)
        # print("")
        # print ("Commits:")
        string_of_commits = ""
        commits = pr.get_commits()
        date = pr.created_at
        list.append(date.date())
        if commits.totalCount != 0:
            for com in commits:
                string_of_commits += (str(com.sha) + " ")
            list.append(string_of_commits)
            print("-----------------------------------------------")
            pr_writter.writerow(list)
    #


