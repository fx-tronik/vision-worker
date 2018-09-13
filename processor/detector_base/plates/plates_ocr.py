from time import sleep

class PlatesOCR:
    def __init__(self, path):
        print("Jestem w init")
    def __del__(self):
        # self.persistent_sess.close()
        pass

    def inference(self, image):
        print("Jestem w inference")
        sleep(1)
        return 25