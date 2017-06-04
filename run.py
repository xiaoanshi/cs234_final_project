# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt

import tensorflow as tf
import numpy as np
import utils
import os
import sys
import random


os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
GPU_CONFIG = tf.ConfigProto()
GPU_CONFIG.gpu_options.per_process_gpu_memory_fraction = 0.5
BATCH_SIZE = 32


def run_epoch(args, model, session, batched_data, batched_labels, batched_seq_lens,  batched_bbox, saver,  file_writer, epoch_num):
    batch_accuracies = []
    for j in xrange(len(batched_data)):
        data_batch = batched_data[j]
        label_batch = batched_labels[j]
        seq_lens_batch = batched_seq_lens[j]
        bbox_batch =  batched_bbox[j]

        summary, loss, rewards, area_accuracy = model.run_one_batch(args, session, data_batch, label_batch, seq_lens_batch, bbox_batch)
        print("Loss of the current batch is {0}".format(loss))
        print("Finished batch {0}/{1}".format(j,len(batched_data)))
        print("Total rewards: {0}".format(rewards))
        print("Average area accuracy per sequence per batch: {0}".format(area_accuracy))
        file_writer.add_summary(summary, j)

        # # Record batch accuracies for test code
        batch_accuracies.append(area_accuracy)

    if args.train == "train":
    # Checkpoint model - every epoch
        utils.save_checkpoint(args, session, saver, epoch_num)
    else: # val or test
        test_accuracy = np.mean(batch_accuracies)
        print "Model {0} accuracy: {1}".format(args.train, test_accuracy)


# def run_actor_critic_model(args):
#     dataset_dir = utils.choose_data(args)
#     dataset = utils.load_dataset(dataset_dir)
#     print "Using checkpoint directory: {0}".format(args.ckpt_dir)

#     model = utils.choose_model(args) # pass in necessary model parameters
#     print "Running {0} model for {1} epochs.".format(args.model, args.num_epochs)

#     global_step = tf.Variable(0, trainable=False, name='global_step')
#     saver = tf.train.Saver(max_to_keep=args.num_epochs)

#     with tf.Session(config=GPU_CONFIG) as session:
#         print "Inititialized TF Session!"

#         # Checkpoint
#         i_stopped, found_ckpt = utils.get_checkpoint(args, session, saver)
#         # Summary Writer
#         file_writer = tf.summary.FileWriter(args.ckpt_dir, graph=session.graph, max_queue=10, flush_secs=30)
#         # Val or Test set accuracie

#         # Make computational graph
#         if args.train == "train" and not found_ckpt:
#             init_op = tf.global_variables_initializer()
#             init_op.run()
#         else:
#             if not found_ckpt:
#                 print "No checkpoint found for test or validation!"
#                 return






def run_rnn_rcnn(args):
    dataset_dir = utils.choose_data(args)
    dataset = utils.load_dataset(dataset_dir)
    print "Using checkpoint directory: {0}".format(args.ckpt_dir)

    model = utils.choose_model(args) # pass in necessary model parameters
    print "Running {0} model for {1} epochs.".format(args.model, args.num_epochs)

    global_step = tf.Variable(0, trainable=False, name='global_step')
    saver = tf.train.Saver(max_to_keep=args.num_epochs)

    with tf.Session(config=GPU_CONFIG) as session:
        print "Inititialized TF Session!"

        # Checkpoint
        i_stopped, found_ckpt = utils.get_checkpoint(args, session, saver)
        # Summary Writer
        file_writer = tf.summary.FileWriter(args.ckpt_dir, graph=session.graph, max_queue=10, flush_secs=30)
		# Val or Test set accuracie

        # Make computational graph
        if args.train == "train" and not found_ckpt:
            init_op = tf.global_variables_initializer()
            init_op.run()
        else:
            if not found_ckpt:
                print "No checkpoint found for test or validation!"
                return

        if "pretrained" in args.model:
            init_fn = tf.contrib.framework.assign_from_checkpoint_fn(
                                model_path='/data/yolo/YOLO_small.ckpt',
                                var_list=model.variables_to_restore)
            init_fn(session)

            if args.model == "pretrained-neg_l1":
                model.add_loss_op('negative_l1_dist')
            elif args.model == "pretrained-iou":
                model.add_loss_op('iou')

        if args.train == 'train':
            for i in xrange(i_stopped, args.num_epochs):
                print "Running epoch ({0})...".format(i)

                batched_data, batched_labels, batched_seq_lens,  batched_bbox = utils.make_batches(dataset, batch_size=BATCH_SIZE)
                run_epoch(args, model, session, batched_data, batched_labels, batched_seq_lens,  batched_bbox,saver, 
                        file_writer, i)


def main(_):
    args = utils.parse_command_line()
    # utils.clear_summaries()
    run_rnn_rcnn(args)


if __name__ == "__main__":
    tf.app.run()
