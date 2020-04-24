from urllib import parse
import base64
import rsa
import binascii

def get_su(user_name):
    username = parse.quote(user_name)   # html字符转义
    username = base64.b64encode(username.encode('utf-8')).decode()
    return username

def get_sp_rsa(passowrd, weibo_rsa_n, servertime, nonce):
    # 这个值可以在prelogin得到,因为是固定值,所以写死在这里
    weibo_rsa_e = 65537  # 10001对应的10进制
    message = str(servertime) + '\t' + str(nonce) + '\n' + passowrd
    key = rsa.PublicKey(int(weibo_rsa_n, 16), weibo_rsa_e)
    encropy_pwd = rsa.encrypt(message.encode('utf-8'), key)
    return binascii.b2a_hex(encropy_pwd).decode()

def card_act_int(text):
    if not text:
        return 0
    if len(text) <=1:
        return 0
    else:
        return int(text[-1])

if __name__ == '__main__':
    print(get_su('18989482970'))
    print(get_sp_rsa('123456', weibo_rsa_n='EB2A38568661887FA180BDDB5CABD5F21C7BFD59C090CB2D245A87AC253062882729293E5506350508E7F9AA3BB77F4333231490F915F6D63C55FE2F08A49B353F444AD3993CACC02DB784ABBB8E42A9B1BBFFFB38BE18D78E87A0E41B9B8F73A928EE0CCEE1F6739884B9777E4FE9E88A1BBE495927AC4A799B3181D6442443', servertime='1585889002', nonce='SF2RM0'))