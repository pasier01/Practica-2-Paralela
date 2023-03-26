"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        '''
        Creamos tres listas que indican el número que cruza, el número esperando 
        y una variable condición para los coches del norte, coches del 
        sur y peatones respectivamente
        '''
        self.number=[Value('i', 0),Value('i', 0), Value('i', 0)]
        self.waiting=[Value('i', 0),Value('i', 0), Value('i', 0)]
        self.cond=[Condition(self.mutex),Condition(self.mutex),Condition(self.mutex) ]
        self.turn = Value ('i', 0) #Cars_north: 0, Cars_south: 1, Ped: 2
    
    def ped(self): 
        return self.number[0].value == 0 and self.number[1].value == 0 \
    
    def car_north(self): 
        return self.number[2].value == 0 and self.number[1].value == 0 \
    
    def car_south(self):
        return self.number[2].value == 0 and self.number[0].value == 0 \
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == 0:
            self.waiting[0].value += 1
            self.cond[0].wait_for(self.car_north)
            self.waiting[0].value -= 1
            self.turn.value = 0
            self.number[0].value += 1
        elif direction == 1:
            self.waiting[1].value += 1
            self.cond[1].wait_for(self.car_south)
            self.waiting[1].value -= 1
            self.turn.value = 1
            self.number[1].value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        self.number[direction].value -= 1
        if direction == 0:
            if not self.waiting[1].value == 0:
                self.turn.value = 1
            elif not self.waiting[2].value == 0:
                self.turn.value = 2
            if self.number[0].value == 0:
                self.cond[1].notify_all()
                self.cond[2].notify_all()       
        elif direction == 1:
            if not self.waiting[2].value == 0:
                self.turn.value = 2
            elif not self.waiting[0].value == 0:
                self.turn.value = 0
            if self.number[1].value == 0:
                self.cond[2].notify_all()
                self.cond[0].notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.waiting[0].value += 1
        self.cond[0].wait_for(self.ped)
        self.waiting[0].value -= 1
        self.turn.value = 2
        self.number[0].value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.number[0].value -= 1 
        if not self.waiting[1].value == 0:
            self.turn.value = 0 
        elif not self.waiting[2].value == 0: 
            self.turn.value = 1 
        if self.number[0].value == 0: 
            if not self.waiting[1].value == 0: 
                self.cond[1].notify_all() 
            else:
                self.cond[2].notify_all()  
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north(factor=4) -> None:
    time.sleep(random.random())

def delay_car_south(factor=4) -> None:
    time.sleep(random.random())

def delay_pedestrian(factor=2) -> None:
    time.sleep(random.random())

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    if direction==0:
        way='North'
    else:
        way='South'
    print(f"car {cid} heading {way} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {way} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {way} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {way} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()

if __name__ == '__main__':
    main()
