from random import randint
from bidi.algorithm import get_display
import arabic_reshaper
import matplotlib.pyplot as plt
from torch import Tensor
from typing import Union
import numpy as np


class CodingString:
    """
    Map the characters of a string to corresponding ints and return it as a list.
    (This is a transformer)
    """

    def __init__(self, map_char_file:str, used_in_train=True):
        """
        Parameters
        ----------
        map_char_file (str): The path of the file that map chars to ints
        used_in_train (bool): Set it true for the training and false for the testing 
        and evaluation steps.
        """
        with open(map_char_file, "r") as f:
            uniq_file = f.readlines()
        self.used_in_train = used_in_train
        # Create a dict that maps unique chars to ints
        self.char_to_int_map = {}
        for line in uniq_file:
            self.char_to_int_map[line[0]] = int(line[2:5])
        # vocab_size is the number of unique chars plus one that represent blank char.
        # Refer to CTC loss algorithm.
        self.vocab_size = len(self.char_to_int_map)  # + 1

    def __call__(self, input:dict) -> Union[dict, np.ndarray]:
        """
        Map the string to a numpy array of ints and then retrurn this array.

        Parameters
        ----------
        input (dict): If ``used_in_train`` equals True, the ``input`` is a dict and we 
        encode its ``gt`` key and return the whole input (with encoded ``gt``). 
        else ``input`` is a string and we encode it and return it in a numpy format.
        """
        txt_out = np.array([], dtype=int)
        if self.used_in_train:
            for char in input["gt"]:
                txt_out = np.append(txt_out, self.char_to_int_map[char])
            input["gt"] = txt_out
            return input
        else:
            for char in input:
                txt_out = np.append(txt_out, self.char_to_int_map[char])
            return txt_out
    
class DecodeString:
    """
    Decode the encoded string
    """
    def __init__(self, map_char_file):
        """
        map_char_file: The path of the file that map chars to ints
        """
        with open(map_char_file, "r") as f:
            uniq_file = f.readlines()
        # Create a dict that maps unique chars to ints
        self.int_to_char_map = {}
        for line in uniq_file:
            self.int_to_char_map[int(line[2:5])] = line[0]
        # vocab_size is the number of unique chars plus one that represent blank char.
        # Refer to CTC loss algorithm.
        self.vocab_size = len(self.int_to_char_map)  # + 1

    def __call__(self, encoded_gt:Union[Tensor, np.ndarray]) -> str:
        """
        Map the encoded string to a decoded string and then return it.

        Parameters
        ----------
        encoded_str (str): the encoded string we want to decode it.
        """
        txt_out = ""
        for coded_char in encoded_gt:
            if coded_char != 0: # coded_char wasn't blank character(defined in CTC class)
                # coded_char is tensor type, then we convert it to int
                txt_out += self.int_to_char_map[int(coded_char)]
        return txt_out
    
def random_from_list(input_list):
    """
    Select one element from the input_list as random and return it.
    """
    return input_list[randint(0, len(input_list) - 1)]

def load_char_map_file(path:str)->dict:
    """
    Load a map between characters and numbers.
    
    Returns
    -------
    A dict maps chars to int.
    """
    with open(path, "r") as f:
        file = f.readlines()
    # Create a dict that maps unique chars to ints
    char_to_int_map = {}
    for line in file:
        char_to_int_map[line[0]] = int(line[2:5])
    return char_to_int_map

def show_imgs(imgs, gts, details, permute=False):
    """
    Show image batches from a tensor. Note that the first dimension of each image is
    height, the second is width, and the third is the number of the image's channel.
    (Note that type of the image shouldn't be Numpy.float16. If use that, raise an error)
    Parameters
    ----------
    imgs(list): A list of images; the type of each image should be float Numpy or
    Torch tensor. Pixel values should be in [0, 1].
    gts(list): A list of ground truths corresponding to images.
    details(list): A list of details about parameters of every image.
    permute(bool): If true, permute each image such that the dimensions correspond
    to the description mentioned at first. (Works on torch.Tensor types only)
    """
    n_imgs = len(imgs)  # Number of input images
    fig, axes = plt.subplots(n_imgs, figsize=(50, 10))
    for i, img in enumerate(imgs, start=0):
        # Convert gt text to a printable style
        gt = arabic_reshaper.reshape(gts[i])
        gt = get_display(gt)
        gt += "\n" + details[i]
        if type(img) == Tensor and permute:
            img = img.permute(2, 1, 0)
        elif type(img) != Tensor and permute:
            raise TypeError(
                f'"permute=True" works just on torch.Tensor type, not on {type(img)}.'
            )

        if n_imgs > 1:
            axes[i].imshow(img)
            axes[i].set_title(gt, loc="right", fontsize=30)
        elif n_imgs == 1:
            axes.imshow(img, cmap="binary")
            axes.set_title(gt, loc="right", fontsize=30)
        else:
            raise ValueError("The imgs list is empty")

def create_char_to_int_map_file(unique_char_file, map_file):
    """
    Create a map file(i.e., a file contains unique chars and their corresponding
    integer) from file contain uniqie characters.
    """
    with open(unique_char_file, "r") as f:
        uniq_file = f.readlines()
    with open(map_file, "w") as f:
        for index, line in enumerate(uniq_file, start=1):
            # Split the unique characters and assign to them an unique numberand save them
            f.write(f"{line[0]}#{format(index, '03d')}\n")

def clean_sentence(input_sent:np.ndarray, sos_index:int, eos_index:int, ignore_token_index=0) -> np.ndarray:
    """
    Remove <sos> token, <eos> token and characters after <eos>, and ignore tokens 
    from sentence and return it.
    
    Parameters
    ----------
    input_sent (np.ndarray): Input sentence that is a vector with the length of ``input_Sent``.
    ``input_sent`` should be encoded string.
    """
    first_eos_indices = np.where(input_sent==eos_index)[0]
    if len(first_eos_indices) != 0:
        # Remove <eos> and characters after that
        input_sent = input_sent[:first_eos_indices.min()]
    input_sent = input_sent[np.where(input_sent != sos_index)[0]]
    # Remove the remaining ignore tokens
    input_sent = input_sent[np.where(input_sent != ignore_token_index)[0]]
    return input_sent