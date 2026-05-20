"""Estructuras de datos basadas en nodos para uso temporal en memoria."""


class Node:
    """Nodo simple para listas enlazadas y colas."""

    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    """Lista enlazada simple para procesar colecciones grandes en memoria."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, value):
        node = Node(value)
        if self.tail:
            self.tail.next = node
            self.tail = node
        else:
            self.head = node
            self.tail = node
        self.size += 1

    def __iter__(self):
        current = self.head
        while current:
            yield current.value
            current = current.next

    def find(self, predicate):
        current = self.head
        while current:
            if predicate(current.value):
                return current.value
            current = current.next
        return None

    def to_list(self):
        return [value for value in self]

    def __len__(self):
        return self.size


class Queue:
    """Cola FIFO implementada con nodos."""

    def __init__(self):
        self.front = None
        self.rear = None
        self.size = 0

    def enqueue(self, value):
        node = Node(value)
        if self.rear:
            self.rear.next = node
            self.rear = node
        else:
            self.front = node
            self.rear = node
        self.size += 1

    def dequeue(self):
        if not self.front:
            return None
        node = self.front
        self.front = node.next
        if self.front is None:
            self.rear = None
        self.size -= 1
        return node.value

    def __len__(self):
        return self.size
