import tensorflow as tf
import time as t
import numpy as np
#import matplotlib.pyplot as plt


# This function randomly selects some rows from the matrixes batch_x and batch_y and returns the rows as two matrixes.
# The number of rows is determined by the batch_size variable. This is exacly the same function that Pontus wrote.
def gen_sub_set(batch_size, batch_x, batch_y):
    if not len(batch_x) == len(batch_y):
        raise ValueError('Lists most be of same length /Pontus')
    index_list = np.random.randint(0, len(batch_x), size=batch_size)
    return [batch_x[index] for index in index_list], [batch_y[index] for index in index_list]


def conv2d(x, W):
  return tf.nn.conv2d(x, W, strides=[1,3,3,1], padding='VALID')


def max_pool(x):
  return tf.nn.max_pool(x, ksize=[1, 3, 3, 1],
                        strides=[1, 3, 3, 1], padding='VALID')


def get_y_for_specified_layers_and_nodes(x,number_of_hidden_layers,number_of_nodes_per_hidden_layer,number_particles,nr_filters):
    if number_of_hidden_layers==0 or number_of_nodes_per_hidden_layer==0:
        raise ValueError("Number of hidden layers or number of nodes per hidden layer can't be zero.")
    weights={}
    biases={}
    weights["W" + str(1)] = tf.Variable(tf.truncated_normal([nr_filters*162, number_of_nodes_per_hidden_layer], stddev=0.1), dtype=tf.float32)
    biases["b" + str(1)] = tf.Variable(tf.ones([number_of_nodes_per_hidden_layer]), dtype=tf.float32)
    for i in range(1,number_of_hidden_layers):
        weights["W"+str(i+1)]=tf.Variable(tf.truncated_normal([number_of_nodes_per_hidden_layer, number_of_nodes_per_hidden_layer], stddev=0.1), dtype=tf.float32)
        biases["b"+str(i+1)]=tf.Variable(tf.ones([number_of_nodes_per_hidden_layer]), dtype=tf.float32)
    weights["W" + str(number_of_hidden_layers+1)] = tf.Variable(tf.truncated_normal([number_of_nodes_per_hidden_layer, number_particles + 1], stddev=0.1),dtype=tf.float32)
    biases["b" + str(number_of_hidden_layers+1)] = tf.Variable(tf.ones([number_particles + 1]), dtype=tf.float32)
    y = x
    for i in range(number_of_hidden_layers):
        y=tf.nn.relu(tf.matmul(y, weights["W"+str(i+1)]) + biases["b"+str(i+1)])
    y=tf.matmul(y,weights["W"+str(number_of_hidden_layers+1)]) + biases["b"+str(number_of_hidden_layers+1)]
    return y


def weight_variable(shape):
  initial = tf.truncated_normal(shape, stddev=0.1)
  return tf.Variable(initial)


def bias_variable(shape):
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial)



