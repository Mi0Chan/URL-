import requests
import termcolor
import sys
import re
import argparse
import threading
import queue
import time
import json


def info(text):
    sys.stdout.write('%s %s %s\n' %(termcolor.colored(''), termcolor.colored('INFO', 'white', 'on_blue'), text))
    return

def warning(text):
    sys.stdout.write('%s %s %s\n' %(termcolor.colored(''), termcolor.colored('WARN', 'white', 'on_yellow'), text))

def error(text):
    sys.stdout.write('%s %s %s\n' %(termcolor.colored(''), termcolor.colored('ERR', 'white', 'on_red'), text))

def ok(text):
    sys.stdout.write('%s %s %s\n' %(termcolor.colored(''), termcolor.colored('OK', 'white', 'on_green'), text))
    pass

def notice(text):
    sys.stdout.write('%s %s %s\n' % (termcolor.colored(''), termcolor.colored('NOTICE', 'white', 'on_cyan'), text))

def output_info(page_info):
    sys.stdout.write('%s %s %s\n' %(termcolor.colored('FETCH', 'white', 'on_cyan'), termcolor. colored('OK', 'white', 'on_green'), page_info['url']))
    sys.stdout.write('%s\n%s %s\n' %(page_info['name'], page_info['desc'], 'test'))

def check_thread(task_list):
    while 1:
        for item in task_list:
            if not item.is_alive():
                task_list.remove(item)
                del item

def output_file(fp, url_list, mode):
    text = ''
    if 'U' in mode:
        text += url_list['url']
    if 'T' in mode:
        text += '|' + url_list['title']
    if 'D' in mode:
        text += '|' + url_list['description']
    fp.write('{}\n'.format(text))
    return

def banner():
    print("""
██╗   ██╗██████╗ ██╗     ██╗
██║   ██║██╔══██╗██║     ██║
██║   ██║██████╔╝██║     ██║
██║   ██║██╔══██╗██║     ╚═╝
╚██████╔╝██║  ██║███████╗██╗
 ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝
-------------------------   
URL! By Ihara Mio ver 1.0 "Glosside"
A URL Fetcher
-------------------------""")

def intval(text):
    digits = ''
    for item in str(text):
        if item.isdigit():
            digits += item
    return int(digits)

class Curl:
    def __init__(self):
        self.keyword = ''
        self.page_count = 1
        self.debug = True
        self.config = {
            'bing': 'https://www.bing.com/search?q=[KEYWORD]&first=[PAGE]',
            'baidu': 'http://www.baidu.com/s?wd=[KEYWORD]&pn=[PAGE]',
            'gogo': 'https://176.122.157.231:5000/api/search?q=[KEYWORD]&p=[PAGE]',
        }
        self.thread = 10
        self.search_engine = ''
        self.output_file = ''
        self.output_mode = ''
        self.config_file = ''
        self.timeout = ''
        self.delay = 0
        #  Internal stuff.
        self.output_mode = ''
        self.fp = False
        self.url_list = []
        self.TaskQueue = queue.Queue()
        args = {
            'keyword': '',   # [keyword]
            'count': '',  # int(count)
            'engine': '',  # [engine]
            'delay': '',  # int(delay)
            'input': '',  # -
            'threads': '',  # int(threads)
            'output': '',  # fp(output)
            'output_mode': '',  # [output_mode]
        }
        return

    def start(self):
        args = ArgParser().parse_args()

        if not args['keyword']:
            error('No keyword found. Quitting.')
        self.search_engine = args['engine']
        self.keyword = args['keyword']
        self.page_count = args['count']
        self.thread = args['threads']
        self.output_mode = args['output_mode']
        self.fp = args['output']
        self.delay = args['delay']
        for item in args['engine']:
            if item == 'G':
                GogoSpider(self).start()
            elif item == 'A':
                BaiduSpider(self).start()
            elif item == 'B':
                SpiderBing(self).start()
        return



