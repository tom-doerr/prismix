def process_file(filepath):
    with open(filepath, "r", encoding='utf-8') as f:
        content = f.read()

    words = content.split()
    word_count = len(words)

    with open(filepath + ".stats", "w") as f:
        f.write(f"Word count: {word_count}")


def main():
    process_file("input.txt")


if __name__ == "__main__":
    main()
