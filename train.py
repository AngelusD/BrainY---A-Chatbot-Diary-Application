import datasets
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from torch.optim import AdamW
from tqdm import tqdm
import os
import json
from torch.nn.utils.rnn import pad_sequence 
import os
import pickle
import tensorflow as tf
import tensorflow as tf
from transformers import TFBlenderbotSmallForConditionalGeneration, BlenderbotSmallTokenizer


# # Model hyperparameters
# BATCH_SIZE = 4
# LEARNING_RATE = 5e-5
# MAX_LENGTH = 256

# # Cache conversation histories and attributes for each user
# user_data = {}

# # Load pre-trained model
# tokenizer = BlenderbotSmallTokenizer.from_pretrained("facebook/blenderbot_small-90M")
# model = TFBlenderbotSmallForConditionalGeneration.from_pretrained("facebook/blenderbot_small-90M")

# def train_model(): 
#     optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE, weight_decay=0.01) 
#     model.compile(optimizer=optimizer)
    
#     # Concatenate conversations and tokenize 
#     concat_input = ""
#     for user_id, conversation in user_data.items():
#         concat_input += " ".join(turn for turn in conversation) + " "
#     inputs = tokenizer.batch_encode_plus([concat_input], max_length=MAX_LENGTH, pad_to_max_length=True)
    
#     # Train model
#     for epoch in range(3):
#         print(f"Epoch {epoch+1}")
#         batches = []
#         for i in range(0, len(concat_input), BATCH_SIZE):
#             batch = {k:v[i:i+BATCH_SIZE] for k,v in inputs.items()}
#             batches.append(batch)
#         for batch in batches:
#             model.train_on_batch(x=batch, y=batch)
            
#     # Save model        
#     model.save("chatbot_model")




# # Load data from data_intermediate.json file and preprocess it into a suitable format for training.
# def load_and_preprocess_data(file_path):
#     with open(file_path) as f:
#         data = json.load(f)
#     dialogs = []
#     for d in data:
#         dialog_text = ""
#         for msg in d["dialog"]:
#             dialog_text += msg["sender"] + ": " + msg["text"] + "\n"
#         dialogs.append(dialog_text.strip())
#     return dialogs

# # Prepare dataset from the preprocessed data using HuggingFace's DatasetDict class.
# def create_dataset(data):
#     dataset_dict = datasets.DatasetDict(
#         {"train": datasets.Dataset.from_dict({"dialogs": data})})
#     return dataset_dict['train']

# file_path = "data_intermediate.json"
# preprocessed_data = load_and_preprocess_data(file_path)
# dataset = create_dataset(preprocessed_data)

# # Set environment variable (replace with your token)
# os.environ["HF_AUTH_TOKEN"] = "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"


# # Load pretrained model and tokenizer
# model = AutoModelForCausalLM.from_pretrained('microsoft/DialoGPT-medium')
# tokenizer = AutoTokenizer.from_pretrained('microsoft/DialoGPT-medium')

# # Add padding token and set pad_token_id
# tokenizer.pad_token = tokenizer.eos_token
# pad_token_id = tokenizer.convert_tokens_to_ids(tokenizer.pad_token)
# model.pad_token_id = pad_token_id

# # Set model type
# model.config.model_type = 'dialogpt'

# def collate_fn(examples):
#     sequences = [torch.tensor(tokenizer.encode(seq, truncation=True)) for seq in examples]
#     sequence_lengths = torch.tensor(list(map(len, sequences)))
#     sequences_padded = pad_sequence(sequences, batch_first=True, padding_value=pad_token_id)  # Change this line
#     return {'input_ids': sequences_padded,
#             'attention_mask': sequences_padded != pad_token_id,
#             'sequence_lengths': sequence_lengths,
#             'labels': sequences_padded}

# # Define the training hyperparameters
# epochs = 2
# batch_size = 2
# lr = 5e-5

# train_dataloader = torch.utils.data.DataLoader(dataset['dialogs'],
#                                                batch_size=batch_size,
#                                                collate_fn=collate_fn)

# # Define the optimizer and loss function
# optimizer = AdamW(model.parameters(), lr=lr)
# loss_fn = torch.nn.CrossEntropyLoss()

# # Train the model
# for epoch in range(epochs):
#     losses = []
#     for batch in tqdm(train_dataloader):
#         inputs = batch
#         labels = batch['labels']
#         outputs = model(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'])
#         loss = loss_fn(outputs.logits.view(-1, outputs.logits.size(-1)), labels.view(-1))
#         loss.backward()
#         optimizer.step()
#         optimizer.zero_grad()
#         losses.append(loss.item())
        
#     print(f'Epoch {epoch+1}, Loss: {torch.mean(torch.tensor(losses))} ')

# # Save model and tokenizer to Hugging Face Hub
# model.push_to_hub('AngelusD/BrainYweB')
# tokenizer.push_to_hub('AngelusD/BrainYweB')

# # Load model and tokenizer from Hugging Face Hub (for testing purposes)
# model_test_path='AngelusD/BrainYweB'
# tokenizer_test_path='AngelusD/BrainYweB'

# model_test=AutoModelForCausalLM.from_pretrained(model_test_path)
# tokenizer_test=AutoTokenizer.from_pretrained(tokenizer_test_path)

