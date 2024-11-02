# -*- coding: utf-8 -*-
"""AIHW3_FashionMNIST.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PClsSM09xmwKs3jOcdG4RZU_mVno9gln
"""

import numpy as np
import pickle
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets
from torchvision.transforms import ToTensor, transforms

#data preparation
data = datasets.FashionMNIST(root= "data", train = True,download = True, transform = transforms.ToTensor())

num_train = 40000
num_valid = 10000
num_test = 10000

train_data, valid_data, test_data = random_split(data, [num_train, num_valid, num_test])

train_dataloader = DataLoader(train_data, batch_size = 64, shuffle = True)
valid_dataloader = DataLoader(valid_data, batch_size = 64, shuffle = True)
test_dataloader = DataLoader(test_data, batch_size = 64, shuffle = True)

# MLP Class
class MLP(nn.Module):
    def __init__(self, input, hidden, output, activation_fun, optimizer_method, alpha,device):
        super(MLP, self).__init__()
        #super().__init__()
        self.flatten = nn.Flatten()
        self.device = torch.device(device)
        self.input = input
        self.hidden = hidden
        self.output = output
        self.activation_fun = activation_fun
        self.optimizer_method = optimizer_method
        self.alpha = alpha

        self.layers = nn.ModuleList()
        old_size = input
        for size in hidden:
            self.layers.append(nn.Linear(old_size, size))
            old_size = size
        self.layers.append(nn.Linear(old_size, output))
        if activation_fun == 'relu':
            self.activation = nn.ReLU()
        elif activation_fun == 'sigmoid':
            self.activation = nn.Sigmoid()
        elif activation_fun == 'tanh':
            self.activation = nn.Tanh()
        elif activation_fun == 'leaky_relu':
            self.activation = nn.LeakyReLU()
        else:
            print("Invalid activation function.")

        if self.optimizer_method == 'adam':
            self.optimizer = optim.Adam(self.parameters(), lr = self.alpha)
        elif self.optimizer_method == 'adagrad':
            self.optimizer = optim.Adagrad(self.parameters(), lr = self.alpha)
        elif self.optimizer_method == 'sgd':
            self.optimizer = optim.SGD(self.parameters(), lr = self.alpha)
        else:
            print("Unknown Optimizer Method:" + self.optimizer_method)

        self.dropout = nn.Dropout(0.2)
        self.to(self.device)

    def forward(self,x):
        x = self.flatten(x).to(self.device)
        for i in range(len(self.layers) - 1):
            x = self.layers[i](x)
            x = self.activation(x)
            x = self.dropout(x)
        x = self.layers[-1](x)
        return x

def gpu_device():
    device = ("cuda" if torch.cuda.is_available() else "cpu")
    return device

def save_img(img, label, file_name, num_rows = 28, num_cols = 28):
    example = np.reshape(img, (num_rows, num_cols))
    plt.matshow(example)
    plt.title("This is a cloth " + str(label))
    plt.savefig(file_name)

data_iter = iter(train_dataloader)
images, labels = next(data_iter)

save_img(images[0], labels[0], 'example.png')

def training_model(model, train_dataloader, valid_dataloader, num_epochs,device, num_train_iters,num_valid_iters, batch_size):
  best_acc = 0
  model.train()
  Optimizer = model.optimizer
  for state in Optimizer.state.values():
    for k, v in state.items():
        if isinstance(v, torch.Tensor):
            state[k] = v.to(device)
  for epoch in range(num_epochs):
      print('Epochs: ' + str(epoch)+' -------------------------')
      avg_loss = 0
      avg_acc = 0
      for i, (x, y) in enumerate(train_dataloader):
          x = x.to(model.device)
          y = y.to(model.device)
          Optimizer.zero_grad()
          predict = model(x)
          loss = nn.CrossEntropyLoss()(predict, y)
          loss.backward()
          Optimizer.step()
          avg_loss += loss.item()
          avg_acc += (predict.argmax(1) == y).sum().item()

  avg_loss = avg_loss / num_train_iters
  avg_acc = avg_acc / (num_train_iters * batch_size)
  print('Training Loss: ' + str(avg_loss))
  print('Training Accuracy: ' + str(avg_acc))

  with torch.no_grad():
    model.eval()
    all_predict = []
    all_labels = []
    for i, (x, y) in enumerate(valid_dataloader):
        x = x.to(model.device)
        y = y.to(model.device)
        predict = model(x)
        all_predict.append(torch.argmax(predict, dim = 1))
        all_labels.append(y)

    all_predict = torch.cat(all_predict, dim = 0)
    all_labels = torch.cat(all_labels, dim = 0)

    acc = ((all_predict == all_labels).sum().item() / len(all_labels))*100
    print('Validation Accuracy: ' + str(acc))
    if acc > best_acc:
        best_acc = acc
        torch.save(model.state_dict(), 'best_model.pth')
  model.load_state_dict(torch.load("best_model.pth"))

def evaluate_model(model, test_dataloader, num_epochs, device):
  model.eval()
  all_predict = []
  all_labels = []
  with torch.no_grad():
    for i, (x, y) in enumerate(test_dataloader):
        x = x.to(model.device)
        y = y.to(model.device)
        predict = model(x)
        all_predict.append(torch.argmax(predict,dim = 1))
        all_labels.append(y)

    all_predict = torch.cat(all_predict, dim = 0)
    all_labels = torch.cat(all_labels)

    test_acc = ((all_predict == all_labels).sum().item() / len(all_labels))*100
    print('-------------------------------')
    print('Test Accuracy: ' + str(test_acc))
    c = torch.zeros(num_output, num_output)
    for i in range(num_output):
      indices = all_labels == i
      count = torch.sum(indices).item()
      assert count == all_predict[indices].size(0)
      arr = all_predict[indices]
      for j in range(num_output):
          c[i,j] = torch.sum(arr == j).item() * 100/ count
    print("Confusion_Matrix:\n",c)
    plt.clf()
    plt.matshow(c)
    plt.savefig('Confusion_Matrix.png')

    print('Done')

num_input = 28*28
num_hidden = input("Enter the number of neurons in hidden layer, as comma separated values eg. 64,32 or 128,64,32\n")
num_hidden = [int(x) for x in num_hidden.split(',')]
num_output = 10
alpha = 1e-4
num_epochs = 100
batch_size = 64
num_train_iters = len(train_dataloader) // batch_size
num_valid_iters = len(valid_dataloader) // batch_size
num_test_iters = len(test_dataloader) // batch_size

device = gpu_device()
model = MLP(num_input, num_hidden, num_output, 'relu', 'adam', alpha, device)
#model1 = MLP(num_input, num_hidden, num_output, 'relu', 'adagrad', alpha, device)
training_model(model, train_dataloader, valid_dataloader, num_epochs, device,num_train_iters,num_valid_iters,batch_size)
#training_model(model1, train_dataloader, valid_dataloader, num_epochs, device,num_train_iters,num_valid_iters,batch_size)

evaluate_model(model, test_dataloader, num_test_iters, device)
#evaluate_model(model1, test_dataloader, num_test_iters, device)
