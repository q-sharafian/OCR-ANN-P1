from torch.nn import Module, Sequential
from .line_model import decoder as l_decoder
from .line_model import encoder as l_encoder


class LineRecognition(Module):
    def __init__(self, params):
        super().__init__()
        self.model = Sequential(
            l_encoder.FCN_Encoder(params), l_decoder.LineDecoder(params)
        )

    def forward(self, sample):
        """
        Forward the images not the image/gt pairs
        Return predicted gt for given img
        """
        return self.model(sample)
