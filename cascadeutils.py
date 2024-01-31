import os

# negative image'lerin adlarını negative.txt dosyasına yazar. path + imageName
def generate_negative_description_file():
    with open('negative.txt', 'w') as f:
        path = "image/negative"
        for filename in os.listdir(path):
            f.write("image/negative/" + filename + "\n")    
    print("Bitti")

generate_negative_description_file()