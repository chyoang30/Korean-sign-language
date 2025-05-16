# coding: utf-8
from collections import Counter, defaultdict

import numpy as np
from torch.utils.data import Dataset

from typing import List, NoReturn, Optional

SIL_TOKEN = "<si>"
UNK_TOKEN = "<unk>"
PAD_TOKEN = "<pad>"


class Vocabulary:
    """ Vocabulary represents mapping between tokens and indices. """

    def __init__(self) -> NoReturn:
        # don't rename stoi and itos since needed for torchtext
        # warning: stoi grows with unknown tokens, don't use for saving or size
        self.specials = []
        self.itos = []
        self.stoi = None
        self.DEFAULT_UNK_ID = None

    def _from_list(self, tokens: Optional[List[str]] = None):
        """
        Make vocabulary from list of tokens.
        Tokens are assumed to be unique and pre-selected.
        Special symbols are added if not in list.

        :param tokens: list of tokens
        """
        self.add_tokens(tokens=self.specials + tokens)
        assert len(self.stoi) == len(self.itos)

    def __str__(self) -> str:
        return self.stoi.__str__()

    def add_tokens(self, tokens: List[str]) -> NoReturn:
        """
        Add list of tokens to vocabulary

        :param tokens: list of tokens to add to the vocabulary
        """
        for t in tokens:
            new_index = len(self.itos)
            # add to vocab if not already there
            if t not in self.itos:
                self.itos.append(t)
                self.stoi[t] = new_index

    def is_unk(self, token: str) -> bool:
        """
        Check whether a token is covered by the vocabulary

        :param token:
        :return: True if covered, False otherwise
        """
        return self.stoi[token] == self.DEFAULT_UNK_ID()

    def __len__(self) -> int:
        return len(self.itos)


class GlossVocabulary(Vocabulary):

    def __init__(self, tokens: Optional[List[str]] = None, file: Optional[str] = None) -> NoReturn:
        """
        Create vocabulary from list of tokens or file.

        Special tokens are added if not already in file or list.
        File format: token with index i is in line i.

        :param tokens: list of tokens
        :param file: file to load vocabulary from
        """
        super().__init__()
        self.specials = [SIL_TOKEN, UNK_TOKEN, PAD_TOKEN]
        self.DEFAULT_UNK_ID = lambda: 1
        self.stoi = defaultdict(self.DEFAULT_UNK_ID)
        self.pad_token = PAD_TOKEN
        self.sil_token = SIL_TOKEN

        if tokens is not None:
            self._from_list(tokens)

        assert self.stoi[SIL_TOKEN] == 0

    def arrays_to_sentences(self, arrays: np.array) -> List[List[str]]:
        gloss_sequences = []
        for array in arrays:
            sequence = []
            for i in array:
                sequence.append(self.itos[i])
            gloss_sequences.append(sequence)
        return gloss_sequences


def filter_min(counter: Counter, minimum_freq: int):
    """ Filter counter by min frequency """
    filtered_counter = Counter({t: c for t, c in counter.items() if c >= minimum_freq})
    return filtered_counter


def sort_and_cut(counter: Counter, limit: int):
    """ Cut counter to most frequent,
    sorted numerically and alphabetically"""
    # sort by frequency, then alphabetically
    tokens_and_frequencies = sorted(counter.items(), key=lambda tup: tup[0]) 
    tokens_and_frequencies.sort(key=lambda tup: tup[1], reverse=True)
    vocab_tokens = [i[0] for i in tokens_and_frequencies[:limit]]
    return vocab_tokens


def build_vocab(cfg, dataset: Dataset, max_size: int, *, min_freq: int = 1) -> Vocabulary:
    exclude_token = cfg.DATASET.VOCABULARY.EXCLUDE_TOKENS

    tokens = []
    for example in dataset.examples:
        anns = example["Kor"]
        tokens.extend(anns)

    counter = Counter(tokens)
    if min_freq > -1:
        counter = filter_min(counter, min_freq)
    vocab_tokens = sort_and_cut(counter, max_size)
    assert len(vocab_tokens) <= max_size

    vocab = GlossVocabulary(tokens=vocab_tokens)

    assert len(vocab) <= max_size + len(vocab.specials)
    assert vocab.itos[vocab.DEFAULT_UNK_ID()] == UNK_TOKEN

    for i, s in enumerate(vocab.specials):
        if i != vocab.DEFAULT_UNK_ID():
            assert not vocab.is_unk(s)

    return vocab
