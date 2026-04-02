import requests
import sys


def dummy_print_completed(tasks):
    print("COMPLETED")
    for t in tasks:
        if t["is_ready"]:
            print(t)
    print(10 * "-")
    print()


def dummy_print_non_completed(tasks):
    print("NOT COMPLETED")
    for t in tasks:
        if not t["is_ready"]:
            print(t)
    print(10 * "-")
    print()


def print_name(tasks):
    for t in tasks:
        print(t["name"])


if __name__ == "__main__":
    evidence_id = str(sys.argv[1])
    task_ids = requests.get(f"http://localhost:8000/evidence/{evidence_id}").json().get("tasks")
    tasks_bodies = []
    for task_id in task_ids:
        tasks_bodies.append(requests.get(f"http://localhost:8000/task/{task_id}").json())
    dummy_print_completed(tasks_bodies)
    dummy_print_non_completed(tasks_bodies)
