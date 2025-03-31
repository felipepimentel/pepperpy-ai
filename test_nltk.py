import sys

print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("\nTrying to import NLTK...")

try:
    import nltk

    print("NLTK version:", nltk.__version__)
    print("\nDownloading required data...")
    nltk.download("punkt")
    nltk.download("stopwords")
    nltk.download("wordnet")
    print("\nTesting NLTK functionality...")
    from nltk.tokenize import word_tokenize

    text = "Testing NLTK functionality."
    tokens = word_tokenize(text)
    print("Tokenization result:", tokens)
except Exception as e:
    print("Error:", str(e))
