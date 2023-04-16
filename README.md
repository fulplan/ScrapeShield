# ScrapeShield


ScrapeShield is a Python library for web scraping that enables you to scrape websites using proxies. The library provides a simple and easy-to-use interface for managing different types of proxies, rotating them at regular intervals, and testing their validity to ensure they are not blacklisted.

> Installation

Dependencies

This class requires the following packages to be installed:

    random
    socks
    socket
    urllib3
    logging
    requests
    time


Initialization

To use this class, you first need to create an instance of the ProxyManager class, passing in the following arguments:

    proxy_ips (optional): A list of proxy IP addresses to use.
    proxy_ports (optional): A list of proxy ports to use. If not provided, the default port for the proxy type will be used.
    proxy_username (optional): The username to use for authenticated proxies.
    proxy_password (optional): The password to use for authenticated proxies.
    proxy_type (optional): The type of proxy to use. Defaults to 'http'.
    verbose (optional): A boolean value indicating whether to output logs to the console.

`    max_requests_per_proxy (optional): The maximum number of requests to make per proxy before rotating to a new one. Defaults to 10.`


`rotate_proxies_every (optional): The number of seconds to wait before rotating to a new proxy. Defaults to 60.`



> Getting Started

To use ScrapeShield in your Python script, first import the ProxyManager class as follows:


```
from scrapeshield import ProxyManager

proxy_manager = ProxyManager(
    proxy_ips=['1.1.1.1', '2.2.2.2'], 
    proxy_ports=[80, 8080], 
    proxy_username='username', 
    proxy_password='password', 
    proxy_type='socks5', 
    verbose=True, 
    max_requests_per_proxy=5, 
    rotate_proxies_every=30
)
```


Updating Proxies

To update the list of available proxies to use, call the _update_proxy_list method. This method updates the proxy_list attribute with the list of available proxies.

python

proxy_manager._update_proxy_list()

Testing Proxies

To test whether a given proxy is functioning properly and not blacklisted, call the _test_proxy method, passing in the proxy as an argument. This method returns True if the proxy is functioning properly and not blacklisted, and False otherwise.

`proxy = {'http': 'socks5://1.1.1.1:80', 'https': 'socks5://1.1.1.1:80'}
is_working = proxy_manager._test_proxy(proxy)
`

Getting a Proxy

To get a working proxy, call the get_proxy method. This method returns a proxy URL that can be used with requests.

`
proxy_url = proxy_manager.get_proxy()
`

Example Usage

Here is an example usage of the ProxyManager class:

```
from proxy_manager import ProxyManager

proxy_manager = ProxyManager(
    proxy_ips=['1.1.1.1', '2.2.2.2'], 
    proxy_ports=[80, 8080], 
    proxy_username='username', 
    proxy_password='password', 
    proxy_type='socks5', 
    verbose=True, 
    max_requests_per_proxy=5, 
    rotate_proxies_every=30
)

proxy_manager._update_proxy_list()

while True:
    proxy_url = proxy_manager.get_proxy()
    print(f"Using proxy: {proxy_url}")
    response = requests.get("http://example.com", proxies={'http':




```
proxy_ips = ['1.1.1.1', '2.2.2.2', '3.3.3.3']  # List of proxy IPs
proxy_ports = [8080, 8888, 9999]  # List of proxy ports (optional)
proxy_username = 'username'  # Proxy username (optional)
proxy_password = 'password'  # Proxy password (optional)
proxy_type = 'http'  # Proxy type: http, socks4, socks5 (default: http)
verbose = True  # Whether to output logs to console (default: False)
max_requests_per_proxy = 10  # Maximum number of requests to make per proxy (default: 10)
rotate_proxies_every = 60  # Interval in seconds to rotate proxies (default: 60)
proxy_manager = ProxyManager(proxy_ips, proxy_ports, proxy_username, proxy_password, proxy_type, verbose, max_requests_per_proxy, rotate_proxies_every)
```
Once you have created the ProxyManager object, you can use it to make HTTP requests using proxies as follows:

```
response = proxy_manager.proxy_manager.request('GET', 'https://www.example.com')
print(response.data)
```

> Rotating Proxies

ScrapeShield automatically rotates proxies at regular intervals to prevent IP blocking and ensure that the scraping process runs smoothly. The rotate_proxies_every parameter specifies the time interval (in seconds) at which proxies should be rotated. By default, proxies are rotated every 60 seconds.
Testing Proxies

ScrapeShield tests the validity of proxies before using them to make HTTP requests. The max_requests_per_proxy parameter specifies the maximum number of requests to make using a single proxy before testing its validity. By default, proxies are tested after every 10 requests.
Contributing

If you would like to contribute to ScrapeShield, please fork the repository and submit a pull request. All contributions are welcome!
License

ScrapeShield is licensed under the MIT License. See LICENSE.txt for more information.