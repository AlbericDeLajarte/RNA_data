import pandas as pd
import os
import numpy as np

import sys
import torch

# Define the one-hot encodings for the sequences and structures
seq2int = {
        'A': 1,
        'C': 2,
        'G': 3,
        'T': 4,
        'U': 4,
        'N': 5,
        'Y': 6,
        'R': 7,
        'K': 8,
        'W': 9,
        'S': 10,
        'M': 11,
        'B': 12,
        'D': 13,
        'H': 14,
        'V': 15,
        'X': 0
    }

dot2int = {'.': 1, '(': 2, ')': 3, 'X': 0}
int2dot = ['X', '.', '(', ')']


def generate_embeddings(df, data_dir, device='cpu'):

    # Create temp folder
    temp_dir = os.path.join(data_dir, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    rna_fm_dir = os.path.join(data_dir, '..', '..', 'RNA-FM', 'redevelop')
    os.chdir(rna_fm_dir)

    # Generate a fasta file
    with open(os.path.join(temp_dir, 'sequences.fasta'), 'w') as f:
        for i in range(len(df)):
            f.write(f'>{df.index[i]}\n{df.iloc[i]["sequence"]}\n')

    # Run RNA-FM to generate the embeddings
    cmd = f'python launch/predict.py --config="pretrained/extract_embedding.yml" \
            --data_path={os.path.join(temp_dir, "sequences.fasta")} --save_dir={temp_dir} \
            --save_frequency 1 --save_embeddings --device={device}'
    
    os.system(cmd)

    # Move results to data_dir and remove temps folder
    os.system(f'mv {temp_dir}/representations {data_dir}/embeddings')
    os.system(f'rm -r {temp_dir}')

    sequences = []
    idx_todelete = []
    for i in range(len(df)):
        file_dir = os.path.join(data_dir, 'embeddings', f'{df.index[i]}.npy')
        if os.path.exists(file_dir):
            sequences.append(file_dir)
        else:
            idx_todelete.append(i)

    df = df.drop(df.index[idx_todelete]) 

    # Return all references in the embeddings folder
    return df, sequences

def import_structure(path_to_structures=None, dataset='synthetic', size=None, save=False, reload=True, rna_fm=False):
    """
    Import the secondary structure dataset and convert to pairing matrix, with padding.
    Each pairing matrix is directly saved as a separate npy file.

    Each row of the dataset contains a sequence and a structure.
    The sequences contains the nucleotides A, C, G, T, U, N
    The structures is binary pairing matrix with 0 for unpaired bases and 1 for paired bases

    :param path_to_structures: Path to the secondary structure dataset in json format
    :param size: The number of datapoints to import
    :param save: Whether to save the dataset as a numpy array
    :param reload: Whether to reload the dataset from the numpy array

    :return: The sequences as numpy array and the list of numpy file names of the pairing matrices
    """

    # assert dataset in ['synthetic', 'bpRNA', 'test_PDB', 'test_Sarah']

    # Paths to the dataset
    dirname = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(dirname, 'dataset', dataset)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    save_path = [os.path.join(data_dir, 'processed_sequences.npy'),
                 os.path.join(data_dir, 'processed_structures.npy')]
    if rna_fm:
        save_path[0] = os.path.join(data_dir, 'references.npy')

    if path_to_structures is None:
        path_to_structures = os.path.join(data_dir, 'secondary_structure.json')


    # Check if the dataset is already saved
    if reload:
        
        # Import the dataset and check size
        if size is None:
            df = pd.read_json(path_to_structures).T
            size = len(df)

        if os.path.exists(save_path[0]) and os.path.exists(save_path[1]):

            print("Loading saved dataset")
            sequences = np.load(save_path[0], allow_pickle=True)
            structures = np.load(save_path[1], allow_pickle=True)

            if len(sequences) < size or len(structures) < size:
                print("Dataset too small, creating new one")
                return import_structure(path_to_structures, size=size, save=save, reload=False, rna_fm=rna_fm)
            else:
                idx = np.random.choice(len(sequences), size=size, replace=False)
                if save:
                    np.save(save_path[0], sequences[idx])
                    np.save(save_path[1], structures[idx])
                
                return sequences[idx], structures[idx]
        else:
            print("Dataset not found, creating new one")
            return import_structure(path_to_structures, size=size, save=save, reload=False, rna_fm=rna_fm)
        

    else:  

        # Import the dataset and check size
        df = pd.read_json(path_to_structures).T
        if size is None:
            size = len(df)      
        elif size > len(df):
            print("Requested size too large, using full dataset")
            size = len(df)
        
        # Get a random sample of the dataset
        idx = np.random.choice(len(df), size=size, replace=False)
        df = df.iloc[idx]


        # Init numpy arrays for sequences
        sequences = []
        structures = []
        
        # Generate embeddings and get list of sequences paths
        if rna_fm:
            df, sequences = generate_embeddings(df, data_dir)

        # Iterate over the rows of the dataframe
        for i, (reference, row) in enumerate(df.iterrows()):

            # Print progress
            if i%1000:
                sys.stdout.write("Processing dataset: %d%%   \r" % (100*i/len(df)) )
                sys.stdout.flush()

            if not rna_fm:
                # Integer encoding of the sequence
                sequences.append(np.array([seq2int[base] for base in row['sequence'].upper()]))
            else:
                assert np.load(sequences[i]).shape[0] == len(row['sequence'])

            # Convert to numpy array
            structures.append(np.array(row['paired_bases']))

        sequences = np.array(sequences, dtype=object)
        structures = np.array(structures, dtype=object)

        # Save sequences and structures as numpy arrays
        if save:
            np.save(save_path[0], sequences)
            np.save(save_path[1], structures)
        
        return sequences, structures



if __name__ == '__main__':

    sequences, structures = import_structure(size=32, save=False, reload=True, dataset='SARS2', rna_fm=True)
    print("Loaded full dataset with shape: \n", sequences.shape, "\n", len(structures))