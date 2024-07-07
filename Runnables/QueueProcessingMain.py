import threading
import database.DatabaseManager as dbm
import pq.python.pq.Queue as q
import Runnables.JobManager as jb
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import utility.LoggingUtility as lut

# Email configuration
SMTP_SERVER = 'smtp.example.com'  # Replace with your SMTP server
SMTP_PORT = 587  # Typically 587 for TLS
SMTP_USERNAME = 'your_email@example.com'  # Replace with your email
SMTP_PASSWORD = 'your_password'  # Replace with your email password
EMAIL_FROM = 'your_email@example.com'  # Replace with your email
EMAIL_TO = 'recipient_email@example.com'  # Replace with recipient's email
EMAIL_SUBJECT = 'Exception in Threaded Job Manager'

def send_exception_email(exception_message):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = EMAIL_SUBJECT

    body = f"An exception occurred: {exception_message}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
def run_job_manager(rbq):
    try:
        rbq.main("scheduling")
    except KeyboardInterrupt:
        print("Keyboard interrupt received, stopping...")
        rbq.stop()
    except Exception as e:
        exception_message = str(e)
        print(f"Exception in thread: {exception_message}")
        send_exception_email(exception_message)
        rbq.stop()

if __name__ == "__main__":
    # List to keep track of threads and job managers
    threads = []
    job_managers = []

    parser = argparse.ArgumentParser(description="Run job managers in multiple threads.")
    parser.add_argument(
        "--num-threads",
        type=int,
        default=3,
        help="Number of threads to run (default: 3)"
    )

    args = parser.parse_args()

    # Number of threads to run
    num_threads = args.num_threads

    for _ in range(num_threads):
        # Initialize job manager
        conn = dbm.getPsycopg2Conn()
        Q = q.PQ(conn)
        q_dict = {"scheduling": Q["scheduling"]}
        rbq = jb.WeightedInserter(q_dict, v=1)
        job_managers.append(rbq)

        # Initialize and start a new thread
        thread = threading.Thread(target=run_job_manager, args=(rbq,))
        thread.start()
        threads.append(thread)

    try:
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("Main program interrupt received, stopping all threads...")
        #send_exception_email("Main program interrupted by KeyboardInterrupt.")
        for rbq in job_managers:
            rbq.stop()  # Call the stop method of each job manager instance
        for thread in threads:
            thread.join()
    except Exception as e:
        exception_message = str(e)
        print(f"Exception in main program: {exception_message}")
        #send_exception_email(exception_message)
        lut.save_message(exception_message,r"C:\Users\DripTooHard\PycharmProjects\pythonProject1\Runnables\Errors\QueueProcessorError","Error Processing Q ")
        for rbq in job_managers:
            rbq.stop()  # Call the stop method of each job manager instance
        for thread in threads:
            thread.join()
