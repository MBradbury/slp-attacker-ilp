
import subprocess

def trim_whitespace(file):
    if file.endswith('.pdf'):
        subprocess.check_call(["pdfcrop", file, file])
    elif file.endswith('.png'):
        subprocess.check_call(["convert", file, "-trim", file])
    else:
        raise RuntimeError("Unknown file type")
