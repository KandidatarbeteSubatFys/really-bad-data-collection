import tensorflow as tf
import numpy as np
import time as t
import matplotlib.pyplot as plt
import math as m
import itertools as it
import help_funks as hf
import tf_funks as tff


def main(x_batch, y_batch, dep_batch, nr_nodes_hidden, nr_hidden_laysers, lam=1, tree=True):
    print('Initializing variables')
    x = tf.placeholder(dtype=tf.float32, shape=[None, 162])                     # Placeholder for input.
    y_ = tf.placeholder(dtype=tf.float32, shape=[None, 10])                     # Placeholder for correct output.

    y = tff.def_fc_layers(x, 162, 10, nr_nodes_hidden, nr_hidden_laysers)       # Defines a fully connected graf.

    loss = tff.split_energy_angle_comb(y, y_, 5, lam=lam, tree=tree)            # Defines loss.
    train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)                    # Set the training method to Adam opt.

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    loss_list = []                                                              # A list to store the loss values.
    loss_list_train = []                                                        # List of loss value for training data.
    move_av = [0]

    print('Partitioning the data')
    x_batch_eval = x_batch[0:int(0.01*len(x_batch))]                            # 1% as evaluation data set.
    x_batch_train = x_batch[int(0.01*len(x_batch)):-1]                          # Rest as training data set.
    y_batch_eval = y_batch[0:int(0.01 * len(x_batch))]
    y_batch_train = y_batch[int(0.01 * len(x_batch)):-1]


    print('Start training')
    start = t.time()                                                            # The time at the start of the training.
    i = 0
    diff = 10                                                                   # Old converges conditions.
    tol = 0.000001
    while m.fabs(diff) > tol and i < 500000:                                                        # Train 500000 steps
        x_batch_sub, y_batch_sub = hf.gen_sub_set(100, x_batch_train, y_batch_train)                # Batch size = 100
        if i % 100 == 0:                                                                            # Store statistics.
            loss_list_train.append(sess.run(loss, feed_dict={x: x_batch_sub, y_: y_batch_sub}))     # Train batch loss.
            x_batch_eval_sub, y_batch_eval_sub = hf.gen_sub_set(300, x_batch_eval, y_batch_eval)    # Evaluation batch 300
            loss_value = sess.run(loss, feed_dict={x: x_batch_eval_sub, y_: y_batch_eval_sub})      # Eval batch loss.
            if i % 10000 == 0:                                                                      # Print to terminal.
                print('Iteration nr. ', i, 'Loss: ', loss_value)
            loss_list.append(loss_value)
            move_av.append(hf.moving_average(loss_list, 20))                                        # Moving average (Old)
            #diff = move_av[-2] - move_av[-1]
        sess.run(train_step, feed_dict={x: x_batch_sub, y_: y_batch_sub})                           # One train step.
        i = i + 1
    end = t.time()                                                                              # Time when training done.

    Traningtime = end - start
    loss_end = sess.run(loss, feed_dict={x: x_batch_eval, y_: y_batch_eval})                    # Loss on the whole set.
    Training_iterations = i

    print('Calculating output')
    out_E = []
    out_theta = []
    out_corr_E = []
    out_corr_theta = []
    out = sess.run(y, feed_dict={x: x_batch_eval})                                      # Run the network on the evalset.
    for i in range(len(out)):
        index_list = tff.min_sqare_loss_combination(out[i], y_batch_eval[i], lam=lam)   # Find the right permutation
        for j in range(int(len(out[0])/2)):                                             # between correct and predicted
            out_E.append(out[i][2*j])                                                   # data.
            out_theta.append(out[i][2*j+1])
            out_corr_E.append(y_batch_eval[i][2*index_list[j]])
            out_corr_theta.append(y_batch_eval[i][2*index_list[j]+1])

    dep_batch_eval = dep_batch[0:int(0.01*len(x_batch))]                                # Deposited energy i detector.
    dep = [dep_val[0] for dep_val in dep_batch_eval]                                    # As a normal list.
    sum_pred = [np.sum(event[[i for i in range(0, len(event), 2)]]) for event in out]   # Sum of predicted energy.

    err_theta = [(out_theta[i]-out_corr_theta[i]) for i in range(len(out_theta))]       # Error in cos(theta).
    err_E = [(out_E[i] - out_corr_E[i])/out_corr_E[i] for i in range(len(out_E))]       # Relative error in energy.
    mean_E = np.mean(err_E)                                                             # Mean of energy error.
    mean_theta = np.mean(err_theta)                                                     # Mean of cos(theta) error.
    std_E = np.std(err_E)                                                       # Standard divination for energy error.
    std_theta = np.std(err_theta)                                               # Standard diviation of cos(theta) error.

    return loss_end, mean_E, mean_theta, std_E, std_theta, err_E, err_theta, out_E, out_corr_E, out_theta,\
           out_corr_theta, loss_list, loss_list_train, Traningtime, Training_iterations, sum_pred, dep


