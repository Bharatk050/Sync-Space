# Generated on: 2025-10-28 21:56:21

import time
from hello_world import print_hello_world

def measure_execution_time():
    start_time = time.time()
    print_hello_world()
    end_time = time.time()
    execution_time = end_time - start_time
    return execution_time

if __name__ == "__main__":
    execution_time = measure_execution_time()
    print(f"Execution time: {execution_time} seconds")