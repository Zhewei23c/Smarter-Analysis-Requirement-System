"""
Train (Fine-tune) BERT Model for Requirements Classification
Using Sentence-Transformers with CosineSimilarityLoss
"""
import csv
import os
import shutil
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader
import random

MODEL_NAME = 'all-MiniLM-L6-v2' 
OUTPUT_PATH = './fine_tuned_bert' 
BATCH_SIZE = 16
EPOCHS = 1 

def load_data(filename="dataset.csv"):
    if not os.path.exists(filename):
        print("❌ dataset.csv not found! Run generate_dataset.py first.")
        return []
    
    examples = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
    train_examples = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row['text']
            label = row['label']
            
            if label == "FR":
                anchor = "The system shall perform a function."
                score = 1.0
            elif label == "NFR":
                anchor = "The system performance must be constrained."
                score = 1.0
            else: 
                anchor = "This is random text noise header footer."
                score = 1.0
            
            train_examples.append(InputExample(texts=[text, anchor], label=score))
            
            if label == "Unknown":
                 train_examples.append(InputExample(texts=[text, "The system shall perform a function."], label=0.0))

    return train_examples

def train():
    print(f"📥 Loading base model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    print("📊 Loading and preparing training data...")
    train_examples = load_data()
    

    random.shuffle(train_examples)
    

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
    

    train_loss = losses.CosineSimilarityLoss(model)

    print("🔥 Starting Fine-tuning (this may take 2-5 minutes)...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        warmup_steps=100,
        show_progress_bar=True
    )

    print(f"💾 Saving fine-tuned model to {OUTPUT_PATH}...")

    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
    
    model.save(OUTPUT_PATH)
    print("✅ Training Complete! You can now run app.py")

if __name__ == "__main__":
    train()