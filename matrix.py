class Mat:
    def __init__(self,b,h):
        self.hoehe=h
        self.breite=b
        self.matrix=[]
        z=0
        while z < h:
            self.matrix.append([0]*b)
            z=z+1

    @classmethod
    def from_list(cls,l):
        hoehe=len(l)
        breite=len(l[0])
        c=cls(breite,hoehe)
        c.matrix=l
        return(c)

    def __add__(self,other):
        if self.hoehe==other.hoehe and self.breite==other.breite:
            ergebnis=Mat(self.breite,self.hoehe)
            for x in range(0,self.breite):
                for y in range(0,self.hoehe):
                    ergebnis.matrix[y][x]=self.matrix[y][x]+other.matrix[y][x]
            return(ergebnis)
        else:
            return(None)

    def __sub__(self,other):
        if self.hoehe==other.hoehe and self.breite==other.breite:
            ergebnis=Mat(self.breite,self.hoehe)
            for x in range(0,self.breite):
                for y in range(0,self.hoehe):
                    ergebnis.matrix[y][x]=self.matrix[y][x]-other.matrix[y][x]
            return(ergebnis)
        else:
            return(None)
        
    def __mul__(self,other):
        if self.breite==other.hoehe:
            ergebnis=Mat(other.breite,self.hoehe)
            for x in range(0,other.breite):
                for y in range(0,self.hoehe):
                    s=0
                    for i in range(0,self.breite):
                        s=s+self.matrix[y][i]*other.matrix[i][x]
                    ergebnis.matrix[y][x]=s
            return(ergebnis)
        else:
            return(None)

    def apply(self,funct):
        ergebnis=Mat(self.breite,self.hoehe)
        for x in range(0,self.breite):
            for y in range(0,self.hoehe):
                ergebnis.matrix[y][x]=funct(self.matrix[y][x])
        return(ergebnis)

    def transpose(self):
        ergebnis=Mat(self.hoehe,self.breite)
        for x in range(0,self.breite):
            for y in range(0,self.hoehe):
                ergebnis.matrix[x][y]=self.matrix[y][x]
        return(ergebnis)

    def mul(self,other):
        if self.hoehe==other.hoehe and self.breite==other.breite:
            ergebnis=Mat(self.breite,self.hoehe)
            for x in range(0,self.breite):
                for y in range(0,self.hoehe):
                    ergebnis.matrix[y][x]=self.matrix[y][x]*other.matrix[y][x]
            return(ergebnis)
        else:
            return(None)
