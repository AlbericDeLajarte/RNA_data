import pandas as pd
import os
import numpy as np

def import_structure(path_to_structures):
    """
    Import the secondary structure dataset and convert to one-hot encoding.

    Each row of the dataset contains a sequence and a structure.
    The sequences contains A, U, C, G and Y, R, N bases.
    The structures contains f, t, i, h, m, or s characters.

    :param path_to_structures: Path to the secondary structure dataset in json format
    :return: A tuple with the one-hot encoded sequences and structures in numpy arrays
    """

    # Define the one-hot encodings for the sequences and structures

    seq2vec = {
        'A': [1, 0, 0, 0, 0],
        'C': [0, 1, 0, 0, 0],
        'G': [0, 0, 1, 0, 0],
        'T': [0, 0, 0, 1, 0],
        'U': [0, 0, 0, 1, 0],
        'Y': [0, 1, 0, 1, 0],
        'R': [1, 0, 1, 0, 0],
        'K': [0, 0, 1, 1, 0],
        'N': [1, 1, 1, 1, 0],
        'X': [0, 0, 0, 0, 1]
    }

    struct2vec = {
        'f': [1, 0, 0, 0, 0, 0, 0],
        't': [0, 1, 0, 0, 0, 0, 0],
        'i': [0, 0, 1, 0, 0, 0, 0],
        'h': [0, 0, 0, 1, 0, 0, 0],
        'm': [0, 0, 0, 0, 1, 0, 0],
        's': [0, 0, 0, 0, 0, 1, 0],
        'X': [0, 0, 0, 0, 0, 0, 1]
    }

    # Import the dataset as a pandas dataframe
    df = pd.read_json(path_to_structures)

    # Get max length of sequence 
    max_seq_len = df['sequence'].str.len().max()

    # Init numpy arrays for sequences and structures
    sequences = np.zeros((len(df), len(seq2vec['A']), max_seq_len))
    structures = np.zeros((len(df), len(struct2vec['f']), max_seq_len))

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():

        if i%100:
            print(i/len(df)*100, "%")
        
        # Apply zero padding to each row (sequence and structure)
        row['sequence'] = row['sequence'].upper().ljust(max_seq_len, 'X')
        row['structure'] = row['structure'].lower().ljust(max_seq_len, 'X') 

        # One hot encoding of the sequence, with padding as 'X' 
        for j, base in enumerate(row['sequence']):
            sequences[i, :, j] = seq2vec[base]

        # One hot encoding of the structure, with padding as 'X' 
        for j, struct in enumerate(row['structure']):
            structures[i, :, j] = struct2vec[struct]
        
    return sequences, structures


if __name__ == '__main__':
    path_to_structures = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'secondary_structure.json')
    sequences, structures = import_structure(path_to_structures)

    print("done")