class GogoSpider:
    def __init__(self, main_controller):
        self.task_list = []
        self.controller = main_controller
        self.url = main_controller.config['gogo']
        self.keyword = self.controller.keyword
        self.page_count = self.controller.page_count
        self.queue = queue.Queue()
        pass

    def start(self):
        checker = threading.Thread(target=check_thread, args=[self.task_list], daemon=True)
        checker.start()
        for item in range(0, self.page_count):
            self.queue.put(item)
        while self.queue.qsize():
            if len(self.task_list) < self.controller.thread:
                thread = threading.Thread(target=self.spiderGoGo, args=[self.queue.get()])
                time.sleep(self.controller.delay)
                thread.start()
                self.task_list.append(thread)
        return

    def spiderGoGo(self, page=0):
        try:
            resp = requests.get(self.url.replace('[KEYWORD]', self.keyword).replace('[PAGE]', str(page+1)), verify=False)
            pages = json.loads(resp.text)
            if 'error' in pages.keys():
                error('Error fetching json for page %s: %s.' %(pages['page'], pages['error']))
                notice('WARNING: This is a SERVER error. please try manually.')
                return
            for item in pages['entries']:
                self.controller.url_list.append(item)
                output_info(item)
                if self.controller.fp:
                    output_file(self.controller.fp, item, self.controller.output_mode)
        except requests.RequestException as e:
            error('Network error fetching page information: %s' %(str(e)))
        except json.JSONDecodeError as e:
            error('Failed to decode json: %s' % (str(e)))
        pass


class BaiduSpider:
    def __init__(self, main_controller):
        self.task_list = []
        self.controller = main_controller
        self.url = main_controller.config['baidu']
        self.keyword = self.controller.keyword
        self.page_count = self.controller.page_count
        self.page_list = []
        self.queue = queue.Queue()
        pass

    def start(self): 
        checker = threading.Thread(target=check_thread, args=[self.task_list], daemon=True)
        checker.start()
        for item in range(0, self.page_count):
            self.queue.put(item)
        while self.queue.qsize():
            if len(self.task_list) < self.controller.thread:
                thread = threading.Thread(target=self.SpiderBaidu, args=[self.queue.get()])
                time.sleep(self.controller.delay)
                thread.start()
                self.task_list.append(thread)

    def SpiderBaidu(self, page=0):
        try:
            resp = requests.get(self.controller.config['baidu'].replace('[KEYWORD]', self.keyword).replace('[PAGE]', str(page*10)), verify=False, )
            if self.controller.debug:
                info('DEBUG: {}'.format(self.controller.config['baidu'].replace('[KEYWORD]', self.keyword).replace('[PAGE]', str(page*10))))
            page_info = re.findall('<div class="result ([\w\W.]+?)</a></div></div>', resp.text)
            for item in page_info:
                name = re.findall('data-tools=\'{"title":"(.+)",', item)
                url = re.findall('url":"(.+)"}\'', item)
                desc = re.findall('<div class="c-abstract.*>(.+)</div><div class="f13"', item)
                if not name or not url or not desc:
                    warning('Failed to get page information from response. Is the regex outdated or the script encountered an error?')
                    continue
                try:
                    resp = requests.get(url[0], allow_redirects=False)
                except requests.RequestException as e:
                    error('Request error fetching page from Baidu: %s' %(str(e)))
                    continue
                if 'location' not in resp.headers.keys():
                    warning('Unable to get page redirect location for URL %s.' %(url[0]))
                else:
                    url = resp.headers['location']
                item = {'name': name[0], 'url': url[0], 'desc': str(desc[0]).replace('<em>', '').replace('</em>', '')}
                self.controller.url_list.append(item)
                output_info(item)
                if self.controller.fp:
                    output_file(self.controller.fp, item, self.controller.output_mode)
        except requests.RequestException as e:
            error('Network error fetching page from Baidu.')
        except re.error as e:
            error('Failed to grep text with regex from fetched page. Is the regex outdated?')
        pass



