import re

if __name__ == '__main__':
    # rex = r'.* ((\w:|[~.])?(.+)+(.*)?)( |.*(\.*)*)* ?.*'
    # rex = r'(\/.*?\/)((?:[^\/]|\\\/)+?)(?:(?<!\\)\s|$)'
    # rex = r'(?:.*)\s(?:-[\w\d]+\s)*([\/\w\d\s.-]+)'
    # rex = r'(?:[a-zA-Z0-9_-])\s(?:-[\w\d]+\s)*([\/\w\d\s.-]+)' GOOD
    rex = r'(?:\w)\s(?:-[\w\d]+\s)*(?:([\/\w\d\s"\\.-]+)|(".*?"))'
    s1 = " ls -la /Users/hjunior/Pictures "
    s2 = "ls -la /Users/hjunior/Pictures/me.png "
    s3 = "ls -la /Users/hjunior/Pictures/*.txt "
    s4 = 'ls -la /Users/hjunior/Pictures/Pictures of Me '
    s5 = 'ls -la /Users/hjunior/Pictures/"Pictures of Me" '
    s6 = 'ls -la /Users/hjunior/Pictures/Pictures\\ of\\ Me" '
    s7 = " ls -la /Users/hjunior/Pictures/ "

    r1 = re.search(rex, s1)
    r2 = re.search(rex, s2)
    r3 = re.search(rex, s3)
    r4 = re.search(rex, s4)
    r5 = re.search(rex, s5)
    r6 = re.search(rex, s6)
    r7 = re.search(rex, s7)

    print(1, s1, '->', r1.group(1) if r1 else 'XXX')
    print(2, s2, '->', r2.group(1) if r2 else 'XXX')
    print(3, s3, '->', r3.group(1) if r3 else 'XXX')
    print(4, s4, '->', r4.group(1) if r4 else 'XXX')
    print(5, s5, '->', r5.group(1) if r5 else 'XXX')
    print(6, s6, '->', r6.group(1) if r6 else 'XXX')
    print(7, s7, '->', r7.group(1) if r7 else 'XXX')

    assert r1 is not None and r1.group(1).strip() == "/Users/hjunior/Pictures"
    assert r2 is not None and r2.group(1).strip() == "/Users/hjunior/Pictures/me.png"
    assert r3 is not None and r3.group(1).strip() == "/Users/hjunior/Pictures/"
    assert r4 is not None and r4.group(1).strip() == "/Users/hjunior/Pictures/Pictures of Me"
    assert r5 is not None and r5.group(1).strip() == '/Users/hjunior/Pictures/"Pictures of Me"'
    assert r6 is not None and r6.group(1).strip() == "/Users/hjunior/Pictures/Pictures\\ of\\ Me"
    assert r7 is not None and r7.group(1).strip() == "/Users/hjunior/Pictures"
