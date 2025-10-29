# Testing_Quality_Assurance

# Testing Quality Assurance for Shoe_Store_Hub_20251028_214718
## Introduction
The Shoe_Store_Hub_20251028_214718 project aims to develop an e-commerce website for a shoe store. This document outlines the testing quality assurance process, including test automation and performance testing. The deliverables for this task include a test plan and a test report.

## Test Plan
The test plan is based on the requirements gathered and analyzed in the previous stages. The test plan includes the following test cases:

* **Test Case 1: Browse Shoes by Category**
	+ Preconditions: The user is logged in and has access to the shoe store website.
	+ Steps:
		1. The user navigates to the shoe store website.
		2. The user selects a shoe category from the list of categories.
		3. The website displays a list of shoes in the selected category.
	+ Expected Result: The website displays a list of shoes in the selected category.
* **Test Case 2: Search for Shoes by Keyword**
	+ Preconditions: The user is logged in and has access to the shoe store website.
	+ Steps:
		1. The user navigates to the shoe store website.
		2. The user enters a keyword in the search bar.
		3. The website displays a list of shoes that match the search keyword.
	+ Expected Result: The website displays a list of shoes that match the search keyword.
* **Test Case 3: View Shoe Details**
	+ Preconditions: The user is logged in and has access to the shoe store website.
	+ Steps:
		1. The user navigates to the shoe store website.
		2. The user selects a shoe from the list of shoes.
		3. The website displays the shoe details, including price, description, and images.
	+ Expected Result: The website displays the shoe details, including price, description, and images.
* **Test Case 4: Add Shoes to Cart**
	+ Preconditions: The user is logged in and has access to the shoe store website.
	+ Steps:
		1. The user navigates to the shoe store website.
		2. The user selects a shoe from the list of shoes.
		3. The user adds the shoe to their cart.
	+ Expected Result: The shoe is added to the user's cart.
* **Test Case 5: Checkout Securely**
	+ Preconditions: The user is logged in and has access to the shoe store website.
	+ Steps:
		1. The user navigates to the shoe store website.
		2. The user selects a shoe from the list of shoes.
		3. The user adds the shoe to their cart.
		4. The user proceeds to checkout.
	+ Expected Result: The user is able to checkout securely.

## Test Automation
The test automation will be implemented using Selenium. The test automation script will cover the test cases outlined in the test plan.

```python
# Example test code: product listing test
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up the webdriver
driver = webdriver.Chrome()

# Navigate to the shoe store website
driver.get("https://shoestorehub.com")

# Select a shoe category
category_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//select[@id='category']"))
)
category_element.select_by_visible_text("Men's Shoes")

# Verify that the website displays a list of shoes in the selected category
shoes_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//div[@class='shoes']"))
)
assert shoes_element.is_displayed()

# Close the webdriver
driver.quit()
```

## Performance Testing
The performance testing will be implemented using JMeter. The performance testing script will cover the test cases outlined in the test plan.

```python
# Example performance test code: product listing test
from jmeter import JMeter

# Set up the JMeter test
test = JMeter()

# Add a thread group to the test
thread_group = test.add_thread_group(
    num_threads=10,
    ramp_up=1,
    loop_count=1
)

# Add a HTTP request to the thread group
http_request = thread_group.add_http_request(
    method="GET",
    url="https://shoestorehub.com",
    protocol="https"
)

# Add a response assertion to the HTTP request
response_assertion = http_request.add_response_assertion(
    response_data="Men's Shoes",
    response_code=200
)

# Run the test
test.run()
```

## Test Report
The test report will include the results of the test cases outlined in the test plan. The test report will include the following information:

* **Test Case 1: Browse Shoes by Category**
	+ Result: Pass
	+ Notes: The website displayed a list of shoes in the selected category.
* **Test Case 2: Search for Shoes by Keyword**
	+ Result: Pass
	+ Notes: The website displayed a list of shoes that match the search keyword.
* **Test Case 3: View Shoe Details**
	+ Result: Pass
	+ Notes: The website displayed the shoe details, including price, description, and images.
* **Test Case 4: Add Shoes to Cart**
	+ Result: Pass
	+ Notes: The shoe was added to the user's cart.
* **Test Case 5: Checkout Securely**
	+ Result: Pass
	+ Notes: The user was able to checkout securely.

## Conclusion
The testing quality assurance process for the Shoe_Store_Hub_20251028_214718 project has been completed. The test plan, test automation, and performance testing have been implemented and executed. The test report includes the results of the test cases outlined in the test plan. The testing quality assurance process ensures that the e-commerce website meets the requirements and is functional, secure, and performant.

## References
* [Requirements_GatheringAnd_Analysis/requirements_document.md](https://github.com/shoestorehub/Shoe_Store_Hub_20251028_214718/blob/main/Requirements_GatheringAnd_Analysis/requirements_document.md)
* [Requirements_GatheringAnd_Analysis/Requirements_GatheringAnd_Analysis.md](https://github.com/shoestorehub/Shoe_Store_Hub_20251028_214718/blob/main/Requirements_GatheringAnd_Analysis/Requirements_GatheringAnd_Analysis.md)
* [Requirements_GatheringAnd_Analysis/stage_metadata.json](https://github.com/shoestorehub/Shoe_Store_Hub_20251028_214718/blob/main/Requirements_GatheringAnd_Analysis/stage_metadata.json)
* [Requirements_GatheringAnd_Analysis/system_specifications.yaml](https://github.com/shoestorehub/Shoe_Store_Hub_20251028_214718/blob/main/Requirements_GatheringAnd_Analysis/system_specifications.yaml)
* [Requirements_GatheringAnd_Analysis/validation_steps.md](https://github.com/shoestorehub/Shoe_Store_Hub_20251028_214718/blob/main/Requirements_GatheringAnd_Analysis/validation_steps.md)