def plot(iterations, loss_training_list, loss_list, err_E, err_theta, out_corr_E, out_E, dep, sum_pred,
            out_corr_theta, out_theta, nodes, layers, n, fig_path):
    print('Ploting')
    # Set up a subfigure environment.
    fig, ax = plt.subplots(2, 4, figsize=(20, 10))

    # Ploting the lossfunction as a function over traning iterations. Start 39 points in for beater formatting.
    iter_list = [i for i in range(0, iterations, 100)]
    ax[0, 0].plot(iter_list[39:-1], loss_training_list[39:-1])
    ax[0, 0].plot(iter_list[39:-1], loss_list[39:-1])
    ax[0, 0].set(ylabel='Loss function (MeV)^2', xlabel='Iteration')

    # Histogram over the relative errors in energy.
    ax[0, 1].hist(err_E, bins='auto')
    ax[0, 1].set(ylabel='Counts', xlabel='Relative error energy')

    # Histogram over error in cos(theta)
    ax[0, 2].hist(err_theta, bins='auto')
    ax[0, 2].set(ylabel='Counts', xlabel='Error cos(theta)')

    # Plot the relative error against cos(theta)
    ax[0, 3].hist2d(out_corr_theta, err_E, bins=int(np.sqrt(len(err_E) / 100)))
    ax[0, 3].set(xlabel='Cos(theta) (correct)', ylabel='Relative error energy')

    # 2D histogram, density plot, predicted against correct.
    ax[1, 0].hist2d(out_corr_E, out_E, bins=int(np.sqrt(len(out_E)/100)))
    ax[1, 0].plot([0, 10], [0, 10], 'r')
    ax[1, 0].set(xlabel='Gun energy (MeV)', ylabel='Predicted energy (MeV)')

    # 2D histogram, density plot, sum predicted energy  against deposited.
    ax[1, 1].hist2d(dep, sum_pred, bins=int(np.sqrt(len(dep)/100)))
    ax[1, 1].plot([0, 50], [0, 50], 'r')
    ax[1, 1].set(xlabel='Deponated energy (MeV)', ylabel=' Sum predicted energy (MeV)')

    # 2D histogram, density plot, predicted cos(theta) against cos(theta) correct.
    ax[1, 2].hist2d(out_corr_theta, out_theta, bins=int(np.sqrt(len(out_theta)/100)))
    ax[1, 2].plot([-1, 1], [-1, 1], 'r')
    ax[1, 2].set(xlabel='Correct cos(theta)', ylabel='Predicted cos(theta)')

    # Plot the error in cos(theta) against energy
    ax[1, 3].hist2d(out_corr_E, err_theta, bins=int(np.sqrt(len(err_E) / 100)))
    ax[1, 3].set(xlabel='Gun energy (correct) (MeV)', ylabel='Error cos(theta)')

    # Add a title to the figures containing tha architecture of the network used.
    fig.suptitle(
        'Hidden layers: ' + str(layers) + ', nodes per layer: ' + str(nodes) + ' iterations: ' + str(iterations))
    name = str(n) + '.' + str(layers) + '.' + str(nodes) + '.png'
    plt.savefig(fig_path + name)                                    # Save the plot
    plt.clf()                                                       # Close the plot


