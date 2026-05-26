import random
import matrix
import math

# Logistische Funktion:
def logistic_function(x):
    return(1.0/(1.0+math.exp(-x)))

# Definiere ein 4->1 Netz
layera=matrix.Mat(1,4)
layera.matrix=[[random.random()],[random.random()],[random.random()],[random.random()]]

# Funktion zur Auswertung des Netzes für einen Input
def forward(inp,bias):
    status=matrix.Mat(4,1)
    status.matrix=[[inp[0]+bias,inp[1]+bias,inp[2]+bias,inp[3]+bias]]
    status=status.apply(logistic_function)
    status=(status*layera)
    status.matrix[0][0]=status.matrix[0][0]+bias
    status=status.apply(logistic_function)
    return(status.matrix[0][0])

# Trainingsdaten
tr_data=[
    [[0,0,0,0],0],
    [[0,0,0,1],0],
    [[0,0,1,0],0],
    [[0,0,1,1],0],
    [[0,1,0,0],0],
    [[0,1,0,1],0],
    [[0,1,1,0],0],
    [[0,1,1,1],0],
    [[1,0,0,0],1],
    [[1,0,0,1],1],
    [[1,0,1,0],1],
    [[1,0,1,1],1],
    [[1,1,0,0],1],
    [[1,1,0,1],1],
    [[1,1,1,0],1],
    [[1,1,1,1],1]    
    ]

# Methode zum Testen des Netzes:
def test(bias):
    e=0.0
    for entry in tr_data:
        o=forward(entry[0],bias)
        t=entry[1]
        e=e+0.5*(o-t)**2
        print(str(entry[0])+"->"+str(t)+":"+str(o))
    e=(e**0.5)/len(tr_data)
    return(e)

def fehler(bias):
    e=0.0
    for entry in tr_data:
        o=forward(entry[0],bias)
        t=entry[1]
        e=e+0.5*(o-t)**2
    e=(e**0.5)/len(tr_data)
    return(e)

# Trainingsschritt
def trainingsschritt(inp,t,lam,bias):
    o=forward(inp,bias)
    for i in [0,1,2,3]:
         d=(o-t)*o*(1-o)*logistic_function(inp[i])
         layera.matrix[i][0]=layera.matrix[i][0]-d*lam

def training(lam,epochen,bias):
    for i in range(0,epochen):
        for entry in tr_data:
            trainingsschritt(entry[0],entry[1],lam,bias)
        if i%100==0:
            f=fehler(bias)
            print(str(i)+":"+str(f))
