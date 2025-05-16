import glob
import os

import cv2
import numpy as np
import torch
from torch import Tensor
from torch.utils.data import Dataset

import pandas as pd
from typing import Callable, List, NoReturn, Optional, Tuple

from .transforms import apply_transform_gens
import pdb

class SignDataset(Dataset):

    def __init__(
        self,
        data_root: str,
        ann_file: str,
        *,
        img_prefix: Optional[str] = None,
        tfm_gens: Optional[list] = None,
        tokenize: Optional[Callable] = None,
        lower: bool = False,
        is_train=False,
        exclude_token=None
    ) -> NoReturn:
        ann_file = os.path.join(data_root, ann_file)

        # option for videos
        self.tfm_gens = tfm_gens

        # option for tokenization
        self.tokenize = tokenize
        self.lower = lower
        self.exclude_token = exclude_token

        self.img_prefix = os.path.join(data_root, img_prefix)
        self.examples = self.load_examples_from_csv(ann_file)
        self.is_train = is_train

    def __getitem__(self, i):
        assert hasattr(self, "vocab")
        example = self.examples[i]

        # read video -> processing
        frames_path = example["frames"]

        # ramdom duplicate and drop
        frames_inds = np.array([i for i in range(len(frames_path))]).astype(int)
        if self.is_train:
            rand_inds = np.random.choice(
                len(frames_path), int(len(frames_path) * 0.2), replace=False
            )

            # random frame insertion
            total_inds = np.concatenate([frames_inds, rand_inds], 0)
            total_inds = np.sort(total_inds)

            # random frame dropping
            rand_inds = np.random.choice(len(total_inds), int(len(total_inds) * 0.2), replace=False)
            selected = np.delete(total_inds, rand_inds)
        else:
            selected = frames_inds
        # frames = np.stack([cv2.imread(f_path, cv2.IMREAD_COLOR) for f_path in frames_path], axis=0)  # noqa

        # read selected images
        
        try:
            frames = np.stack([cv2.imread(frames_path[i], cv2.IMREAD_COLOR) for i in selected], axis=0)
        except ValueError:
            print(example)
            #pdb.set_trace()
        if self.tfm_gens is not None:
            frames, _ = apply_transform_gens(self.tfm_gens, frames)

        # gloss -> CTC supervision signal
        tokens = example["Kor"]
        indices = [self.vocab.stoi[token] for token in tokens]
        return frames, indices

    def __len__(self):
        return len(self.examples)

    def load_examples_from_csv(self, ann_file: str) -> List[dict]:
        annotations = pd.read_csv(ann_file, sep=",",encoding='euc-kr')
        annotations = annotations[["Filename", "Kor"]]

        examples = []
        for i in range(len(annotations)):
            example = dict(annotations.iloc[i])
            # glob all image locations
            frames_path = glob.glob(os.path.join(self.img_prefix, example["Filename"],"*.jpg"))
            frames_path.sort()
            example["frames"] = frames_path

            # tokenization
            glosses_str = example["Kor"]
            if self.tokenize is not None and isinstance(glosses_str, str):
                if self.lower:
                    glosses_str = glosses_str.lower()
                tokens = self.tokenize(glosses_str.rstrip("\n"))
                example["Kor"] = tokens
                '''
                example["Kor"] = [
                    token for token in tokens
                    # exclude some tokens in annotations, i.e., ["__ON__", "__OFF__"].
                    if (self.exclude_token is not None and token not in self.exclude_token)
                ]
                '''
            examples.append(example)

        return examples

    @property
    def gloss(self):
        return [example["Kor"] for example in self.examples]

    def load_vocab(self, vocabulary):
        self.vocab = vocabulary
        self.pad_idx = self.vocab.stoi[self.vocab.pad_token]
        self.sil_idx = self.vocab.stoi[self.vocab.sil_token]

    def collate(self, data):
        videos, glosses = list(zip(*data))

        def pad(videos: List[Tensor], glosses: List[int]
                ) -> Tuple[Tuple[List[Tensor], List[int]], Tuple[List[int], List[int]]]:
            video_lengths = [len(v) for v in videos]
            max_video_len = max(video_lengths)
            padded_videos = []
            for video, length in zip(videos, video_lengths):
                C, H, W = video.size(1), video.size(2), video.size(3)
                new_tensor = video.new(max_video_len, C, H, W).fill_(1e-8)
                new_tensor[:length] = video
                padded_videos.append(new_tensor)

            gloss_lengths = [len(s) for s in glosses]
            max_len = max(gloss_lengths)
            glosses = [
                s + [self.pad_idx] * (max_len - len(s)) if len(s) < max_len else s for s in glosses
            ]
            return (padded_videos, video_lengths), (glosses, gloss_lengths)

        (videos, video_lengths), (glosses, gloss_lengths) = pad(videos, glosses)
        videos = torch.stack(videos, dim=0)
        video_lengths = Tensor(video_lengths).long()
        glosses = Tensor(glosses).long()
        gloss_lengths = Tensor(gloss_lengths).long()
        return (videos, video_lengths), (glosses, gloss_lengths)
