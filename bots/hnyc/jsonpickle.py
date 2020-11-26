import json
import jsonpickle
from json import JSONEncoder
from pprint import pprint

class Employee(object):
    def __init__(self, name, salary, address):
        self.name = name
        self.salary = salary
        self.address = address

class Address(object):
    def __init__(self, city, street, pin):
        self.city = city
        self.street = street
        self.pin = pin

address = Address("Alpharetta", "7258 Spring Street", "30004")
employee = Employee("John", 9000, address)

print("Encode Object into JSON formatted Data using jsonpickle")
empJSON = jsonpickle.encode(employee, unpicklable=False)

print("Writing JSON Encode data into Python String")
employeeJSONData = json.dumps(empJSON, indent=4)
print(employeeJSONData)

print("Decode JSON formatted Data using jsonpickle")
EmployeeJSON = jsonpickle.decode(employeeJSONData)
print(EmployeeJSON)

# Let's load it using the load method to check if we can decode it or not.
print("Load JSON using loads() method")
employeeJSON = json.loads(EmployeeJSON)
print(employeeJSON)