def parameter_sweep():
    # File name of deposed energy in the cristal's.
    energy_file_name ='/n/home/oljacob/Dokument/Kandidatarbete/a_tree/angle_5gamma/XBe_5gun_iso_01_10_1000000.txt'
    # File name of the data from the guns.
    gun_file_name = '/n/home/oljacob/Dokument/Kandidatarbete/a_tree/angle_5gamma/gun_5gun_iso_01_10_1000000.txt'
    # File name of all deposed energy in the detector.
    dep_file_name = '/n/home/oljacob/Dokument/Kandidatarbete/a_tree/angle_5gamma/XBsum_5gun_iso_01_10_1000000.txt'
    # Path to the folder where all figures will be placed.
    fig_path = '/n/home/oljacob/Dokument/Kandidatarbete/a_tree/angle_5gamma/figs/'
    # Path to the folder where all non figure files will be placed, not that existing files in this location will be
    # over writen if over_write = True.
    file_path = '/n/home/oljacob/Dokument/Kandidatarbete/a_tree/angle_5gamma'

    # Parameters to sweep over.
    hidden_nodes = [256]                                    # [32, 64, 128, 256, 512, 1024, 2048, 4096]
    hidden_layers = [5, 5]                                  # [1, 2, 3, 4, 5]
    tree = [False, True]

    # Make the parameter sweep lists.
    nodes, layers, tree = hf.gen_parameter_sweep_list(hidden_nodes, hidden_layers, tree, repit=1)

    # Open files and make dedicated functions to write in them.
    stats_write = hf.make_write_function(file_path=file_path + '/stats.txt', over_write=True, header='')
    loss_write = hf.make_write_function(file_path=file_path + '/loss.txt', over_write=True, header='')
    loss_train_write = hf.make_write_function(file_path=file_path + '/loss_train.txt', over_write=True, header='')
    err_write = hf.make_write_function(file_path=file_path + '/err.txt', over_write=True, header='')

    # Read the training, evaluation and deposited data in to memory.
    print('Reading data')
    x_batch = hf.read_data(energy_file_name)
    y_batch = hf.read_data(gun_file_name)
    dep_batch = hf.read_data(dep_file_name)

    for i in range(len(nodes)):
        print('Laysers: ' + str(layers[i]) + ' nodes: ' + str(nodes[i]))

        # Calls the main script to preform the training.
        loss, mean_E, mean_theta, std_E, std_theta,\
        err_E, err_theta, out_E, out_corr_E, out_theta,\
        out_corr_theta, loss_list, loss_training_list,\
        trainingtime, iterations, sum_pred, dep = main(x_batch, y_batch, dep_batch,
                                                       nodes[i], layers[i], tree=tree[i])

        # Plots the summarizing plots of the training.
        plot(iterations, loss_training_list, loss_list, err_E, err_theta, out_corr_E, out_E, dep, sum_pred,
            out_corr_theta, out_theta, nodes[i], layers[i], i, fig_path)

        # Write to stats file .
        stats_write(str(i) + ' ' + str(layers[i]) + ' ' + str(nodes[i]) + ' ' + str(loss) + ' ' + str(mean_E)
                    + ' ' + str(mean_theta) + ' ' + str(std_E) + ' ' + str(std_theta) + ' ' + str(trainingtime)
                    + ' ' + str(iterations) + ' \n')

        # Restructure the list of loss values to a string, to be writen to file.
        loss_str = str()
        loss_train_str = str()
        for i in range(len(loss_list)):
            loss_str = loss_str + ' ' + str(loss_list[i])
            loss_train_str = loss_train_str + ' ' + str(loss_training_list[i])

        loss_write(loss_str + ' \n')                                            # Write to loss file.
        loss_train_write(loss_train_str + ' \n')                                # Writ to loss_train file.

        # Restructure the list of relative errors to a string, to be writen to file.
        err_str_E = str()
        err_str_theta = str()
        for i in range(len(err_E)):
            err_str_E = err_str_E + ' ' + str(err_E[i])
            err_str_theta = err_str_theta + ' ' + str(err_theta[i])

        # Energy errors and cos(theta) errors i writen to the file alternating.
        err_write(err_str_E + ' \n')                                        # Write relativ error i energy to err file.
        err_write(err_str_theta + ' \n')                                    # Write error i cos(theta) to err file.

    print('Exiting')



if __name__ == '__main__':
    parameter_sweep()