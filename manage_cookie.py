from scrapy import cmdline

def main():
    spider_name = 'weibo_cookie'
    subject = '罗志祥道歉'
    dbName = 'lzx'
    cmdline.execute(['scrapy', 'crawl', spider_name, '-a', f'subject={subject}', '-a', f'dbName={dbName}'])

if __name__ == '__main__':
    main()