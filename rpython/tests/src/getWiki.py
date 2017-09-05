import gzip

if __name__ == '__main__':
     f = open("wikiXML.txt", "w")
     f.write(gzip.open('wikipages.xml.gz').read())