class SpiderBing:
    def __init__(self, main_controller):
        self.task_list = []
        self.controller = main_controller
        self.url = main_controller.config['bing']
        self.keyword = self.controller.keyword
        self.page_count = self.controller.page_count
        self.page_list = []
        self.queue = queue.Queue()
        pass

    def start(self):
        checker = threading.Thread(target=check_thread, args=[self.task_list], daemon=True)
        checker.start()
        for item in range(0, self.page_count):
            self.queue.put(item)
        while self.queue.qsize():
            if len(self.task_list) < self.controller.thread:
                thread = threading.Thread(target=self.BingSpider, args=[self.queue.get()])
                time.sleep(self.controller.delay)
                thread.start()
                self.task_list.append(thread)


    def BingSpider(self, page):
        try:
            resp = requests.get(self.controller.config['bing'].replace('[KEYWORD]', self.keyword).replace('[PAGE]', str((page*10+1))), verify=False, headers={'User-Agent': 'Mozilla/5.0 (X114514; SibylOS x86_64; rv:69.0) Gecko/PseudoBrowser v 1.14'})
            #  f = open('/home/nimda/tmp/test.%s' %(page), 'w+');f.write(resp.text);f.close() #
            #  Blessed be Bing, a searching engine re....well god damn it remake that shit just remake this shit plz
            if self.controller.debug:
                info('DEBUG: {}'.format(self.controller.config['bing'].replace('[KEYWORD]', self.keyword).replace('[PAGE]', str((page*10+1)))))
            page_info = re.findall('<li class="b_algo">(.+?)<div class="b_attribution"', resp.text)
            if not page_info:
                warning('WARNING: Failed to get string match regex from Bing response. Is the regex outdated?')
            for item in page_info:
                name = re.findall('<h2><a target="_blank" href=".*" h="ID=.*">(.+?)</a>', item)
                url = re.findall('<h2><a target="_blank" href="(.+?)" h="ID=.+">', item)
                desc = re.findall('f', item)
                if not name or not url or not desc:
                    warning('Warning: Failed to grep regex from page description. Is the regex outdated or the  script encountered an error?')
                    return
                self.controller.url_list.append({'name': name[0].replace('<strong>', '').replace('</strong>', ''), 'url': url[0], 'desc': desc[0].replace('<strong>', '').replace('</strong>', '')})
                output_info({'name': name[0].replace('<strong>', '').replace('</strong>', ''), 'url': url[0], 'desc': desc[0].replace('<strong>', '').replace('</strong>', '')})
                if self.controller.fp:
                    output_file(self.controller.fp, {'name': name[0].replace('<strong>', '').replace('</strong>', ''), 'url': url[0], 'desc': desc[0].replace('<strong>', '').replace('</strong>', '')}, self.controller.output_mode)
        except re.error as e:
            error('Failed to grep content by regexp: %s' %(str(e)))
        except requests.RequestException as e:
            error('Failed to get response from Bing. Please check your connection.')
        return


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        args = {
            'keyword': [],   # [keyword]
            'count': '',  # int(count)
            'engine': [],  # [engine]
            'delay': '',  # int(delay)
            'input': '',  # -
            'threads': '',  # int(threads)
            'output': '',  # fp(output)
            'output_mode': [],  # [output_mode]
        }
        self.parser.add_argument('-k', '--keyword', dest='keyword',  help='Keyword to get from searc engine.')
        self.parser.add_argument('-p', '--page_count', dest='count', type=int, help='Search page count.', default=10)
        self.parser.add_argument('-e', '--search-engine', dest='engine', help='Search engine (case insenstive). Current support: [b]ing, b[a]idu, [g]ogo|[g]oogle.', default='B')
        self.parser.add_argument('-t', '--search-delay', dest='delay', type=float, help='Search delay dealing with searching engine (seconds). ', default=0)
        self.parser.add_argument('-i', '--input-file', dest='input', help='Keyword file to search.')
        self.parser.add_argument('-m', '--output-mode', dest='output_mode', help='Output mode. [U]rl, [T]tile, [D]escription', default='UT')
        self.parser.add_argument('-o', '--output-file', dest='output', help='Output file to storage page content.')
        self.parser.add_argument('-r', '--threads', type=int,  dest='threads', help='Threads.', default=10)
        #  self.parser.add_argument('-h', '--help', dest=args['help'], action='store_true', help='Show this help. Whaddayaexpect, choomba?')
        # todo: helps
        self.parser.description = 'A url fetcher which can fetch links from searching engine.'
        arg = self.parser.parse_args()
        args['keyword'] = arg.keyword
        if arg.input:
            try:
                fp = open(arg.input, 'r')
                c = 0
                for item in fp.readlines():
                    c += 1
                    args['keyword'].append(item)
                notice('Read %i keyword(s) from keyword list.')
                fp.close()
            except Exception as e:
                error('Failed to read from input file list: %s' %(str(e)))
        if not args['keyword']:
            error('Keyword not found.')
            self.parser.print_help()
            exit()
        args['count'] = intval(arg.count)
        for item in arg.engine.split():
            if item.upper()[0]=='G':
                args['engine'].append('G')
            elif item.upper()[0] == 'A':
                args['engine'].append('A')
            elif item.upper()[0] == 'B':
                item += ' '
                args['engine'].append('A' if item[1] == 'A' else 'B')
        args['threads'] = intval(arg.threads)
        args['delay'] = intval(arg.delay)
        if arg.output:
            try:
                args['output'] = open(arg.output, 'w+')
            except Exception as e:
                error('Unable to open output file: {}'.format(e))
        for item in arg.output_mode.upper():
            if item != 'U' and item != 'T' and item != 'D':
                continue
            args['output_mode'].append(item)
        info('Arguments parse complete.')
        self.args = args


    def parse_args(self):
        return self.args


if __name__ == '__main__':
    banner()
    sess = Curl()
    sess.start()
