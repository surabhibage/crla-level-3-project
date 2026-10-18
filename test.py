import random as rn;
import pandas as pd;

## somehow put everyone's name into a list/central area to access as we need.
##a = input("Can you list the names? ");
##a = [a];
names = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"]
tinkerToys = []
scenarios = []
teaching = []


##randomly assign names into groups
for name in names:
  groupNumber = rn.randint(1,3); # fix name matching to each 
  if groupNumber == 1:
    tinkerToys.append(name)
    tinkerToys = sorted(tinkerToys)
  elif groupNumber == 2:
    scenarios.append(name)
  elif groupNumber == 3:
    teaching.append(name)
print("names in tinkertoys", tinkerToys)


b = input("Are you a pro staff y/n").lower()
if b == "y":
  ##add a bit to check which room you are in

  ##for now, this is the code assuming you are in the tinker toys room
  ## idk how to code a dropdown menu but this might be where it'd go basically
  usedNames = []
  nameCounter = 0
  for i in tinkerToys:
    nameCounter += 1
  while usedNames != tinkerToys:
    c = input("Who are you observing: ").lower()
    c = str(c)
    if c in usedNames:
      print("name already used")
      nameCounter += 1
    elif c in tinkerToys:
      d = str(input("would you like to work with them? ").lower)
      ## somehow put result into a matrix that corresponds to each person's name
      e = int(input("talking skills (1-4): "))
      usedNames.append(c)
      usedNames = sorted(usedNames)
    else:
       print("This person doesn't exits")
elif b == "n":
  print("No pro staff bit yet")
  ## basically copy the above logic.