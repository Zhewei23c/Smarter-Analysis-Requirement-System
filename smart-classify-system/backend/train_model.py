import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def train_model():
    print("Loading general training data (dataset.csv)...")
    

    try:
        df = pd.read_csv("dataset.csv")
    except FileNotFoundError:
        print("Error: dataset.csv not found. Please create the universal dataset file first.。")
        return


    X = df['text']
    y = df['label']


    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_features=5000)
    X_vectorized = vectorizer.fit_transform(X)


    X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)


    print("Training general model...")
    model = LinearSVC()
    model.fit(X_train, y_train)


    predictions = model.predict(X_test)
    print(f"Model accuracy: {accuracy_score(y_test, predictions)}")
    print(classification_report(y_test, predictions))


    joblib.dump(model, "fr_nfr_model.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")
    print("The general model has been saved as 'fr_nfr_model.pkl'")

if __name__ == "__main__":
    train_model()