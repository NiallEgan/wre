import gzip


if __name__ == "__main__":
    f = open("../tests/wiki.xml", "w")
    f.write(gzip.open('wikipages.xml.gz').read())
