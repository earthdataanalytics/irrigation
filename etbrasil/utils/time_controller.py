import time


class TimeController:
    
    __start_time = 0

    def __init__(self):
        pass

    def get_time(self):
        return time.strftime("%Y%m%d-%H%M%S")

    def start_time(self):
        self.__start_time = time.time()

    def end_time(self):
        return time.time() - self.__start_time

    """Decorator
        @TimeP.timeit   
    """

    def timeit(self, func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print("")
            print("==========================TIME WRAPPER==============================")
            time_in_sec = end - start
            time_in_min = time_in_sec / 60
            time_in_hour = time_in_min / 60
            if time_in_hour > 1:
                print(f"Execution time of {func.__name__} is {int(time_in_hour)} hours {int(time_in_min)} minutes {int(time_in_sec)} seconds")
            elif time_in_min > 1:
                print(f"Execution time of {func.__name__} is {int(time_in_min)} minutes {int(time_in_sec)} seconds")
            else:
                print(f"Execution time of {func.__name__} is {int(time_in_sec)} seconds")
            print("====================================================================")
            print("")
            return result

        return wrapper