import re


def car_no(text):
    pat = re.compile("(.[A-Za-z0-9]{6}|.{7}(?=\W*$))")
    return pat.search(text)
    
def reason(text):
    pat = re.compile("(挡|堵|占|施工|碍事|画线|压|停|消防|没).*(门口|位置|车|车位|道|路|门|井盖|线|车窗|桩|禁停区)|(挡|堵|占|施工|碍事|画线|压|停|消防|没).*$|^.*(门口|位置|车|车位|道|路|门|井盖|线|车窗|桩|禁停区)")
    return pat.search(text)

def test_reason():
    strs = ["挡我充电器","挂我门口了","停在禁停区啦","这里不允许停车"]
    for text in strs:
        print(f"{text} -> {reason(text)}")
        
if __name__ == "__main__":
    import argparse
    # Create a parser
    parser = argparse.ArgumentParser(description='Regex parser')
    # Add argument
    parser.add_argument('type', default="carno", help="entrance id")
    
    print(car_no("金2P2期37。"))