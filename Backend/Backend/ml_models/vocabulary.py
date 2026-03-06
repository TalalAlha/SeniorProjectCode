import json
import re


class Vocabulary:
    PAD_TOKEN = '<PAD>'
    START_TOKEN = '<START>'
    END_TOKEN = '<END>'
    UNK_TOKEN = '<UNK>'

    def __init__(self):
        self.word2idx = {}
        self.idx2word = {}

    def decode(self, indices):
        _skip = (self.PAD_TOKEN, self.START_TOKEN, self.UNK_TOKEN)
        words = []
        for idx in indices:
            word = self.idx2word.get(idx, self.UNK_TOKEN)
            if word == self.END_TOKEN:
                break
            if word not in _skip:
                words.append(word)
        text = ' '.join(words)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        return text

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        vocab = cls()
        vocab.word2idx = data['word2idx']
        vocab.idx2word = {int(k): v for k, v in data['idx2word'].items()}
        return vocab

    def __len__(self):
        return len(self.word2idx)
