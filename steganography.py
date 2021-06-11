from PIL import Image
import numpy as np
import argparse
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

# メイン
def main():
    # コマンドライン引数取得
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", action='store_true')
    parser.add_argument("-x", "--expand", action='store_true')
    parser.add_argument("-i", "--input_image", type=str)
    parser.add_argument("-o", "--output_image", type=str)
    parser.add_argument("-m", "--message_file", type=str)
    parser.add_argument("-f", "--output_file", type=str)
    parser.add_argument("-p", "--password", type=str)
    args = parser.parse_args()

    if args.add :
        # メッセージ埋め込み
        stegano(args.input_image, args.message_file, args.password, args.output_image)
    
    if args.expand :
        # メッセージ取得
        getdata(args.output_image, args.password, args.output_file)


# 暗号化
def encrypt(decrypted_data, password):
    sha = SHA256.new()
    sha.update(password.encode())
    key = sha.digest()
    cipher = AES.new(key, AES.MODE_EAX)
    return cipher.nonce + cipher.encrypt(decrypted_data)


# 隠ぺい
def stegano(input_file, message_file, password, output_file):
    # ファイル読み込み
    f = open(message_file, 'rb')
    txt = f.read()
    txt += b'\0'

    img = Image.open(input_file).convert('RGB')
    width, height = img.size
    img2 = Image.new('RGB', (width, height))
    #img_pixels = np.array([[img.getpixel((x,y)) for x in range(width)] for y in range(height)])

    # 暗号化
    enctxt = encrypt(txt, password)

    # テキストを2進数に変換する。
    bintxt = ''
    for c in enctxt:
        # print(hex(c) + " " + "{:08b}".format(c))
        bintxt += "{:08b}".format(c)

    #print(bintxt[:32])

    # 色の下位1ビットを書き換える。
    n = 0
    for y in range(height):
        for x in range(width):
            # 下位1ビットを書き換える。
            r, g, b = img.getpixel((x, y))
            if n < len(bintxt):
                if bintxt[n] == '0':
                    b = b & 0xfe
                else:
                    b = b | 0x01

            # 値を新しい画像に反映する。
            img2.putpixel((x,y), (int(r), int(g), int(b)))
            n += 1

    # img2.show()
    img2.save(output_file)


# 復号化
def decrypt(encrypted_data, password, iv):
    sha = SHA256.new()
    sha.update(password.encode())
    key = sha.digest()
    cipher = AES.new(key, AES.MODE_EAX, iv)
    return cipher.decrypt(encrypted_data)


# 取得
def getdata(stegano_image, password, message_file):
    img = Image.open(stegano_image).convert('RGB')
    width, height = img.size

    bintxt = ''
    # 色の下位1ビットを読み取る。
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            bintxt += bin(b)[-1]

    #print(bintxt[:32])

    # 2進数をテキストに変換する。
    bary = bytearray()
    for n in range(0, int(len(bintxt) / 8)):
        c = int(bintxt[n * 8:n * 8 + 8], 2)
        bary.append(c)

    # 復号化
    txt = decrypt(bytes(bary[16:]), password, bary[:16])

    try:
        msgLen = txt.index(b'\0')
    except ValueError:
        msgLen = len(txt)

    if message_file != None:
        f = open(message_file, 'wb')
        f.write(txt[:msgLen])
        f.close()
    else:
        print(txt[:msgLen].decode())

# 実行
main()


