import requests
import typer
import time
import logging
import sys

app = typer.Typer()


@app.command()
def health_check(environment:str):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    url = f"https://{environment}.lightops.io"
    retries = 30
    sleep_time = 30
    Finish = False

    while retries != 0 and not Finish:
        logging.info('Attempting HTTP GET request to ' + url)
        try:
            HttpRequest = requests.get(url)
            if HttpRequest.status_code == 200:
                logging.info('HTTP GET request succeeded')
                Finish = True
                sys.exit(0)
            else:
                logging.info('HTTP GET request failed, trying again in 30 seconds')
                retries -= 1
                time.sleep(sleep_time)
        except Exception as error:
            logging.info('HTTP GET request failed, trying again in 30 seconds')
            print("\033[1m" + "Error: " + "\033[0m" + str(error))
            retries -= 1
            time.sleep(sleep_time)

    logging.info(f"HTTP GET request failed {retries} times")
    sys.exit(1)


if __name__ == "__main__":
    app()
