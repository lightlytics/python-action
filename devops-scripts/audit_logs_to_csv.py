import csv

with open('audit_log_to_csv.csv', mode='w') as csv_file:
    pr_writter = csv.writer(csv_file, delimiter=',')
    pr_writter.writerow(["date", "user", "ip", "port"])
