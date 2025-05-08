from transformers import RobertaTokenizer, RobertaForSequenceClassification

# Load from HuggingFace hub
model_name = "roberta-base"  # Or your fine-tuned model if available online
tokenizer = RobertaTokenizer.from_pretrained(model_name)
model = RobertaForSequenceClassification.from_pretrained(model_name)

# Save locally
save_path = "static/roberta_model"
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print("Model and tokenizer saved to static/roberta_model")
