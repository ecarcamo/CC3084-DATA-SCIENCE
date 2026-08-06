import kagglehub
import os
import shutil
import random

def main():
    print("Downloading dataset via kagglehub...")
    path = kagglehub.dataset_download("grassknoted/asl-alphabet")
    print(f"Dataset downloaded to: {path}")

    # Determine train directory structure
    train_dir = os.path.join(path, "asl_alphabet_train", "asl_alphabet_train")
    if not os.path.exists(train_dir):
        train_dir = os.path.join(path, "asl_alphabet_train")
        if not os.path.exists(train_dir):
            # In case it's directly in the root
            train_dir = path

    dest_dir = "data"
    os.makedirs(dest_dir, exist_ok=True)

    # We want 600 images per class
    N = 600
    
    classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
    
    # We might have test and train folders, let's filter if it's the root
    if "asl_alphabet_train" in classes:
        train_dir = os.path.join(path, "asl_alphabet_train")
        classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]

    # Still checking if double nested
    if "asl_alphabet_train" in classes:
        train_dir = os.path.join(train_dir, "asl_alphabet_train")
        classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]

    print(f"Found {len(classes)} classes in {train_dir}")
    random.seed(42) # For reproducibility

    for class_name in classes:
        class_path = os.path.join(train_dir, class_name)
        dest_class_path = os.path.join(dest_dir, class_name)
        os.makedirs(dest_class_path, exist_ok=True)
        
        images = [img for img in os.listdir(class_path) if img.endswith(".jpg") or img.endswith(".png")]
        random.shuffle(images)
        sampled = images[:N]
        
        for img in sampled:
            src = os.path.join(class_path, img)
            dst = os.path.join(dest_class_path, img)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
        print(f"Sampled {len(sampled)} images for class {class_name}")

    print("Sampling complete!")

if __name__ == "__main__":
    main()
