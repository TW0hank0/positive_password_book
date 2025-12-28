import os


def main():
    dirs = os.listdir(os.path.join(os.path.dirname(__file__), "..", "dist"))
    for i in dirs:
        if i.startswith("positive_password_book"):
            print(
                os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "dist", i)
                )
            )
            break


main()
