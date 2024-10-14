from scrapy.crawler import CrawlerProcess
from course_spider import CourseSpider

# Initialize the Scrapy process
process = CrawlerProcess(settings={
    "FEEDS": {
        "output/courses.csv": {  # Save to CSV file in the "output" folder
            "format": "csv",
            "encoding": "utf8",
            "store_empty": False,
            # Updated fields based on the latest spider changes
            "fields": [
                "course_title",
                "course_type",
                "partnership",
                "skill_level",
                "topic",
                "url",
                "course_description",
                "instructor_name",
                "duration"
            ],  # Specify the fields you want in the CSV
        },
    },
})

# Run the spider
process.crawl(CourseSpider)
process.start()