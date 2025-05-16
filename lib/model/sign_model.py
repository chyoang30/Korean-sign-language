import torch
import torch.nn as nn

from .layers import Conv1d, Conv2d, get_norm


class SignModel(nn.Module):

    def __init__(self, vocab):
        super().__init__()
        activation = nn.ReLU()
        norm_2d = "BN_2d"
        norm_1d = "BN_1d"

        # 2d feature extraction
        self.conv1 = Conv2d(
            3, 32, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(32)
        )  # (3, 224, 224) -> (32, 224, 224)
        self.pool1 = nn.MaxPool2d(2, stride=2)  # (32, 112, 112)

        self.conv2 = Conv2d(
            32, 64, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(64)
        )
        self.pool2 = nn.MaxPool2d(2, stride=2)  # (64, 56, 56)

        self.conv3 = Conv2d(
            64, 64, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(64)
        )
        self.conv4 = Conv2d(
            64, 128, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(128)
        )
        self.pool4 = nn.MaxPool2d(2, stride=2)  # (128, 28, 28)

        self.conv5 = Conv2d(
            128, 128, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(128)
        )
        self.conv6 = Conv2d(
            128, 256, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(256)
        )
        self.pool6 = nn.MaxPool2d(2, stride=2)  # (256, 14, 14)

        self.conv7 = Conv2d(
            256, 256, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(256)
        )
        self.conv8 = Conv2d(
            256, 512, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(512)
        )
        self.pool8 = nn.MaxPool2d(2, stride=2)  # (512, 7, 7)

        self.conv9 = Conv2d(
            512, 512, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm2d(512)
        )
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))  # (512, 1, 1)

        # temporal encode
        self.tconv1 = Conv1d(
            512, 512, 5, stride=1, padding=2, activation=activation, norm=nn.BatchNorm1d(512)
        )
        self.tpool1 = nn.MaxPool1d(2, stride=2)

        self.tconv2 = Conv1d(
            512, 512, 5, stride=1, padding=2, activation=activation, norm=nn.BatchNorm1d(512)
        )
        self.tpool2 = nn.MaxPool1d(2, stride=2)

        self.tconv3 = Conv1d(
            512, 1024, 3, stride=1, padding=1, activation=activation, norm=nn.BatchNorm1d(1024)
        )

        # classification
        self.classifier = nn.Linear(1024, len(vocab))

        # init
        self.init_layers()

    def init_layers(self):
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # x: (B, T, C, H, W) -> (B*T, C, H, W)
        # features: (B*T, 512, 1, 1) -> (B, T, 512)
        # after t1: (B, T//4, 512)
        # after t2: (B, T//4, 1024)
        # how to handle linear layer ? 1d input shape?
        _, clip_length, _, _, _ = x.shape
        """
        temporal_group = int(clip_length / self.num_groups)
        results = []
        for t in range(0, clip_length, temporal_group):
            # t_slice = x[:, t:t + temporal_group]  # (B, group, C, H, W)
            results.append(self.extract_feature(x[:, t:t + temporal_group]))  # (B, C, group)
        x = torch.cat(results, dim=2)
        assert x.size(2) == clip_length
        """
        x = self.extract_feature(x)
        # temporal encoding
        x = self.tpool1(self.tconv1(x))
        x = self.tpool2(self.tconv2(x))
        x = self.tconv3(x)  # (batch, 1024, T//4)

        # classifier
        x = x.transpose(1, 2)  # (batch, T//4, 1024)
        x = self.classifier(x)  # (batch, T//4, C)
        return x

    def extract_feature(self, x):
        batch_size, clip_length, C, H, W = x.shape
        x = x.view(batch_size * clip_length, C, H, W)
        x = self.pool1(self.conv1(x))
        x = self.pool2(self.conv2(x))
        x = self.pool4(self.conv4(self.conv3(x)))
        x = self.pool6(self.conv6(self.conv5(x)))
        x = self.pool8(self.conv8(self.conv7(x)))
        x = self.avg_pool(self.conv9(x))  # (B*T, 512, 1, 1)
        x = x.view(x.shape[:2]).view(batch_size, clip_length, -1).transpose(1, 2)  # (B, C, T)
        return x
