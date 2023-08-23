try:
    import sys
    import os
    from src.dentalia import main as dentaila
    from src.santaelena import main as santaelena
    from src.yapdomik import main as yapdomik
except ModuleNotFoundError as e:
    print(
        e,
        'Run pip install -r requirements.txt'
    )
    sys.exit()


def main():
    try:
        start = sys.argv[1]
        if start not in ['-a', '-den', '-san', '-yap']:
            raise IndexError
    except IndexError:
        print(
            'Arguments are required:\n'
            '\t-den\tto call dentalia\n'
            '\t-yap\tto call yapdomik\n'
            '\t-san\tto call santaelena\n'
            '\t-a\tto call all'
        )
        return
    try:
        path = sys.argv[2]
    except IndexError:
        path = './data'
        if not os.path.exists('./data/'):
            os.mkdir('./data/')

    match start:
        case '-a':
            dentaila(path)
            yapdomik(path)
            santaelena(path)
        case '-den':
            dentaila(path)
        case '-yap':
            yapdomik(path)
        case '-san':
            santaelena(path)


if __name__ == "__main__":
    main()
