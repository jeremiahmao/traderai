from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

#https://huggingface.co/ProsusAI/finbert
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
labels = ["positive", "negative", "neutral"]

def estimate_sentiment(news):
    if news:
        tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)

        result = model(tokens["input_ids"], attention_mask=tokens["attention_mask"])["logits"]

        result = torch.nn.functional.softmax(torch.sum(result, 0), dim=-1)
        prob = result[torch.argmax(result)]
        sentiment = labels[torch.argmax(result)]
        return prob, sentiment
    else:
        return 0, labels[-1]
    

if __name__ == "__main__":
    tensor, sentiment = estimate_sentiment(['markets responded POSITIVE to the news!','traders were pleased!'])
    print(tensor, sentiment)
    print("CUDA: " + str(torch.cuda.is_available()))
