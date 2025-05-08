from kagglehub import dataset_download
import pandas as pd
from sklearn.model_selection import train_test_split

def load_resume_dataset():
    # Download and read dataset
    ds = dataset_download("saugataroyarghya/resume-dataset")
    csv_path = ds.path + "/UpdatedResumeDataSet.csv"
    df = pd.read_csv(csv_path)

    # Create dynamic label mappings
    unique_labels = df['Category'].unique()
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    # Apply label encoding
    df['Category'] = df['Category'].map(label2id)

    # Train-test split
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df["Resume"], df["Category"], test_size=0.2, random_state=42
    )

    return train_texts, val_texts, train_labels, val_labels, label2id, id2label
