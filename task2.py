import time
from typing import Optional
import numpy as np
import bcrypt
import multiprocessing as mp

if mp.get_context().get_start_method(allow_none=True) is None:
    mp.set_start_method("spawn")

DICT_FILENAME = "nltk_data/corpora/words/en"
NUM_WORKERS = 1


def crack_password(password_hash: bytes, num_workers: int = 1) -> Optional[str]:

    def worker(partition, partition_index, found_password_index):
        for i, password in enumerate(partition):
            password = password.encode("utf-8")
            if bcrypt.checkpw(password, password_hash):  # true if password is correct
                with found_password_index.get_lock():
                    found_password_index.value = partition_index + i
                return

    with open(DICT_FILENAME, "r") as wordlist:
        words = np.array(wordlist.read().splitlines())

    partitions = np.array_split(words, num_workers)
    index_value = mp.Value("i", -1)
    workers = []
    partition_i = 0
    for partition in partitions:
        w = mp.Process(target=worker, args=(partition, partition_i, index_value))
        w.start()
        workers.append(w)
        partition_i += len(partition)

    while True:
        if index_value.value != -1:
            for w in workers:
                w.terminate()
            with open(DICT_FILENAME, "r") as wordlist:
                return wordlist.read().splitlines()[index_value.value]
        elif all([not w.is_alive() for w in workers]):
            return
        time.sleep(0.1)


if __name__ == "__main__":
    with open("shadow.txt", "r") as shadow_file:
        shadow = shadow_file.read().splitlines()
    with open("cracked.txt", "w") as cracked_file:
        pass
    for line in shadow:
        user, password_str = line.split(":")
        print(f"Cracking password for {user}")
        start_time = time.time()

        result = crack_password(password_str.encode(), NUM_WORKERS)
        if result is None:
            print(f"{user} password not found")
        else:
            print(f"{user} password found:", result)
        duration = time.time() - start_time
        print(f"Time taken: {duration}s")

        with open("cracked.txt", "a") as cracked_file:
            cracked_file.write(f"{user}:{result}, time:{duration}\n")
