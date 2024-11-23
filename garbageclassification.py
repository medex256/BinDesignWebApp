from transformers import pipeline # pip install transformers
from PIL import Image

# it need to cache model first. kind of slow but easy to use. not so accurate

# input file path or file object
def garbage_classification(image_path):
    # Load the image classification pipeline
    pipe = pipeline("image-classification", model="yangy50/garbage-classification")

    # Load an image
    image = Image.open(image_path)
    image.resize((640,640))

    # Classify the image
    results = pipe(image)

    # Print the results
    return results

    # example results:
    # [{'label': 'paper', 'score': 0.9879968762397766}, 
    # {'label': 'trash', 'score': 0.28979307413101196}, 
    # {'label': 'glass', 'score': 0.26779070496559143}, 
    # {'label': 'metal', 'score': 0.25491994619369507}, 
    # {'label': 'cardboard', 'score': 0.25006282329559326}]

if __name__ == '__main__':
    print(garbage_classification("test-images/plastic2.jpg"))
    print(garbage_classification("test-images/paper.jpg"))