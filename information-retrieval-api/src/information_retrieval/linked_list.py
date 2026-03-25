import logging


logger = logging.getLogger(__name__)


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self, data=None):
        self.head = None
        if data is not None:
            self.insert(data)

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next            

    def is_empty(self):
        return self.head is None

    def insert(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return
        current_node = self.head
        while(current_node.next):
            current_node = current_node.next
        current_node.next = new_node
            
    def insertSorted(self, data):
        new_node = Node(data)
        if self.is_empty(): 
            self.head = new_node
        elif self.head.data > data: # if the data is smaller than the head
            new_node.next = self.head
            self.head = new_node
        elif self.head.data == data: # if the data is equal to the head, don't insert it again
            return
        else:
            current = self.head
            while current.next and current.next.data < new_node.data: # find the right position to insert
                current = current.next
                
            if current.next is not None and current.next.data == new_node.data:   # if the data is already in the next node, don't insert it again
                return   
                
            new_node.next = current.next # insert the new node
            current.next = new_node
        
    def delete(self, data):
        if self.is_empty():
            return

        if self.head.data == data:
            self.head = self.head.next
            return

        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                return
            current = current.next

    def search(self, data):
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False

    def display(self):
        current = self.head
        values = []
        while current:
            values.append(str(current.data))
            current = current.next
        logger.info("%s", " ".join(values))
        
    def length(self):
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count
        