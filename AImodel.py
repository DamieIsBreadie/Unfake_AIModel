import torch
import torch.nn as nn
from transformers import BertModel, BertTokenizer


# ------------------ Configuration ------------------
class Config:
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    BASE_MODEL = 'bert-base-uncased'
    MAX_LEN = 512
    BATCH_SIZE = 32
    NUM_WORKERS = 4
    TEMPERATURE = 4.0
    MODEL_PATH = "Unfake_v3.pth"


# ------------------ Model Definition ------------------
class FakeNewsClassifier(nn.Module):
    def __init__(self, dropout_rate=0.3):
        super().__init__()
        self.bert = BertModel.from_pretrained(Config.BASE_MODEL)
        self.dropout = nn.Dropout(dropout_rate)
        # Three parallel CNN blocks with kernel sizes 3, 4, and 5
        self.conv3 = nn.Conv1d(self.bert.config.hidden_size, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv1d(self.bert.config.hidden_size, 128, kernel_size=4, padding=1)
        self.conv5 = nn.Conv1d(self.bert.config.hidden_size, 128, kernel_size=5, padding=1)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.activation = nn.ReLU()
        self.classifier = nn.Sequential(
            nn.Linear(384, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, 2)
        )

    def forward(self, input_ids, attention_mask):
        bert_output = self.bert(input_ids, attention_mask)
        # Permute output to shape (batch, hidden_size, seq_len) for CNN layers
        sequence_output = bert_output.last_hidden_state.permute(0, 2, 1)
        conv3_out = self.pool(self.activation(self.conv3(sequence_output))).squeeze(-1)
        conv4_out = self.pool(self.activation(self.conv4(sequence_output))).squeeze(-1)
        conv5_out = self.pool(self.activation(self.conv5(sequence_output))).squeeze(-1)
        combined = torch.cat([conv3_out, conv4_out, conv5_out], dim=1)
        return self.classifier(self.dropout(combined))


# -------- Load Model --------
def load_model(model_path="Unfake_v3.pth"):
    model = FakeNewsClassifier()
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    return model


# -------- Load BERT Tokenizer --------
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")


# -------- Text Preprocessing --------
def text_preprocessing(text):
    tokens = tokenizer(
        text,
        max_length=512,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    return tokens["input_ids"], tokens["attention_mask"]


# -------- Make Predictions --------
def model_predict(text, model):
    """"Returns prediction and confidence scores"""
    input_ids, attention_mask = text_preprocessing(text)
    input_ids, attention_mask = input_ids.to(torch.device("cpu")), attention_mask.to(torch.device("cpu"))

    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        probs = torch.softmax(logits, dim=1)
        label = "Fake" if probs[0][0] > probs[0][1] else "Real"
        confidence = probs[0].tolist()

    return label, confidence
