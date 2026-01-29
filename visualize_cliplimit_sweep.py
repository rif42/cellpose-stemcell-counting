
import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from cellpose import models
from matplotlib.colors import LinearSegmentedColormap

# Import local modules
sys.path.append(os.getcwd())
try:
    from confluency_cellpose import calculate_confluency, apply_clahe_to_image
except ImportError:
    # Fallback if imports fail (e.g. if run from a different dir)
    pass

def visualize_results(image_path, clip_limits, output_path):
    print(f"Processing {image_path}...")
    
    # Setup plot
    num_plots = len(clip_limits)
    cols = 3
    rows = (num_plots + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(18, 5 * rows))
    axes = axes.flatten()
    
    # Load original image once
    img_orig = cv2.imread(image_path)
    # Convert to grayscale for CLAHE
    img_gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
    
    # Load model
    print("Loading Cellpose model...")
    model = models.CellposeModel(gpu=True, pretrained_model='cpsam')
    
    for i, cl in enumerate(clip_limits):
        print(f"  Running for Clip Limit: {cl}...")
        ax = axes[i]
        
        # 1. Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=cl, tileGridSize=(8, 8))
        img_clahe = clahe.apply(img_gray)
        
        # 2. Run Cellpose (using logic similar to confluency_cellpose.py)
        # We run it directly to avoid overhead of saving images in the loop
        # and to get direct access to masks for plotting
        masks, flows, styles = model.eval(
            img_clahe,
            diameter=50,
            flow_threshold=2.0,
            cellprob_threshold=-1,
            niter=2000
        )
        
        cellprob_map = flows[2]
        binary_mask = cellprob_map > -1
        confluency = (np.sum(binary_mask) / binary_mask.size) * 100
        
        # 3. Visualize
        # Show CLAHE image
        ax.imshow(img_clahe, cmap='gray')
        
        # Overlay Mask (Green with transparency)
        # Create a custom colormap that is transparent for 0 and green for 1
        cmap_mask = LinearSegmentedColormap.from_list('alpha_green', [(0, 0, 0, 0), (0, 1, 0, 0.4)])
        ax.imshow(binary_mask, cmap=cmap_mask)
        
        ax.set_title(f"Clip Limit: {cl} | Confluency: {confluency:.1f}%", fontsize=14, fontweight='bold')
        ax.axis('off')

    # Turn off unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Comparison saved to {output_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize CLAHE clip limit sweep')
    parser.add_argument('image_path', help='Path to input image')
    args = parser.parse_args()
    
    target_image = args.image_path
    
    # Generate output filename based on input
    dirname = os.path.dirname(target_image)
    basename = os.path.splitext(os.path.basename(target_image))[0]
    output_file = os.path.join(dirname, f"cliplimit_sweep_{basename}.png")
    
    clip_limits = [0.5, 2, 5, 10, 20, 40]
    
    if os.path.exists(target_image):
        visualize_results(target_image, clip_limits, output_file)
    else:
        print(f"Error: File not found: {target_image}")
