from scrapy import cmdline

def main():
    spider_name = 'weibo'
    login_name = '13625101236'
    login_password = 'SDFSDFLLL1233'
    subject = '美国'
    cmdline.execute(['scrapy', 'crawl', spider_name, '-a', f'login_name={login_name}', '-a', f'login_password={login_password}', '-a', f'subject={subject}'])

if __name__ == '__main__':
    main()