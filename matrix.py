import numpy as np

class Mat:
    """
    Optimierte Matrix-Klasse für neuronale Netze mit NumPy.
    
    Diese Klasse verwendet NumPy für schnelle vektorisierte Matrixoperationen,
    ideal für maschinelles Lernen und neuronale Netze.
    """
    
    def __init__(self, width, height, values=None):
        """
        Initialisiert eine Matrix mit Nullen oder gegebenen Werten.
        
        Args:
            width: Breite der Matrix (Spalten)
            height: Höhe der Matrix (Zeilen)
            values: Optional - NumPy Array oder Liste von Werten
        """
        # Shape als (height, width) für NumPy Konvention: rows × columns
        if values is None:
            # Schnelle Initialisierung mit Nullen
            self.data = np.zeros((height, width), dtype=np.float32)
        else:
            # Konvertiere zu NumPy Array mit float32 für GPU-Kompatibilität
            self.data = np.array(values, dtype=np.float32)
        
        self.height = height
        self.width = width

    @classmethod
    def from_list(cls, data_list):
        """
        Erstellt eine Matrix aus einer Python-Liste.
        
        Args:
            data_list: 2D Python-Liste
            
        Returns:
            Mat: Neue Matrix mit den Listendaten
        """
        # NumPy erkennt automatisch die Dimensionen
        arr = np.array(data_list, dtype=np.float32)
        height, width = arr.shape
        mat = cls(width, height)
        mat.data = arr
        return mat

    @classmethod
    def random(cls, width, height, mean=0, std=1):
        """
        Erstellt eine Matrix mit zufälligen Werten (wichtig für Neural Network Initialisierung).
        
        Args:
            width: Breite der Matrix
            height: Höhe der Matrix
            mean: Durchschnitt der Normalverteilung (Standard: 0)
            std: Standardabweichung (Standard: 1, für Xavier oft: sqrt(2/(n_in+n_out)))
            
        Returns:
            Mat: Matrix mit Zufallswerten
        """
        mat = cls(width, height)
        # Verwendet Normalverteilung - besser als uniform für neuronale Netze
        mat.data = np.random.normal(mean, std, (height, width)).astype(np.float32)
        return mat

    def __add__(self, other):
        """
        Addiert zwei Matrizen (vektorisiert mit NumPy).
        
        Operationen: C = A + B
        """
        # Shape-Überprüfung
        if self.height != other.height or self.width != other.width:
            raise ValueError(f"Matrix-Dimensionen passen nicht: {self.shape} vs {other.shape}")
        
        # NumPy macht dies in C - viel schneller als Python-Schleifen
        result = Mat(self.width, self.height)
        result.data = self.data + other.data
        return result

    def __sub__(self, other):
        """
        Subtrahiert zwei Matrizen (vektorisiert mit NumPy).
        
        Operation: C = A - B
        """
        if self.height != other.height or self.width != other.width:
            raise ValueError(f"Matrix-Dimensionen passen nicht: {self.shape} vs {other.shape}")
        
        result = Mat(self.width, self.height)
        result.data = self.data - other.data
        return result
        
    def __matmul__(self, other):
        """
        Matrixmultiplikation (nicht element-weise).
        
        Wenn A ist (m×n) und B ist (n×p), dann ist A@B (m×p)
        Dies ist die wichtigste Operation in neuronalen Netzen: output = input @ weights
        """
        # Dimensionsüberprüfung: Spalten von A müssen = Zeilen von B sein
        if self.width != other.height:
            raise ValueError(
                f"Kann nicht multiplizieren: ({self.height}×{self.width}) @ ({other.height}×{other.width})"
            )
        
        result = Mat(other.width, self.height)
        # @ ist NumPy's schnelle Matrixmultiplikation (BLAS-Bibliothek)
        result.data = self.data @ other.data
        return result

    def apply(self, func):
        """
        Wendet eine Funktion auf alle Elemente der Matrix an (element-weise).
        
        Dies wird für Aktivierungsfunktionen verwendet:
        - ReLU: max(0, x)
        - Sigmoid: 1/(1+e^-x)
        - Tanh: (e^x - e^-x)/(e^x + e^-x)
        
        Args:
            func: Funktion die auf jedes Element angewendet wird
            
        Returns:
            Mat: Neue Matrix mit angewendeter Funktion
        """
        result = Mat(self.width, self.height)
        # NumPy's vectorize erlaubt Python-Funktionen, aber NumPy native Funktionen sind schneller
        result.data = np.vectorize(func, otypes=[np.float32])(self.data)
        return result

    def transpose(self):
        """
        Transponiert die Matrix (vertauscht Zeilen und Spalten).
        
        Dies ist wichtig für Backpropagation und Gewichts-Updates.
        (m×n)^T = (n×m)
        """
        result = Mat(self.height, self.width)
        # .T ist die NumPy Transpose-Operation - sehr schnell
        result.data = self.data.T
        return result

    def mul_elementwise(self, other):
        """
        Element-weise Multiplikation (Hadamard Produkt) von zwei Matrizen.
        
        Anders als __mul__: Dies multipliziert entsprechende Elemente direkt.
        Wird oft für Masking und Gradient-Propagation verwendet.
        
        Args:
            other: Andere Matrix mit gleicher Größe
            
        Returns:
            Mat: Matrix mit element-weisen Produkten
        """
        if self.height != other.height or self.width != other.width:
            raise ValueError(f"Matrix-Dimensionen passen nicht: {self.shape} vs {other.shape}")
        
        result = Mat(self.width, self.height)
        # * ist element-weise Multiplikation in NumPy
        result.data = self.data * other.data
        return result

    def __repr__(self):
        """Schöne Darstellung der Matrix für Debugging"""
        return f"Mat({self.width}×{self.height})\n{self.data}"

    @property
    def shape(self):
        """Gibt die Form der Matrix als Tuple zurück: (höhe, breite)"""
        return (self.height, self.width)

    def sum(self):
        """Summiert alle Elemente der Matrix (z.B. für Kostenfunktion)"""
        return np.sum(self.data)

    def mean(self):
        """Berechnet den Durchschnitt aller Elemente"""
        return np.mean(self.data)

    def flatten(self):
        """Wandelt Matrix in 1D Array um (für Eingabe in vollständig verbundene Layer)"""
        return self.data.flatten()


# Schneller Performance-Test: python matrix.py
if __name__ == "__main__":
    import time
    
    print("\n🚀 PERFORMANCE-BENCHMARK\n")
    
    # Test Matrixmultiplikation
    A = Mat.random(1000, 1000)
    B = Mat.random(1000, 1000)
    
    start = time.time()
    for _ in range(10):
        C = A @ B
    elapsed = time.time() - start
    
    gflops = (10 * 2 * 1000**3) / elapsed / 1e9
    print(f"Matrixmultiplikation (1000×1000): {elapsed*1000:.1f}ms für 10x | {gflops:.1f} GFLOPS\n")
    
    # Test Addition
    start = time.time()
    for _ in range(1000):
        C = A + B
    elapsed = time.time() - start
    
    print(f"Addition (1000×1000): {elapsed*1000:.1f}ms für 1000x\n")
    
    print("✓ NumPy Optimierung aktiv - 100-1000x schneller als reine Python!\n")
