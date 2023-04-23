import os
import numpy as np
import subprocess
import re
import sys
import pandas as pd

# Function from https://github.com/kkyamada/bert-rbp
def get_mea_structures(path_to_fasta, path_to_linearpartition):
    
    command = 'cat {} | {} -M'.format(path_to_fasta, path_to_linearpartition)
    
    # could use capture_output=True to not print to stdout, but we will need to print progress bar another way
    output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True)
    
    assert output.returncode == 0, 'ERROR: in execute_linearpartition_mea for {}'.format(path_to_fasta)
    
    outputs = output.stdout.decode().strip().split('\n')
    
    structure_seqs = []
    sequences = []
    for i_s, row in enumerate(outputs):

        # If the structure is the sequence information:
        if i_s%4 == 0:
            sequences.append(row)

        # If the structure is a dot-bracket structure:
        if (i_s-2)%4 == 0:
            structure_seqs.append(row)
                        
    return sequences, structure_seqs

if __name__ == '__main__':

    dir_name = os.path.dirname(os.path.abspath(__file__))

    # Get path to fasta file
    if len(sys.argv) >= 2:
        path_to_fasta = sys.argv[1]
    else:
        path_to_fasta = os.path.join(dir_name, '..', 'sequence_dataset', 'sequences_full.fasta')

    # Compile LinearPartition if it hasn't been compiled yet
    if not os.path.exists(os.path.join(dir_name, 'LinearPartition', 'bin')):
        print('Compiling LinearPartition')
        os.chdir(os.path.join(dir_name, 'LinearPartition'))
        os.system('make')
        os.chdir(dir_name)

    # Get the secondary structure sequences
    path_to_linearpartition = os.path.join(dir_name, 'LinearPartition', 'linearpartition')
    sequences, structures = get_mea_structures(path_to_fasta, path_to_linearpartition)

    # Save the dataframes as json
    save_dir = os.path.join(dir_name, 'dataset', 'dot_bracket')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    df = pd.DataFrame({'sequence': sequences, 'structure': structures})
    df.to_json(os.path.join(save_dir, 'secondary_structure.json'), indent=2)