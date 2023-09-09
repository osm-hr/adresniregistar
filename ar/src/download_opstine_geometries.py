import os


def main():
    if not os.path.exists('rgz_creds'):
        print("Before runnning download, you need to create file named 'rgz_creds' with two lines.")
        print("First line should contain username to log in to https://opendata.geosrbija.rs")
        print("Second line should contain password to log in to https://opendata.geosrbija.rs")
        return

    with open('rgz_creds') as f:
        username = f.readline().strip()
        password = f.readline().strip()

    print("Skinite rucno za sad")


if __name__ == '__main__':
    main()
