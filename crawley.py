try:
    from robotparser import RobotFileParser
    from BeautifulSoup import BeautifulSoup
    from cgi import escape
    from Queue import *
    import urlparse as parse
    import urllib2
    import tld
    import optparse
    import networkx as grapher
    import matplotlib.pyplot as plt
except ImportError as e:
    print e.message


#maintain crawled urls
visited_urls = []
#to store urls to crawl
url_queue = Queue()  # stores tuples of (url, depth)
#to visualise url linkages
graph = grapher.Graph()


#removes url fragment
def remove_fragment(url):
    base, fragment = parse.urldefrag(url)
    return base


#checks if url can be crawled according to robots.txt
def robots_check(url):

    #creating url for robots.txt
    root_url = tld.get_tld(url)
    prefix = 'http://www.'
    suffix = '/robots.txt'
    robots_url = prefix + root_url + suffix

    #checking url validity
    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp.can_fetch('*', url)


#Given a page, extract and return links
def get_link_tags(response):
    html = response.read()
    unicode_html = unicode(html, 'utf-8', errors='replace').strip()
    content = BeautifulSoup(unicode_html)
    link_tags = content('a')
    return link_tags


#Cleans links and adds unique links to queue
def process_tags(link_tags, url, depth):
    for link_tag in link_tags:
        href = link_tag.get('href')

        if href:
            link = remove_fragment(href)
            if link not in visited_urls:
                new_url = parse.urljoin(url, escape(link))
                url_queue.put((new_url, depth+1))
                graph.add_edge(url, new_url)

# Gets links from a page and processes them.
def parse_page(response, url, depth):
    try:
        #get response and parse anchor tags
        link_tags = get_link_tags(response)

        #parse anchor tags and add hyperlink to queue
        if link_tags:
            process_tags(link_tags, url, depth)

    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code

    except urllib2.URLError as e:
        print e.message

    except Exception as e:
        print e.message


#find next link, check, and open
def crawl(url, max_depth):
    url_queue.put((url, 0))  # initial depth is 0
    counter = 0

    while not url_queue.empty():
        print 'Url no:{0}'.format(counter)
        counter += 1

        url, depth = url_queue.get()
        print 'crawling: {0}'.format(url)
        print 'Depth:{0} '.format(depth)
        print ' Max depth is {0}'.format(max_depth)
        print depth > max_depth
        if depth > max_depth:
            print ' Exceeded depth \n'
            break
        else:
            print ' Enters else'
            if not robots_check(url):
                print 'Robots.txt prevents crawling this url'

            else:

                response = urllib2.urlopen(url)
                headers = response.info()

                #if non html content ignore
                content_type = 'text/html'
                if content_type not in headers['content-type']:
                    print 'Non HTML File'

                else:
                    parse_page(response, url,depth)
                    visited_urls.append(url)
    return counter


def visualise():
    grapher.draw(graph)
    plt.show()

#handles command line arguments and returns values
def parse_options():

    parser = optparse.OptionParser()

    parser.add_option('-l', '--url',
                            action='store',
                            dest='url',
                            help='Seed url to start crawling from')

    parser.add_option('-d', '--depth',
                            action='store',
                            dest='depth',
                            help='Maximum Depth to  traverse')

    parser.add_option('-f', '--filename',
                            action='store',
                            dest='filename',
                            help='filename to store crawled urls in')
    opts, args = parser.parse_args()



    # Making sure all mandatory options are present.
    mandatories = ['url', 'depth', 'filename']
    for m in mandatories:
        if not opts.__dict__[m]:
            print "One or more mandatory options are missing\n"
            parser.print_help()
            exit(-1)

    return opts, args


#Save visited urls to file
def write_urls(filename):
    f = open(filename, 'w')
    for url in visited_urls:
        f.write(url+'\n')
    f.close()


#start of program
def main():

    opts, args = parse_options()
    url = opts.url
    max_depth = opts.depth
    filename = opts.filename

    url_count = crawl(url, max_depth)

    visualise()

    write_urls(filename)
    print'{0} urls crawled\n'.format(url_count)


#to enable these functions to be used with other files
if __name__ == '__main__':
    main()