#def main(file_name_x, file_name_y,number_particles,number_of_hidden_layers,number_of_nodes_per_hidden_layer):
def main(conv_npz, number_particles, number_of_hidden_layers, number_of_nodes_per_hidden_layer, nr_filters):
    if nr_filters>32:
        raise ValueError("Number of filters can't be too big because some matrices will become too large. 32 worked but 64 didn't.")

    print('Reading convlolution and pooling matrices')
    conv_pool_matrices=np.load('conv_2_matrices.npz')
    first_conv_mat=conv_pool_matrices['first_conv_mat']
    first_conv_mat=tf.convert_to_tensor(first_conv_mat,dtype=tf.float32)

    print('Initializing variables')
    #Making placeholders for the inputdata (x) and the correct output data (y_)
    x = tf.placeholder(dtype=tf.float32, shape=[None, 162]) #162=number of crystals in crystal ball detector
    y_ = tf.placeholder(dtype=tf.float32, shape=[None, number_particles+1])

    W_conv1 = weight_variable([3, 3, 1, nr_filters])
    b_conv1 = bias_variable([nr_filters])

    conv_image_1_flat=tf.matmul(x,first_conv_mat)
    conv_image_1 = tf.reshape(conv_image_1_flat, [-1, 3, 3*162, 1])

    h_conv1 = tf.nn.relu(conv2d(conv_image_1, W_conv1) + b_conv1)
    h_conv1_flat=tf.reshape(h_conv1,[-1,nr_filters*162])

    from_conv=h_conv1_flat

    y = get_y_for_specified_layers_and_nodes(from_conv, number_of_hidden_layers, number_of_nodes_per_hidden_layer,number_particles,nr_filters)

    # As the loss funtion the softmax-crossentropy is used since it's common for classification problems.
    # To optimize the variables, Adam Optimizer is used since it fairs well in comparisons and is easy to use.
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y, labels=y_))
    train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)

    # To check the accuracy, the highest argument of the outputlayer and the one-hot-vector (one-hot is just a way to
    # represent the correct number of guns) is compared

    correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
    # converts boelean to ones and zeros and takes the mean
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))


    print('Reading data')
    data_set=np.load(conv_npz)
    x_batch_train=data_set['x_batch_train']
    y_batch_train = data_set['y_batch_train']
    x_batch_eval = data_set['x_batch_eval']
    y_batch_eval = data_set['y_batch_eval']


    # Now the trainging begins. To get more information regarding the training part, and the whole program, see
    # "Deep learing for experts" on tensorflows webpage.
    print('Start training')
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    start = t.time()

    loss_list_train = []
    accuracy_list_eval = []
    accuracy_list_train = []
    iterations = []

    # Number in "range"=number of training iterations
    for i in range(500000):
        # here 100 reandomly selected rows from the training set are extracted
        x_batch_sub, y_batch_sub = gen_sub_set(100, x_batch_train, y_batch_train)
        if i % 100 == 0:
            iterations.append(i)
            # from the 100 rows from the training set, the loss function is calculated
            loss_list_train.append(sess.run(loss, feed_dict={x: x_batch_sub, y_: y_batch_sub}))
            # To calculate the accuracy, a bigger set of 300 rows are selected
            x_batch_eval_sub, y_batch_eval_sub = gen_sub_set(300, x_batch_eval, y_batch_eval)
            accuracy_value=sess.run(accuracy, feed_dict={x: x_batch_eval_sub, y_: y_batch_eval_sub})
            accuracy_value_train=sess.run(accuracy, feed_dict={x: x_batch_sub, y_: y_batch_sub})
            if i % 1000 == 0:
                print('Iteration nr. ', i, 'Acc: ', accuracy_value)
            accuracy_list_eval.append(accuracy_value)
            accuracy_list_train.append(accuracy_value_train)
        sess.run(train_step, feed_dict={x: x_batch_sub, y_: y_batch_sub})

    end=t.time()

    trainingtime = end - start
    np.savez(
        './parameter_sweep_mult_only1conv/conv_2_only_1conv_' + str(number_of_hidden_layers) + 'layers_' + str(number_of_nodes_per_hidden_layer) + 'nodes_' + str(
            nr_filters) + 'filters_' + str(
            iterations[-1]) + 'iterations.npz', loss_list_train=np.array(loss_list_train),
        accuracy_list_train=np.array(accuracy_list_train), accuracy_list_eval=np.array(accuracy_list_eval),
        iterations=np.array(iterations), trainingtime=trainingtime, number_of_hidden_layers=number_of_hidden_layers,
        number_of_nodes_per_hidden_layer=number_of_nodes_per_hidden_layer, nr_filters=nr_filters)

    # print("Trainingtime: " + str(int(trainingtime))+" seconds")
    #
    # # Basic plotting of accuracy and training loss function using matplotlib.pyplot. Havn't figured out how to change the fontsize though.
    # fig, ax = plt.subplots(2, figsize=(20, 10)) #fig=entire figure, ax=subplots
    # ax[0].plot(iterations[0:-1], loss_list_train[0:-1])
    # ax[0].set(ylabel='Loss function', xlabel='Iteration')
    # ax[1].plot(iterations[0:-1], accuracy_list_train[0:-1])
    # ax[1].plot(iterations[0:-1], accuracy_list_eval[0:-1])
    # ax[1].set(ylabel='Accuracy', xlabel='Iterations')
    #
    # plt.show(fig)

if __name__ == '__main__':
    #main('ord_data_set_XB_up_to_7guns_0dot1_to_10MeV_ca2000000events_iso_digi_sup_90percent.npz', 7, 1, 1024, 32)

    # for sweep
    for i in range(2,6):
        main('ord_data_set_XB_up_to_7guns_0dot1_to_10MeV_ca2000000events_iso_digi_sup_90percent.npz', 7, 1, 1024, 2**i)







