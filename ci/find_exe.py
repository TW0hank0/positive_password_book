import os


def main():
    dirs = os.listdir(os.path.join(os.path.dirname(__file__), "..", "dist"))
    for i in dirs:
        if i.startswith("positive_password_book"):
            print(i)
            break


main()
