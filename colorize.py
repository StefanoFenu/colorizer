import tensorflow as tf
import skimage.transform
from skimage.io import imsave, imread
from skimage.color import rgb2gray

with open("model/colorize.tfmodel", mode='rb') as f:
    fileContent = f.read()

graph_def = tf.GraphDef()
graph_def.ParseFromString(fileContent)
grayscale = tf.placeholder("float", [1, 224, 224, 1])
tf.import_graph_def(graph_def, input_map={ "grayscale": grayscale }, name='')

def load_image(path):
        img = rgb2gray(imread(path))
        short_edge = min(img.shape[:2])
        yy = int((img.shape[0] - short_edge) / 2)
        xx = int((img.shape[1] - short_edge) / 2)
        crop_img = img[yy : yy + short_edge, xx : xx + short_edge]
        # resize to 224, 224
        img = skimage.transform.resize(crop_img, (224, 224))
        # desaturate image
        return img


def process_image(gray_image):
    img_gray = gray_image.reshape(1, 224, 224, 1)

    with tf.Session() as sess:
        inferred_rgb = sess.graph.get_tensor_by_name("inferred_rgb:0")
        inferred_batch = sess.run(inferred_rgb, feed_dict={ grayscale: img_gray })
    
    return inferred_batch[0]
