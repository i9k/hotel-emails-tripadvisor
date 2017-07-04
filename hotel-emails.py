import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import sys
import pandas as pd
from collections import defaultdict, namedtuple

# full path to the webdriver to use; use webdriver.PhantomJS() for invisible browsing
driver = webdriver.Chrome('/Users/ik/Codes/hotel-emails-tripadvisor/webdriver/chromedriver')
# default waiting time
WAIT_TIME = 40
# base URL
BASE_REVIEW_URL = "http://tripadvisor.com.au/"
# page to go to first
start_page  = "https://www.tripadvisor.com.au/Best-Hotels-Sydney.html"
driver.get(start_page)
time.sleep(5)

def _how_many_pages_on_pagination_bar():
	"""
	locate the pagination bar at the bottom of the current page and find how many pages are there
	"""
	all_possible_bar_divs = driver.find_elements_by_xpath("//div[contains(@class,'unified') and contains(@class, 'standard_pagination')]")
	max_page = None
	time.sleep(3)
	if all_possible_bar_divs:
		for located_div in all_possible_bar_divs:
			try:
				max_page = int(located_div.get_attribute("data-numpages"))
				break  # no need to keep looking
			except:
				continue
		if max_page:
			return max_page
		else:
			print("[ERROR]: can't find max page on the pagination bar at the bottom...")
			sys.exit(0)
	else:
		print("[ERROR]: can't locate the pagination bar at the bottom...")
		sys.exit(0)

# pagination bar at the bottom of the page
pagination_bar = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "pageNumbers")))

max_page = _how_many_pages_on_pagination_bar()

print("[pagination bar]: available pages to visit: {}".format(max_page))


# start visiting pages

for page in range(1, max_page + 1):

	print("page {}".format(page))

	# first simply find that button
	# pagination bar at the bottom of the page
	pagination_bar = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "pageNumbers")))
	try:
		page_button = pagination_bar.find_element_by_xpath("span[@data-page-number='" + str(page) + "']")
	except:
		try:
			page_button = pagination_bar.find_element_by_xpath(".//a[@data-page-number='" + str(page) + "']")
		except:
			print("[ERROR]: unable to find page {} button on the pagination bar!".format(page))
			sys.exit(0)

	#  if got to here, the button has been found; but it is clickable?
	try:
		time.sleep(3)
		page_button.click()
	except:
		# give a warning but assume that it's because we are already on the page we need
		print("[WARNING]: page button on the pagination bar is not clickable...")

	# create a hotel url list for the hotels on this page
	hname_lst = []
	hurl_lst = []
	hwebs_lst = []
	haddr_lst = []
	hemail_lst = []
	# can we find any hotels on this page at all?
	hrefs_on_page = driver.find_elements_by_xpath(".//a[@class='property_title']")

	if not hrefs_on_page:
		print("[ERROR]: cannot find any hotel links on this page...")
		sys.exit(0)
	else:
		for a in hrefs_on_page:
			hname_lst.append(a.text.lower().strip())
			hurl_lst.append(a.get_attribute("href"))

	print("found {} hotels on this page...".format(len(hname_lst)))

	for i, url in enumerate(hurl_lst[:2]):

		print("hotel {}/{}: {}".format(i + 1, len(hname_lst), hname_lst[i]))
		print("url: {}".format(url))

		driver.get(url)
		time.sleep(5)
		# hotel main page handle
		hmain_h = driver.current_window_handle

		#  a d d r e s s

		hotel_address = []

		try:
			span_address = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "street-address")))
			hotel_address.append(span_address.text.lower().strip())
		except:
			print("[WARNING]: cannot find street address for {}..".format(hname_lst[i]))
		try:
			span_locality = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "locality")))
			hotel_address.append(span_locality.text.lower().strip())
		except:
			print("[WARNING]: cannot find localty for {}..".format(hname_lst[i]))
		try:
			span_country = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "country-name")))
			hotel_address.append(span_country.text.lower().strip())
		except:
			print("[WARNING]: cannot find country for {}..".format(hname_lst[i]))

		haddr_lst.append(" ".join(hotel_address))

		print("address: {}".format(haddr_lst[-1]))

		# w e b s i t e

		# see if there's a link to the hotel's website; if there is, click
		try:
			WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "website"))).click()
			time.sleep(5)   # give it 5 sec to load
			# the website is supposed to start loading in a new window
			for h in driver.window_handles:
				if h != hmain_h:
					driver.switch_to_window(h)
					hwebs_lst.append(driver.current_url.split("//")[1].split("/")[0].lower().strip())
					driver.close()
					driver.switch_to_window(hmain_h)
		except:
			hwebs_lst.append(None)

		print("website: {}".format(hwebs_lst[-1]))

		# hotel main page handle again
		hmain_h = driver.current_window_handle

		# e m a i l

		# check if there's an option to email the hotel

		try:
			email_hotel_option = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "email")))
		except:
			print("[WARNING]: can't find the email hotel option...")
			hemail_lst.append(None)
			continue
		try:
			email_hotel_option.click()
			time.sleep(3)
		except:
			print("[ERROR]: cannot click on the email option...")
			sys.exit(0)

		hotel_email = None

		try:
			alert = driver.switch_to.alert
		except:
			print("[ERROR]: cannot switch to alert!")
			sys.exit(0)

		# if got here, the switch to alert went well
		inps = driver.find_elements(By.XPATH, "//input[@id='receiver']")
		if not inps:
			print("[ERROR]: cannot find any suitable inputs!")
			sys.exit(0)
		else:
			for inp in inps:
				try:
					hotel_email = inp.get_attribute("value").lower().strip()
					hemail_lst.append(hotel_email)
					alert.dismiss()
					break
				except:
					print("[ERROR]: cannot pick the vaue of email input!")
					hemail_lst.append(None)
					sys.exit(0)

			print("email: {}".format(hemail_lst[-1]))


		# handles = driver.window_handles
		# driver.switch_to_window(handles[0])

driver.quit()
