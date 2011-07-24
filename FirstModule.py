from lxml import etree
import os

def main():
    tree_root = etree.Element("mails")
    path = "D:\\UNI\\SS11\\BP\\syawrtie.default" #search this path for mboxes
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            if "." not in filename: #detects files without extension as mbox...
                mbox = root + "\\" + filename
                scan_mbox(mbox, tree_root)
    #write xml-tree to file
    fobj = open("mails.xml", "wb")
    fobj.write(etree.tostring(tree_root, pretty_print=True))
    fobj.flush()
    fobj.close()
    
def scan_mbox(mbox, root):
    fobj = open(mbox, "rb")                              #mbox file to read
    a = 0
    mbox = etree.SubElement(root, "mbox", path=mbox)
    for line in fobj:                                   #walk file line by line
        line.strip()
        part = line.split()                             #splits line at whitespaces
        if len(part) > 1:
            if part[0] == b'From' and part[1] == b'-':    #new Message begins
                msg = etree.SubElement(mbox, "msg")
                a += 1
            if part[0] == b'To:':
                text = ""
                for x in range(1, len(part)):
                    try:
                        text += part[x].decode('utf-8') + " "
                    except:
                        text += part[x].decode('cp1252') + " "
                etree.SubElement(msg, "to").text = text
            if part[0] == b'From:':
                text = ""
                for x in range(1, len(part)):
                    text += part[x].decode('cp1252') + " "
                etree.SubElement(msg, "from").text = text
            if part[0] == b'Subject:':
                text = ""
                for x in range(1, len(part)):
                    text += part[x].decode('cp1252') + " "
                etree.SubElement(msg, "title").text = text
            if part[0] == b'Date:':
                text = ""
                for x in range(1, len(part)):
                    text += part[x].decode('cp1252') + " "
                etree.SubElement(msg, "date").text = text
    print("\nmails found: ")  #just for debugging
    print(a)

main()