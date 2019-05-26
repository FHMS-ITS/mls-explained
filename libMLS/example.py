import libmls   #  <-- Import the Rust implemented module (mlslib.so)

def hello():
    print(libmls.hello())

hello()
