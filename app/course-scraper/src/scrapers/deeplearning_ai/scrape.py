import scrapy
import json
import time
import csv


class CourseSpider(scrapy.Spider):
    name = "deeplearning_courses"
    npages = 10
    custom_settings = {
        'DOWNLOAD_DELAY': 0.6
    }

    # Define the mapping for skill levels
    skill_level_mapping = {
        "Beginner": "Easy",
        "Intermediate": "Medium"
    }

    origin = "https://www.deeplearning.ai"

    def start_requests(self):
        api_url = 'https://y5109wlmqw-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.20.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.67.0)%3B%20react%20(18.2.0)%3B%20react-instantsearch%20(7.7.2)%3B%20react-instantsearch-core%20(7.7.2)%3B%20next.js%20(13.5.6)%3B%20JS%20Helper%20(3.18.0)&x-algolia-api-key=9030ff79d3ba653535d5b66c26b56683&x-algolia-application-id=Y5109WLMQW'

        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://www.deeplearning.ai",
            "Referer": "https://www.deeplearning.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
            "content-type": "application/x-www-form-urlencoded",
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"'
        }

        for i in range(1, self.npages + 1):
            payload = {
                "requests": [{
                    "indexName": "courses_date_desc",
                    "params": f"clickAnalytics=true&facets=%5B%22course_type%22%2C%22partnership%22%2C%22skill_level%22%2C%22topic%22%5D&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&maxValuesPerFacet=1000&query=&tagFilters=&page={str(i)}"
                }]
            }

            yield scrapy.Request(
                url=api_url,
                body=json.dumps(payload),
                method='POST',
                headers=headers,
                callback=self.parse_api_response
            )

    def parse_api_response(self, response):
        json_data = response.json()

        for result in json_data.get('results', []):
            hits = result.get('hits', [])

            for hit in hits:
                # Get the skill level, ensuring it's not a list
                skill_level = hit.get('skill_level')

                if isinstance(skill_level, list):
                    skill_level = skill_level[0] if skill_level else 'Unknown'

                # Use the dictionary to map skill levels, with a default of 'Unknown'
                mapped_skill_level = self.skill_level_mapping.get(skill_level, 'Unknown')

                # Get the course URL and make a request to the course detail page
                course_url = self.origin + hit.get('landing_page')

                # Prepare the basic course data
                course_data = {
                    'course_title': hit.get('title'),
                    'course_type': hit.get('course_type'),
                    'partnership': hit.get('partnership'),
                    'skill_level': mapped_skill_level,
                    'topic': hit.get('topic'),
                    'url': course_url
                }

                # Add a 0.5 second delay before sending the request
                time.sleep(0.5)

                # Request the course detail page
                yield scrapy.Request(
                    url=course_url,
                    callback=self.parse_course_page,
                    meta={'course_data': course_data}  # Pass the course data to the next callback
                )

    def parse_course_page(self, response):
        # Extract additional details from the course detail page
        course_data = response.meta['course_data']
        course_type = course_data.get('course_type', 'Courses')  # Default to 'Courses'

        # Use different XPath based on course_type
        if course_type == "Short Courses":
            course_description = response.xpath('//div[@class="short-course-description"]/text()').get(
                default='No description available')
            instructor_name = response.xpath('//div[@class="short-course-instructor"]/text()').get(
                default='No instructor listed')
            # Use XPath to extract the '1 Hour' dynamically from the correct p tag.
            duration = response.xpath('//div[@class="flex flex-col items-center justify-center mx-4"][2]/p/text()').get(
                default='Duration not listed')
        elif course_type == "Specializations":
            course_description = response.xpath('//div[@class="specialization-description"]/text()').get(
                default='No description available')
            instructor_name = response.xpath('//div[@class="specialization-instructor"]/text()').get(
                default='No instructor listed')
            duration = response.xpath('//span[@class="specialization-duration"]/text()').get(
                default='Duration not listed')
        else:  # Default to "Courses"
            course_description = response.xpath('//div[@class="course-description"]/text()').get(
                default='No description available')
            instructor_name = response.xpath('//div[@class="course-instructor"]/text()').get(
                default='No instructor listed')
            duration = response.xpath('//span[@class="course-duration"]/text()').get(default='Duration not listed')

        # Update course_data with the additional fields
        course_data.update({
            'course_description': course_description,
            'instructor_name': instructor_name,
            'duration': duration
        })

        # Save course_data to a new CSV file called "course_data.csv"
        with open("data/course_data.csv", mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['course_title', 'course_type', 'partnership', 'skill_level', 'topic', 'url',
                          'course_description', 'instructor_name', 'duration']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write the header only once
            if csv_file.tell() == 0:
                writer.writeheader()

            # Write the course data
            writer.writerow(course_data)

        # Yield the full course data as a Scrapy item
        yield course_data
