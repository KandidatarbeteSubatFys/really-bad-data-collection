"""Some different functions that could be to help, mostly concerning data handling.
    -- Spring 2018; ce2018
"""
import numpy as np
import math as m
from random import shuffle


def read_data(file, cols=162, dtype=np.float32):
	rows = file_len(file)
	out = np.zeros((rows, cols), dtype=dtype)
	with open(file) as f: 
		for i, line in enumerate(f): 
			out[i] = np.fromstring(line.rstrip(), dtype=dtype, sep=' ')
	return out


def randomize_content(*args):
    """Randomize the internal order of two lists but still keep the relation between the events in the different files.
    Args:   x_batch: list A list where every row internal list is associated with the same row in y_batch.
            y_batch: list see x_batch
    Out:    new_x_batch, new_y_batch: randomized versions of x_batch and y_batch.
    """
    for arg in args:
        if not (isinstance(arg, list) or isinstance(arg, np.ndarray)):
            raise TypeError('All input arguments must be of type list. /Pontus')
        elif not len(args[0]) == len(arg):
            raise TypeError('Batches most be of same size /Pontus')

    index_list = np.arange(0, len(args[0]), dtype=np.int)                        # All incises of the x_batch list shuffled.
    np.random.seed(89375)
    np.random.shuffle(index_list)

    return tuple(arg[index_list] for arg in args)


def file_len(file):
	with open(file) as f:
		for i, l in enumerate(f):
			pass
	return i + 1 


def gen_sub_set(batch_size, batch_x, batch_y):
    """Generates a random subset of two lists, where the elements of the two list is associated with eachother.
    Args:   batch_size: int the size of the subset to be generated.
            batch_x:  list the list the subset should be generated from together with the batch_y subset.
            batch_y: list see batch_x.
    Out:    unnamed: list the subsets of batch_x and batch_y (as a touple)
    """
    if not len(batch_x) == len(batch_y):
        raise ValueError('Lists most be of same length /Pontus')
    elif batch_size > len(batch_x):
        raise ValueError("The batch size can't be greater then the size of the lists.")

    index_list = np.random.randint(0, len(batch_x), size=batch_size)               # Random subset of index to the lists
    return [batch_x[index] for index in index_list], [batch_y[index] for index in index_list]


def moving_average(list, points):
    """A function to calculate the average of the last elements in a given list.
    Args:   list: list the list the average should be taken over.
            points: the number of entrys the averages should be taken over.
    Out:     unnamed: float the averages of the last 'points' enterys in 'list', if the list is shorter then 'points'
                      the averages is taken over the whole list.
    """
    if len(list) < points:                                          # If list is to short, averages of the whole list.
        return m.fsum(list)/len(list)
    else:                                                           # Averages of the points last elements in the list.
        return (m.fsum(list[-points:-1]) + list[-1])/points


def make_write_function(file_path, over_write=True, header=''):
    """A function factory to make functions that write to a file. Mostly to get rid of the with statements.
    Args:   file_path: str the file path to the file in question (the file name as well).
            over_write: boolean if true, the old file is first over writen.
            header: str enter a initial str to be added to the file.
    Out:    writer_function: funk a function that writes a string to the file given to make_write_function.
    """
    s = 'w' if over_write else 'a'          # write over or append.
    with open(file_path, s) as f:           # Opens the file, a check.
        if not header == '':
            f.write(header + ' \n')         # Write header.

    def write_function(txt):                # Defines output function.
        with open(file_path, 'a') as f:     # Opens file in append mode.
            f.write(txt + '\n')             # Write given string.

    write_function.__doc__ = 'A function that writes to ' + file_path       # Adds a doc string.

    return write_function                   # Returns the write function.


def gen_parameter_sweep_list(*argv, repit=1):
    """Given multiple lists with the parameter values of each parameter this function returns a list for each parameter
    that between them looks att all the combinations of the parameters given in the input lists.
    Args:   *args: lists with we allowed values for the different parameters.
            repit: int the number of times a combination will appear in the output.
    Out:    list_of_lists: tuple containing lists of all the allowed combinations in a parameter sweep,
                           parameter for parameter.
    """
    for arg in argv:                                                        # Check that all arguments are valid.
        if not isinstance(arg, list):
            raise TypeError('All arguments must be of type list. /Pontus')

    list_of_lists = [[] for i in argv]                                      # init output with right type and len.

    def get_index_list():
        """current_index is the index combinations all the lists in argv can have. Incrementally increase the first
        value in current_index until it overflows the len of the first list give as argument in gen_parameter_sweep_list.
        Then add to the second argument in current_index and set the first argument to 0, ect.
        """
        index_lists = []
        current_index = [0 for i in argv]                               # init all index to zero.
        for i in range(np.prod([len(arg) for arg in argv])):            # Loop over the total number of combinations.
            for j in range(len(current_index)):
                if current_index[j] > len(argv[j]) - 1:                 # If overflow add to next value in the list and
                    current_index[j + 1] = current_index[j + 1] + 1     # set the current to zero.
                    current_index[j] = 0
            for i in range(repit):                                      # Add multiple copies if wanted.
                index_lists.append(current_index[:])
            current_index[0] = current_index[0] + 1                     # Increment current index.
        return index_lists

    for index_list in get_index_list():                                 # Add all the combinations to the output.
        for i in range(len(list_of_lists)):                             # Loop over the parameters.
            list_of_lists[i].append(argv[i][index_list[i]])

    return tuple(list_of_lists)


if __name__ == '__main__':
    print('The file contains some functions mostly concerning data handling.')
    print('-- Spring 2018; ce2018')

