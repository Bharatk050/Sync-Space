# Generated on: 2025-10-28 21:56:42

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_hello_world():
    """Prints 'hello world' to the console."""
    logger.info('Printing hello world')
    print('hello world')

if __name__ == "__main__":
    print_hello_world()