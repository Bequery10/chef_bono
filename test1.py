class Chat:
    def __init__(self, id):
        self.id = id
        self.data = None

    def get_id(self):
        return self.id


class Other:

    def print_chat_data(self):
        chat1 = Chat(1)
        chat1.data = "Hello, this is chef bono!"

        chat2 = Chat(2)
        print(chat1.data)


printer = Other()

printer.print_chat_data()
