from datetime import datetime, timezone,date
import os
import csv
import json



def getTimeStamp():
    return datetime.now(timezone.utc)


def parse_timestamp(timestamp_str):
    # Define the format of the input string
    timestamp_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    # Parse the string into a datetime object
    dt_object = datetime.strptime(timestamp_str, timestamp_format)

    return dt_object

def dateTimeJsonDumps(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def serializeWithDates(data):
    """Serialize a dictionary containing date and datetime objects to a JSON string"""
    return json.dumps(data, default=dateTimeJsonDumps)

# Function to generate the filename based on the scraping start timestamp
def generate_filename(scraping_start_timestamp):
    return scraping_start_timestamp.strftime("%Y-%m-%d-%H.csv")


# Function to write exceptions to a CSV file
def logExceptionsToCsv(exceptions, scraping_start_timestamp,columns, directory):
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Generate the filename
    filename = generate_filename(scraping_start_timestamp)
    filepath = os.path.join(directory, filename)

    # Write the exceptions to the CSV file
    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the header if the file is new
        if file.tell() == 0:
            writer.writerow(columns)

        for exception in exceptions:
            writer.writerow(exception)