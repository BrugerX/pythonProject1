from datetime import datetime, timezone
import os
import csv

def getTimeStamp():
    return datetime.now(timezone.utc)

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