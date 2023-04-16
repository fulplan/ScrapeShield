import random
import socks
import socket
import urllib3
import logging
import requests
import time


class ProxyManager:
    """
    This class contains the functionality for managing different types of proxies.
    """

    def __init__(self, proxy_ips=None, proxy_ports=None, proxy_username=None, proxy_password=None,
                 proxy_type='http', verbose=False, max_requests_per_proxy=10, rotate_proxies_every=60):

        self.max_requests_per_proxy = max_requests_per_proxy
        self.rotate_proxies_every = rotate_proxies_every
        self.requests_count = 0
        self.last_rotation_time = time.time()
        self.proxy_ips = proxy_ips or []
        self.proxy_ports = proxy_ports or []
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.proxy_type = proxy_type.lower()
        self.verbose = verbose
        self.last_proxy_index = -1

        # Set up proxy manager
        if self.proxy_type == 'socks4':
            socks_version = socks.SOCKS4
        elif self.proxy_type == 'socks5':
            socks_version = socks.SOCKS5
        elif self.proxy_type == 'https':
            socks_version = socks.HTTP
        elif self.proxy_type == 'http':
            socks_version = None
        else:
            raise ValueError(f"Invalid proxy type {self.proxy_type}")

        # Update proxy URL based on proxy type
        if self.proxy_type in ['socks4', 'socks5']:
            proxy_url = f"{self.proxy_type}://{':'.join(filter(None, [self.proxy_username, self.proxy_password]))}@{':'.join(filter(None, [self.proxy_ips[0], str(self.proxy_ports[0])] + ['']))}"
            self.proxy_manager = urllib3.ProxyManager(
                proxy_url=proxy_url,
                timeout=urllib3.Timeout(connect=5.0, read=10.0),
                num_pools=10,
                retries=urllib3.Retry(total=3, backoff_factor=0.5, status_forcelist=[
                                      500, 502, 503, 504]),
                maxsize=10,
                username=self.proxy_username,
                password=self.proxy_password,
                sock_version=socks_version,
            )
        elif self.proxy_type == 'http':
            if self.proxy_username and self.proxy_password:
                auth = f"{self.proxy_username}:{self.proxy_password}@"
            else:
                auth = ''
            proxy_url = f"{self.proxy_type}://{auth}{':'.join(filter(None, [self.proxy_ips[0], str(self.proxy_ports[0])] + ['']))}"
            self.proxy_manager = urllib3.ProxyManager(
                proxy_url=proxy_url,
                timeout=urllib3.Timeout(connect=5.0, read=10.0),
                num_pools=10,
                retries=urllib3.Retry(total=3, backoff_factor=0.5, status_forcelist=[
                                      500, 502, 503, 504]),
                maxsize=10,
            )

    def _update_proxy_list(self):
        """
        This method updates the list of available proxies to use.
        """
        self.proxy_list = []
        for i, ip in enumerate(self.proxy_ips):
            port = self.proxy_ports[i] if self.proxy_ports else None
            # Update proxy URL based on proxy type
            if self.proxy_type in ['socks4', 'socks5']:
                proxy_url = f"{self.proxy_type}://{':'.join(filter(None, [self.proxy_username, self.proxy_password]))}@{':'.join(filter(None, [ip, str(port)] + ['']))}"
            elif self.proxy_type == 'http':
                if self.proxy_username and self.proxy_password:
                    auth = f"{self.proxy_username}:{self.proxy_password}@"
                else:
                    auth = ''
                proxy_url = f"{self.proxy_type}://{auth}{':'.join(filter(None, [ip, str(port)] + ['']))}"
            else:
                raise ValueError(f"Invalid proxy type {self.proxy_type}")
            self.proxy_list.append({
                'http': proxy_url,
                'https': proxy_url,
                'working': False,
                'blacklisted': False
            })

    def _test_proxy(self, proxy):
        """
        This method tests whether a given proxy is functioning properly and not blacklisted.
        """
        BLACKLISTED_DOMAINS = [
            'google.com', 'facebook.com']  # Change this list as per your requirements

        try:
            response = self.proxy_manager.request('GET', f"http://{proxy['http']}", headers=urllib3.util.make_headers(
                proxy_basic_auth=f"{self.proxy_username}:{self.proxy_password}"))
            if response.status == 200:
                domain = random.choice(BLACKLISTED_DOMAINS)
                response = self.proxy_manager.request('GET', f"http://{domain}", headers=urllib3.util.make_headers(
                    proxy_basic_auth=f"{self.proxy_username}:{self.proxy_password}"), timeout=10)
                if response.status == 200:
                    # Proxy working
                    return True
                else:
                    # Proxy blacklisted
                    logging.warning(
                        f"Proxy {proxy['http']} is blacklisted for domain {domain}")
                    return False
            else:
                # Proxy not working
                logging.warning(f"Proxy {proxy['http']} is not working")
                return False
        except urllib3.exceptions.HTTPError as e:
            # Error occurred while testing proxy due to HTTP error
            logging.warning(
                f"HTTP error occurred while testing proxy {proxy['http']}: {e}")
            return False
        except socks.ProxyConnectionError as e:
            # Error occurred while connecting to SOCKS proxy
            logging.warning(
                f"Error occurred while connecting to SOCKS proxy {proxy['http']}: {e}")
            return False
        except (socket.timeout, urllib3.exceptions.TimeoutError) as e:
            # Timeout occurred while testing proxy
            logging.warning(
                f"Timeout occurred while testing proxy {proxy['http']}: {e}")
            return False
        except Exception as e:
            # Other errors occurred while testing proxy
            logging.warning(
                f"Error occurred while testing proxy {proxy['http']}: {e}")
            return False

    def make_request(self, url):
        """
        This method makes a request using a randomly selected proxy from the list of available proxies.
        """
        if self.rotate_proxies_every and time.time() - self.last_rotation_time > self.rotate_proxies_every:
            # Rotating proxies after every `rotate_proxies_every` seconds.
            if self.verbose:
                logging.debug("Rotating proxies...")
            self._update_proxy_list()
            self.last_rotation_time = time.time()

        if self.requests_count >= self.max_requests_per_proxy:
            # Switching to next proxy once max requests limit has been reached.
            self.last_proxy_index += 1
            if self.last_proxy_index == len(self.proxy_list):
                self.last_proxy_index = 0
            self.requests_count = 0

        while not self.proxy_list[self.last_proxy_index]['working']:
            # Skipping over blacklisted or non-working proxies.
            self.last_proxy_index += 1
            if self.last_proxy_index == len(self.proxy_list):
                self.last_proxy_index = 0

        # Making request using selected proxy.
        proxy = self.proxy_list[self.last_proxy_index]
        try:
            response = requests.get(url, proxies={
                'http': f"http://{proxy['http']}",
                'https': f"https://{proxy['http']}"
            })
            if response.status_code == 200:
                self.requests_count += 1
                return response.content
            else:
                # Marking proxy as non-working if request fails.
                logging.warning(
                    f"Request failed with status {response.status_code} using proxy {proxy['http']}")
        except:
            pass

        proxy['working'] = False
        self.last_proxy_index += 1
        if self.last_proxy_index == len(self.proxy_list):
            self.last_proxy_index = 0
        return None

    def get_proxy(self):
        """
        This method retrieves a working proxy from the list of available proxies.
        """
        # Rotate proxies if required
        if self.requests_count >= self.max_requests_per_proxy or time.time() - self.last_rotation_time >= self.rotate_proxies_every:
            self._update_proxy_list()
            self.requests_count = 0
            self.last_proxy_index = -1
            self.last_rotation_time = time.time()

        # Get next working and non-blacklisted proxy
        num_proxies = len(self.proxy_list)
        for i in range(num_proxies):
            index = (self.last_proxy_index + i + 1) % num_proxies
            proxy = self.proxy_list[index]
            if proxy['working'] and not proxy['blacklisted']:
                self.last_proxy_index = index
                self.requests_count += 1
                return proxy['http']

        # No working proxy found
        raise ValueError("No working proxy found")

    def mark_proxy_as_working(self, proxy_url):
        """
        This method marks a given proxy as working.
        """
        for proxy in self.proxy_list:
            if proxy['http'] == proxy_url:
                proxy['working'] = True
                proxy['blacklisted'] = False
                break

    def mark_proxy_as_not_working(self, proxy_url):
        """
        This method marks a given proxy as not working.
        """
        for proxy in self.proxy_list:
            if proxy['http'] == proxy_url:
                proxy['working'] = False
                proxy['blacklisted'] = False
                break

    def mark_proxy_as_blacklisted(self, proxy_url):
        """
        This method marks a given proxy as blacklisted.
        """
        for proxy in self.proxy_list:
            if proxy['http'] == proxy_url:
                proxy['working'] = False
                proxy['blacklisted'] = True
                break

    def add_proxy(self, ip, port=None):
        """
        This method adds a new proxy to the list of available proxies.
        """
        self.proxy_ips.append(ip)
        self.proxy_ports.append(port)
        self._update_proxy_list()

    def remove_proxy(self, index):
        """
        This method removes a proxy from the list of available proxies.
        """
        if index < len(self.proxy_ips):
            del self.proxy_ips[index]
            if self.proxy_ports and index < len(self.proxy_ports):
                del self.proxy_ports[index]
            self._update_proxy_list()

    def clear_proxies(self):
        """
        This method clears the list of available proxies.
        """
        self.proxy_ips = []
        self.proxy_ports = []
        self._update_proxy_list()

    def use_tor(self):
        """
        This method sets up a connection to tor for proxy usage.
        """
        try:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket
            if self.verbose:
                logging.info("Connected to Tor network for proxy usage.")
        except Exception as e:
            logging.error("Failed to connect to Tor network.")
            if self.verbose:
                logging.error(str(e))

    def rotate_proxies(self):
        """
        This method rotates through the list of available proxies.
        """
        if len(self.proxy_list) > 0:
            self.last_proxy_index = (
                self.last_proxy_index + 1) % len(self.proxy_list)

    def test_all_proxies(self):
        """
        This method tests all the available proxies and updates their 'working' status accordingly.
        """
        for proxy in self.proxy_list:
            proxy['working'] = self._test_proxy(proxy)

    def check_proxy_health(self, index):
        """
        This method checks the health of a single proxy by making a request to a test URL using the proxy.
        """
        if index < len(self.proxy_list):
            proxy = self.proxy_list[index]
            proxy['working'] = self._test_proxy(proxy)
            return proxy['working']
        else:
            return False

    def get_working_proxies(self):
        """
        This method returns a list of working proxies.
        """
        working_proxies = []
        for proxy in self.proxy_list:
            if proxy['working'] and not proxy['blacklisted']:
                working_proxies.append(proxy['http'])
        return working_proxies

    def get_random_working_proxy(self):
        """
        This method returns a random working proxy from the list of available proxies.
        """
        working_proxies = self.get_working_proxies()
        if len(working_proxies) > 0:
            return random.choice(working_proxies)
        else:
            return None

    def get_request_with_random_proxy(self, url):
        """
        This method makes a request using urllib3 with a randomly chosen working proxy.
        """
        random_proxy = self.get_random_working_proxy()
        if not random_proxy:
            return None
        try:
            response = self.proxy_manager.request('GET', url, headers=urllib3.util.make_headers(
                proxy_basic_auth=f"{random_proxy['proxy_username']}:{random_proxy['proxy_password']}"), proxy_url=random_proxy[self.proxy_type], timeout=5.0)
            if response.status != 200:
                raise urllib3.exceptions.HTTPError(
                    f"Received a non-200 status code ({response.status}) from {random_proxy['http']}")
            if self.verbose:
                logging.info(
                    f"Request successful via {random_proxy['http']}, response:\n{response.data.decode()}")
            return response
        except (urllib3.exceptions.MaxRetryError, urllib3.exceptions.NewConnectionError) as e:
            logging.error(
                f"Could not connect to the proxy {random_proxy['http']}. Error: {str(e)}")
            random_proxy['working'] = False
            return None
        except urllib3.exceptions.HTTPError as e:
            logging.error(str(e))
            random_proxy['working'] = False
            return None
        except Exception as e:
            logging.error(
                f"An error occurred with {random_proxy['http']}: {str(e)}")
            random_proxy['working'] = False
            return None
